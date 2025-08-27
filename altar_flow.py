from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
import json

# This will let us use the Ollama model
from langchain_ollama import ChatOllama

from bible.bible_tools import random_chapter, select_chapter, scripture_exists
TOOLS = [random_chapter, select_chapter, scripture_exists]

from typing import TypedDict, Optional, List, Literal

# ========================== Models ===========================
main_model = ChatOllama(
    model="gpt-oss:20b",
    disable_streaming=False,
    callbacks=[]
).bind_tools(TOOLS)
# ========================== End Models ===========================

# ========================== State ===========================
class AltarState(TypedDict, total=False):
    user_text: str
    scripture_ref: str    # e.g., "Psalm 19"
    scripture_text: Optional[str]
    theme_word: Optional[str]        # e.g., "Peace"
    mirror_points: Optional[List[str]]
    discern_checks: Optional[List[str]]
    guidance: Optional[str]
    status: Literal["ok","warn","fail"]
    messages: Annotated[list, add_messages]
# ========================== End State ===========================

# =========================== Graph Initialization ===========================
graph_builder = StateGraph(AltarState)

from langgraph.graph import StateGraph, END
# =========================== End Graph Initialization ===========================

# =========================== Nodes ===========================
def chatbot(state: AltarState):
    messages = state.get("messages", [])
    return {"messages": [main_model.invoke(messages)]}

import json

def anchor_node(state: AltarState):
    """
    The core decision node.
    GPT‑OSS decides whether to select a chapter, correct a reference,
    or pick a random passage.
    """
    user_text = state.get("user_text", "")
    scripture_ref = state.get("scripture_ref", "")

    prompt = f"""
    The user is seeking guidance from scripture.

    User situation: "{user_text}"
    Preferred reference (optional): "{scripture_ref}"

    Rules:
    - If scripture_ref is valid, call select_chapter(book, chapter).
    - If scripture_ref looks wrong or misspelled, correct it and then call select_chapter().
    - If scripture_ref is empty, call random_chapter().
    - Always return the scripture reference and full text.
    """

    response = main_model.invoke(prompt)

    # If GPT‑OSS chooses to call a tool, LangGraph routes automatically.
    return state | {"messages": [response]}

def update_state_from_tool(state: AltarState) -> AltarState:
    """Unpack the tool output and inject into state."""
    if not state.get("messages"):
        return state


    messages = state.get("messages", [])

    if not messages:
        return state
    last_msg = messages[-1]
    
    # Check if last message came from a tool
    if hasattr(last_msg, "name") and last_msg.name in ["random_chapter", "select_chapter"]:
        try:
            data = json.loads(last_msg.content)
            state["scripture_ref"] = data["scripture_ref"]
            state["scripture_text"] = data["scripture_text"]
        except Exception as e:
            print(f"⚠️ Failed to parse tool output: {e}")
    return state

# =========================== End Nodes ===========================

# =========================== Node Contstruction ===========================
# graph.add_node("anchor", anchor_node)
# graph.add_node("extract", extract_theme_node)
# graph.add_node("mirror", mirror_node)
# graph.add_node("discern", discern_node)
# graph.add_node("apply", apply_node)
# graph.add_node("log", log_node)
graph_builder = StateGraph(AltarState)

tool_node = ToolNode(tools=TOOLS)

graph_builder.add_node("anchor", anchor_node)
graph_builder.add_node("tools", tool_node)
graph_builder.add_node("update_state", update_state_from_tool)

# If the model wants to call a tool, run it; otherwise finish.
graph_builder.add_conditional_edges("anchor", tools_condition)

# After a tool runs, update the state, then END
graph_builder.add_edge("tools", "update_state")
graph_builder.add_edge("update_state", END)

# If the model doesn't call a tool, anchor goes straight to END
graph_builder.add_edge("anchor", END)

graph_builder.set_entry_point("anchor")
graph = graph_builder.compile()
# =========================== End Node Construction ===========================

def run_repl():
    print("=== ALTAR APP TEST ===")
    print("Type 'quit' to exit.\n")

    while True:
        user_text = input("Enter your situation: ").strip()
        if user_text.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        flip = input("Do you want to pick a passage yourself? (y/n): ").strip().lower()

        if flip == "y":
            scripture_ref = input("Enter scripture reference (e.g. Psalm 19): ").strip()
            initial_state = AltarState(user_text=user_text, scripture_ref=scripture_ref)
        else:
            initial_state = AltarState(user_text=user_text)

        print("\n--- STREAMING GRAPH UPDATES ---")
        final_state = AltarState()
        for event in graph.stream(initial_state):
            for state in event.values():
                final_state = state
                print(f"[Node Update] → {state}")

        print("\n--- FINAL RESULT ---")
        print(f"User Text      : {final_state.get('user_text')}")
        print(f"Scripture Ref  : {final_state.get('scripture_ref')}")
        print(f"Scripture Text : {final_state.get('scripture_text')}")
        print("=======================\n")

run_repl()

