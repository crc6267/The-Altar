import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import logging
from langchain_ollama import ChatOllama
from langchain.prompts import ChatPromptTemplate
from langchain.schema import SystemMessage
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from bible.bible_helpers import *

logging.basicConfig(level=logging.INFO)

# --- Example Local Tools ---
def list_models():
    return ["gpt-oss:20b", "phi3:mini", "mistral:latest", "nomic-embed-text:latest"]

def embed_text(model: str, text: str):
    return {
        "model": model,
        "text": text,
        "embedding": [0.12, 0.33, 0.91]  # stubbed example
    }

# --- Register Tools ---
tools = [
    {
        "name": "list_models",
        "description": "List available local Ollama models",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "embed_text",
        "description": "Generate embeddings for input text using a local model",
        "parameters": {
            "type": "object",
            "properties": {
                "model": {"type": "string", "description": "Model name"},
                "text": {"type": "string", "description": "Text to embed"}
            },
            "required": ["model", "text"]
        }
    },
    {
        "name": "random_chapter",
        "description": "Fetch a random chapter from the Bible",
        "parameters": {"type": "object", "properties": {}, "required": []}
    }
]

# --- Bind Model to Tools ---
model = ChatOllama(
    model="gpt-oss:20b",
    disable_streaming=False,
    callbacks=[StreamingStdOutCallbackHandler()]
).bind_tools(tools)

with open("../assets/breath.txt", "r", encoding="utf-8") as f:
    system_message_content = f.read()

# --- Prompt Template ---
prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content=system_message_content),
    ("human", "{input}")
])

# --- Query Processing ---
def process_query(query: str):
    # Format prompt using your langchain PromptTemplate
    formatted_prompt = prompt.format_messages(input=query)
    result = model.invoke(formatted_prompt)

    # If the model decides to call a tool
    if hasattr(result, "tool_calls") and result.tool_calls:  # type: ignore
        tool_results = {}
        for tool_call in result.tool_calls: # type: ignore
            name = tool_call["name"]
            args = tool_call.get("args", {})
            try:
                if name == "list_models":
                    tool_results[name] = list_models()
                elif name == "embed_text":
                    # Always force embedding model as per your rule
                    if "model" not in args:
                        args["model"] = "nomic-embed-text"
                    tool_results[name] = embed_text(**args)
                elif name == "random_chapter":
                    bible = load_bible()
                    book, chapter, verses = random_chapter(bible)
                    text = chapter_text_from(verses)
                    tool_results[name] = {"book": book, "chapter": chapter, "text": text}
                else:
                    tool_results[name] = f"Unknown tool: {name}"
            except Exception as e:
                tool_results[name] = f"Tool {name} failed: {str(e)}"

        # **Second pass** — inject tool results back into context
        follow_up_prompt = [
            SystemMessage(content=system_message_content),
            ("human", query),
            ("ai", "Tool results: " + str(tool_results)),
            ("human", "Utilize these results to provide a response."),
        ]

        final_result = model.invoke(follow_up_prompt)
        return final_result.content

    # Otherwise, just return normal LLM output
    return result.content

# --- Manual Test ---
if __name__ == "__main__":
    while True:
        query = input("\nYou: ")
        if query.lower() in ["exit", "quit"]:
            break
        response = process_query(query)
