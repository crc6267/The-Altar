import subprocess
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Ollama MCP Server")

@mcp.tool(description="List locally installed Ollama models",)
def list_models():
    process = subprocess.run(
        ["ollama", "list"],
        capture_output=True,
        text=True
    )
    lines = process.stdout.strip().split("\n")[1:]
    return [line.split()[0] for line in lines]

@mcp.tool(
    description="Generate a response using a local Ollama model",
)
def generate(model, prompt):
    process = subprocess.run(
        ["ollama", "run", model],
        input=prompt.encode(),
        capture_output=True
    )
    return process.stdout.decode()

@mcp.tool(
    description="Create embeddings for a text input using a local Ollama model",
)
def embed_text(model, text):
    process = subprocess.run(
        ["ollama", "embed", "-m", model],
        input=text.encode(),
        capture_output=True
    )
    return process.stdout.decode()

if __name__ == "__main__":
    mcp.run()