from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from langchain_ollama import ChatOllama

from bible_tools import random_chapter, select_chapter
TOOLS = [random_chapter, select_chapter]

class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

main_model = ChatOllama(
    model="gpt-oss:20b",
    disable_streaming=False,
    callbacks=[]
).bind_tools(TOOLS)

def chatbot(state: State):
    return {"messages": [main_model.invoke(state["messages"])]}

graph_builder.add_node("chatbot", chatbot)
tool_node = ToolNode(tools=TOOLS)
graph_builder.add_node("tools", tool_node)
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")
graph = graph_builder.compile()

def stream_graph_updates(user_input: str):
    seen = None
    # Prepend a system prompt before the user input
    for event in graph.stream({
        "messages": [
            {
                "role": "system",
                "content": (
                    """
                    You are a scripture study assistant.

                    Your goal: provide prayerful, Christ-centered guidance rooted in Scripture.
                    
                    If the user provides a specific Bible book and chapter (e.g. "John 3"), use the `select_chapter` tool to retrieve the text.
                    Review the chapter text and utilize it for the following response.

                    Follow this structure for *every* response:
                    1. **Theme Word** — one distilled word or phrase that captures the essence.
                    2. **Context Reflection** — 2–3 poetic, empathetic sentences tying the user’s situation to the theme.
                    3. **Scripture References** — 2–3 directly relevant passages quoted verbatim (keep them short).
                    4. **Checks** — Always include 4 checks:
                        — Aligns with Scripture?  
                        — Glorifies Christ?  
                        — Brings peace?  
                        — Bears fruit?
                    5. **Application** — Up to 4–5 numbered steps for prayer, reflection, and action.
                    6. **Probing Question** — End with a single thoughtful, open-ended question.

                    Tone: compassionate, reverent, concise but layered.
                    Never force brevity; depth is welcome, but clarity comes first.
                    """
                )
            },
            {"role": "user", "content": user_input}
        ]
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
    try:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        stream_graph_updates(user_input)
    except:
        user_input = "What do you know about LangGraph?"
        print("User: " + user_input)
        stream_graph_updates(user_input)
        break