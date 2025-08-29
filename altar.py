from typing import Annotated
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

import json

from langchain_ollama import ChatOllama

from bible_tools import random_chapter, select_chapter
BIBLE_TOOLS = [random_chapter, select_chapter]

from prompt import SYSTEM_PROMPT

class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

main_model = ChatOllama(
    model="gpt-oss:20b",
    disable_streaming=False,
    callbacks=[]
).bind_tools(BIBLE_TOOLS)

def chatbot1(state):
    if "tool_result" in state and not state.get("tool_result_verified"):
        result = state["tool_result"]
        book = result.get("book")
        chapter = result.get("chapter")
        verses = result.get("verses")
        if book and chapter:
            # Add a clean handoff message but preserve state
            return {
                "messages": state["messages"] + [AIMessage(content=f"Verified passage: {book} {chapter}.", type="ai", tool_calls=[])] + [ToolMessage(content=json.dumps({"name": "select_chapter", "arguments": {"book": book, "chapter": chapter, "verses": verses}}), type="tool", tool_calls=[])],
            }
        else:
            return {
                "messages": state["messages"] + [AIMessage(content="❌ Invalid tool result.")],
                "tool_result_verified": False
            }

    # Normal model behavior
    reply = main_model.invoke(state["messages"])
    return {
        "messages": state["messages"] + [reply],
        "tool_result": state.get("tool_result")  # <- this line is already good
    }

def chatbot2(state):
    result = state.get("tool_result", {})
    print('\n\nIn chatbot2 with tool_result:', result, "\n\n")
    book = result.get("book")
    print('\n\nIn chatbot2 with book:', book, "\n\n")
    chapter = result.get("chapter")
    print('\n\nIn chatbot2 with chapter:', chapter, "\n\n")
    verses = result.get("verses")
    print('\n\nIn chatbot2 with verses:', verses[:100] if verses else None, "\n\n")

    if not (book and chapter and verses):
        return {
            "messages": state["messages"] + [AIMessage(content="❌ Missing or invalid tool result; cannot proceed.")]
        }

    # Seed the prompt for reflection or summarization
    prompt = f"Summarize the key message of {book} {chapter}:\n\n{verses[:3000]}"  # truncate to avoid overload
    reply = main_model.invoke([HumanMessage(content=prompt)])

    return {
        "messages": state["messages"] + [reply]
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
    return "__end__"

graph_builder.add_node("chatbot1", chatbot1)
graph_builder.add_node("chatbot2", chatbot2)

bible_tool_node = ToolNode(tools=BIBLE_TOOLS)
boof_tool_node  = ToolNode(tools=BOOF_TOOLS)
graph_builder.add_node("bible_tools", bible_tool_node)
graph_builder.add_node("boof_tools",  boof_tool_node)

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
    {"boof_tools": "boof_tools", "__end__": END},
)
graph_builder.add_edge("boof_tools", "chatbot2")   # loop back after tools

graph_builder.add_edge(START, "chatbot1")

graph = graph_builder.compile()

print("=== Running the graph ===")
for step in graph.stream({"messages": ["Can you pick a random verse for me?"]}, stream_mode="updates"):
    node_name, delta = next(iter(step.items()))
    print(f"→ {node_name}")
    for k, v in delta.items():
        print(f"   {k}: {v}")

from IPython.display import Image, display

from pathlib import Path

# Get the PNG bytes from LangGraph
png_bytes = graph.get_graph().draw_mermaid_png()

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

# def stream_graph_updates(user_input: str):
#     seen = None
#     for event in graph.stream({
#         "messages": [
#             {
#                 "role": "system",
#                 "content": SYSTEM_PROMPT   
#             },
#             {"role": "user", "content": user_input}
#         ]
#     }):
#         for state in event.values():
#             msgs = state.get("messages", [])
#             if not msgs:
#                 continue
#             last = msgs[-1]

#             if getattr(last, "type", None) == "ai" and not getattr(last, "tool_calls", None):
#                 content = last.content
#                 if isinstance(content, list):
#                     content = "".join(
#                         (p.get("text", "") if isinstance(p, dict) else str(p))
#                         for p in content
#                     )
#                 if content and content != seen:
#                     print("\n\n =============================== Start of Devotion ================================ \n")
#                     print("Assistant:", content)
#                     print("\n\n ================================ End of Devotion ================================= \n")
#                     seen = content

# while True:
#     print("Proverbs 16:33 — 'The lot is cast into the lap, but the whole disposing thereof is of the LORD.'\n")
#     print("This is not an oracle, but an assistant to help you reflect on what the Spirit might be saying to YOU through His word.\n")
#     print("\n#1 Step into the altar. Please grab your bible\n")
#     print("#2 Take a moment to center yourself and think about what is weighing on your heart.\n")
#     print("#3 Flip to a random book and chapter in the Bible.\n")
#     print("#4 Share your situation or question, and provide the book and chapter you flipped to.\n")

#     try:
#         user_input = input("Enter petition: ")
#         if user_input.lower() in ["quit", "exit", "q"]:
#             print("Goodbye!")
#             break
#         stream_graph_updates(user_input)
#     except:
#         user_input = "What do you know about LangGraph?"
#         print("User: " + user_input)
#         stream_graph_updates(user_input)
#         break