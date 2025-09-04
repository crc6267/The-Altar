from typing import Annotated, Optional
from typing_extensions import TypedDict
import json
import traceback

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

def chatbot1(state):
    print('We are in chatbot1')
    # If there is a last message and its a tool message
    if state["messages"][-1] and isinstance(state["messages"][-1], ToolMessage):
        print('we are in if')
        # Get most recent message
        last_message = state["messages"][-1]
        # print("This is the last message", last_message
        # TODO Investigate why the result comes back as none
        # TODO Prompts need to be more robust and instructional, the LLM is not tool calling and messeing up a little bit
        # NOTE: The tool message content is always a json string. You must parse it before treating it like an object
        content = json.loads(last_message.content)
        # Now we can dissect the json object
        tool_result = content["tool_result"]
        book = tool_result["book"]
        chapter = tool_result.get("chapter")
        verses = tool_result.get("verses")
        
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
                "tool_result_verified": False
            }

    # Normal model behavior
    reply = main_model.invoke(state["messages"])
    return {
        "messages": state["messages"] + [reply]
    }

def chatbot2(state):
    # Seed the prompt for reflection or summarization
    prompt = f"""
        You are a summarizer and literary analyzer. Your job is to provide a 3 word summary or analysis of two things - The users statement and the bible verse provided.
        
        The bible summarization will serve as the anchor theme for the rest of this program.
        
        Here is the Bible verse to summarize: {state['bible_info']['book']} {state['bible_info']['chapter']}: {state['bible_info']['verses']}
        
        Here is the user's input: {state["user_input"]}
        
        Please return the format as a json string with the keys "anchor_theme" and "user_theme"
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
    content = json.loads(last_message.content)
    
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

print("=== Running the graph ===")
# for step in graph.stream({"messages": ["Can you pick a random verse for me?"], "bible_info": None}, stream_mode="updates"):
#     node_name, delta = next(iter(step.items()))
#     print(f"→ {node_name}")
#     for k, v in delta.items():
#         print(f"   {k}: {v}")

# from IPython.display import Image, display

# from pathlib import Path

# Get the PNG bytes from LangGraph
# png_bytes = graph.get_graph().draw_mermaid_png()

# Try to render in a notebook; otherwise save to a file

# from pathlib import Path
# import os
# import traceback

# def save_langgraph_png(graph, outpath="langgraph.png"):
#     try:
#         obj = graph.get_graph().draw_mermaid_png()  # may return bytes or an IPython Image-like
#         # Normalize to raw PNG bytes
#         if isinstance(obj, (bytes, bytearray)):
#             png = bytes(obj)
#         elif hasattr(obj, "data"):  # IPython Image-like
#             png = obj.data
#         elif hasattr(obj, "getvalue"):  # BytesIO-like
#             png = obj.getvalue()
#         else:
#             raise TypeError(f"Unexpected return type: {type(obj)}")
#         out = Path(outpath).resolve()
#         out.write_bytes(png)
#         print(f"✅ Saved graph to: {out}")
#         print(f"📂 Current working dir was: {Path.cwd()}")
#     except Exception:
#         print("❌ Failed to render/save the graph. Full traceback:")
#         traceback.print_exc()

# # call it:
# save_langgraph_png(graph, "langgraph.png")

def stream_graph_updates(user_input: str):
    seen = None
    for event in graph.stream({
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful bible assistant. If the user asks to flip to a random chapter, use the random chapter tool. If they provide scripture or a passage, use the select chapter to tool to grab it."   
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
        