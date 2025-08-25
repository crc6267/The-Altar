import subprocess
import json
from ollama_mcp import list_models, generate, embed_text

SYSTEM_PROMPT = """
You are a local assistant with access to these tools:
- list_models(): Lists all locally installed Ollama models.
- generate(model, prompt): Generates a response from a model.
- embed_text(model, text): Creates embeddings for a piece of text.

If you want to use a tool, respond ONLY in valid JSON like this:
{"tool": "list_models", "args": {}}

Otherwise, respond normally.
"""

def ask_ollama(model, prompt):
    process = subprocess.run(
        ["ollama", "run", model],
        input=prompt.encode(),
        capture_output=True
    )
    return process.stdout.decode().strip()

def handle_tool_call(tool_name, args):
    if tool_name == "list_models":
        return list_models()
    elif tool_name == "generate":
        return generate(**args)
    elif tool_name == "embed_text":
        return embed_text(**args)
    else:
        return f"Unknown tool: {tool_name}"

def chat():
    print("\n=== Local Ollama Chat ===\n")
    models = list_models()
    print("Available Models:", ", ".join(models))

    model = input("\nChoose a model: ").strip()
    if model not in models:
        print(f"❌ Model '{model}' not found.")
        return

    print(f"\nUsing model: {model}\n(Type 'exit' to quit)\n")

    history = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("\nGoodbye!")
            break

        history.append({"role": "user", "content": user_input})

        # Get model response
        response = ask_ollama(model, json.dumps(history))

        # Check if response is JSON (tool call)
        try:
            parsed = json.loads(response)
            if "tool" in parsed:
                print(f"\n⚡ Using tool: {parsed['tool']}")
                result = handle_tool_call(parsed["tool"], parsed.get("args", {}))
                history.append({"role": "tool", "content": str(result)})
                print("🔧 Tool result sent back to model.\n")
                continue
        except json.JSONDecodeError:
            pass

        # Otherwise, it's a normal response
        print(f"{model}: {response}")
        history.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    chat()

