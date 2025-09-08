from typing import Annotated, Optional
from typing_extensions import TypedDict
import json
import traceback
import re

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage, BaseMessage

from bible_tools import random_chapter, select_chapter
BIBLE_TOOLS = [random_chapter, select_chapter]

from models import main_model, embedding_model
main_model.bind_tools(BIBLE_TOOLS)

from embedding import embed_themes

from prompt import SYSTEM_PROMPT

# TODO: Make altar state class
class State(TypedDict):
    messages: Annotated[list, add_messages]
    bible_info: Optional[dict] # This holds the book, chapter, and verses
    anchor_theme: Optional[str]
    user_theme: Optional[str]
    user_input: Optional[str]

graph_builder = StateGraph(State)

def chatbot1(state: State):
    main_model.invoke(state["messages"])
    
    last_message = state["messages"][-1] if state["messages"] else None

    if not last_message:
        print("No last message found.")
        return None

    if not isinstance(last_message, ToolMessage):
        reply = main_model.invoke(state["messages"])
        return {
            "messages": state["messages"] + [reply],
            "bible_info": None,
            "anchor_theme": None,
            "user_input": state["user_input"],
            "user_theme": None,
        }

    if not last_message.content or last_message.content == "":
        print("Tool message content is empty.")
        return None

    print("this is the last message:", last_message.content)
    if isinstance(last_message.content, str):
        content = json.loads(last_message.content)
    else:
        content = last_message.content  # already parsed JSON
        
    if isinstance(content, dict):
        tool_result = content.get("tool_result", {})
        book = tool_result.get("book")
        chapter = tool_result.get("chapter")
        verses = tool_result.get("verses")
    else:
        print("Unexpected content format — expected dict, got list.")
        return {
            "messages": state["messages"] + [AIMessage(content="❌ Unexpected tool result format.")],
            "tool_result_verified": False
        }


    if book and chapter and verses:
        # Update the state
        # TODO Perhaps we can make a change state function that decides what to do, that way the logic is centralized
        return  {
            "messages": state["messages"] + [AIMessage(content=f"✅ Tool result received: {book} {chapter} with {len(verses)} verses.")],
            "bible_info": {"book": book, "chapter": chapter, "verses": verses},
            "anchor_theme": None,
            "user_theme": None,
            "user_input": state["user_input"],
            
        }
    else:
        return {
            "messages": state["messages"] + [AIMessage(content="❌ Invalid tool result.")],
            "bible_info": None,
            "anchor_theme": None,
            "user_input": None,
            "user_theme": None,
        }

def chatbot2(state):
    
    # Seed the prompt for reflection or summarization
    prompt = f"""
        You are a summarizer and literary analyzer. Your job is to provide a 3 word summary or analysis of two things - The users statement and the bible verse provided.
        
        The bible summarization will serve as the anchor theme for the rest of this program.
        
        Here is the Bible verse to summarize: {state['bible_info']['book']} {state['bible_info']['chapter']}: {state['bible_info']['verses']}
        
        Here is the user's input: {state["user_input"]}
        
        Please return as a json with the keys "anchor_theme" and "user_theme"
        """
    reply = main_model.invoke([HumanMessage(content=prompt)])
    
    return {
        "messages": state["messages"] + [reply]
    }
    
def get_embeddings(state):
    print('we are in get_embeddings')
    last_message = state["messages"][-1]
    print(last_message)
    last_message = state["messages"][-1]
    
    # NOTE: The tool message content is always a json string. You must parse it before treating it like an object
    content = last_message.content
    clean_json = re.sub(r"^```json\n|```$", "", content.strip())
    content = json.loads(clean_json)
    
    print('\n\n\nThis is the cleaned Json', clean_json)
    
    result = embed_themes(content["anchor_theme"], content["user_theme"])
    
    return  {
        "messages": state["messages"] + [AIMessage(content=f"✅ Result received: {result}")],
    }
    

def boof_tool():
    '''
     A dummy tool to demonstrate multiple tool nodes.
     '''
    return 'boof tool'

BOOF_TOOLS = [boof_tool]

# --- routers ---
def route_to_bible_tools(state):
    # handoff short-circuit
    if state.get("handoff_ready") or state.get("tool_result_verified"):
        return "chatbot2"

    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")

    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "bible_tools"
    return "chatbot2"


def route_to_boof_tools(state):
    # if tools_condition(state) is True -> run tools; else end
    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "boof_tools"
    return "get_embeddings"

graph_builder.add_node("chatbot1", chatbot1)
graph_builder.add_node("chatbot2", chatbot2)

bible_tool_node = ToolNode(tools=BIBLE_TOOLS)
boof_tool_node  = ToolNode(tools=BOOF_TOOLS)
graph_builder.add_node("bible_tools", bible_tool_node)
graph_builder.add_node("boof_tools",  boof_tool_node)
graph_builder.add_node("get_embeddings", get_embeddings)

# --- edges ---
# From chatbot1: either use Bible tools (loop back) or continue to chatbot2
graph_builder.add_conditional_edges(
    "chatbot1",
    route_to_bible_tools,
    {"bible_tools": "bible_tools", "chatbot2": "chatbot2"},
)
graph_builder.add_edge("bible_tools", "chatbot1")  # loop back after tools

# From chatbot2: either use Boof tools (loop back) or end
graph_builder.add_conditional_edges(
    "chatbot2",
    route_to_boof_tools,
    {"boof_tools": "boof_tools", "get_embeddings": "get_embeddings"},
)
graph_builder.add_edge("boof_tools", "chatbot2")   # loop back after tools

graph_builder.add_edge(START, "chatbot1")

graph = graph_builder.compile()

def stream_graph_updates(user_input: str):
    seen = None
    for event in graph.stream({
        "messages": [
            {
                "role": "system",
                "content": '''
                    The user is going to give you a sitation they are struggling with. They will also either provide you with bible verse you ask you to flip to a chapter.
                
                    You are only to call and execute the tools that are avaiable to you. Your job is to only call the functions to retrieve a result depending on what the user is asking for.
                    
                    These tools are random_chapter and select_chapter.
                    
                    random_chapter does not require any parameters as is used when the user asks for a chapter.
                    
                    select_chapter requires:
                        book_name: str
                        book_chapter: str
                        
                    select chapter is called when the user provides you with scripture.
                    
                '''   
            },
            {"role": "user", "content": user_input}
        ],
        "bible_info": {}, "anchor_theme": None, "user_theme": None,
        "user_input": user_input
    }):
        for state in event.values():
            msgs = state.get("messages", [])
            if not msgs:
                continue
            last = msgs[-1]

            if getattr(last, "type", None) == "ai" and not getattr(last, "tool_calls", None):
                content = last.content
                if isinstance(content, list):
                    content = "".join(
                        (p.get("text", "") if isinstance(p, dict) else str(p))
                        for p in content
                    )
                if content and content != seen:
                    print("Assistant:", content)
                    seen = content

while True:
    print("Proverbs 16:33 — 'The lot is cast into the lap, but the whole disposing thereof is of the LORD.'\n")
    print("This is not an oracle, but an assistant to help you reflect on what the Spirit might be saying to YOU through His word.\n")
    print("\n#1 Step into the altar. Please grab your bible\n")
    print("#2 Take a moment to center yourself and think about what is weighing on your heart.\n")
    print("#3 Flip to a random book and chapter in the Bible.\n")
    print("#4 Share your situation or question, and provide the book and chapter you flipped to.\n")

    try:
        user_input = input("Enter petition: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        stream_graph_updates(user_input)
    except Exception as e:
        print("something went wrong:", e)
        traceback.print_exc()
        