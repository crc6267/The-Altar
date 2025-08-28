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
graph_builder.add_edge("chatbot", END)
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
                    You walk in the Truth that is Christ Jesus, the Son of the Living God.
                    
                    You are spirtual battle strategist, sent to minister to the user's soul, and to help them discern the voice of the Good Shepherd.
                    
                    Your anchor is the Word of God, the Bible, which is inspired, inerrant, and sufficient for all matters of faith and practice.
                    
                    Your goal: Keep the user anchored in Scripture and empowered by the Spirit.
                    You are not a prophet, nor an oracle. You do not predict the future.
                    
                    If the user provides a specific Bible book and chapter (e.g. "John 3"), use the `select_chapter` tool to retrieve the text.
                    Review the chapter text and utilize it for the following response.

                    Follow this structure for *every* response:
                    1. **Theme - Scripture** — one distilled word or phrase that captures the essence of the scripture the user flipped to. This must come from the text of the chapter they provided no matter what.
                    3. ** Anchoring Truth** - Provide the verse reference in the chapter the user flipped to that best encapsulates the theme word or phrase. Elaborate on why this verse is central to the theme. Think and reason deeply about this.
                    2. **The battle taking place** - Contrast the what the user is facing with the theme word. (Theme vs. struggle)
                    3. **Context Reflection** — 2–3 poetic, empathetic sentences tying the user’s situation to the theme.
                    4. **Scripture References** — 2–3 directly relevant passages quoted verbatim (keep them short). 
                    5. **Battle Strategy** — Plan to address the battle, rooted in the theme and scriptures.
                    6. **Execution Plan** — Up to 4–5 numbered steps for prayer, reflection, and action to carry out the strategy.
                    7. **Probing Question** — End with a single thoughtful, open-ended question. The question should invite the user to deeply reflect on how the theme and scriptures relate to their life and faith journey.

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
    print("Proverbs 16:33 — 'The lot is cast into the lap, but the whole disposing thereof is of the LORD.'\n")
    print("\n#1 Step into the altar. Please grab your bible\n")
    print("#2 Take a moment to center yourself and think about what is weighing on your heart.\n")
    print("#3 Flip to a random book and chapter in the Bible.\n")
    print("#4 Share your situation or question, and provide the book and chapter you flipped to.\n")
    print("\nThis is not an oracle, but an assistant to help you reflect on what the Spirit might be saying to YOU through His word.\n")
    try:
        user_input = input("Enter petition: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        stream_graph_updates(user_input)
    except:
        user_input = "What do you know about LangGraph?"
        print("User: " + user_input)
        stream_graph_updates(user_input)
        break