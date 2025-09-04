from langchain_ollama import ChatOllama

main_model = ChatOllama(
    model="gpt-oss:20b",
    top_k=40,
    disable_streaming=False,
    callbacks=[],
)

embedding_model = ChatOllama(
    model = "embeddinggemma:300m",
    disable_streaming=False,
    callbacks=[]
)