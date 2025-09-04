# pip install -U langchain-ollama
from langchain_ollama import OllamaEmbeddings
import numpy as np

# Make sure you've pulled the model first: `ollama pull embeddinggemma`
emb = OllamaEmbeddings(
    model="embeddinggemma:300m",   # or "embeddinggemma:latest"
    validate_model_on_init=True,               # let Ollama use your GPU
)

# query = "I feel lost and confused"
# docs = [
#     "I am so happy",
#     "Why cant I hear God?",
#     "Jupiter, the largest planet in our solar system, has a prominent red spot.",
#     "Saturn, famous for its rings, is sometimes mistaken for the Red Planet."
# ]

# # EmbeddingGemma works best with “query/document” prompts:
# q_vec   = emb.embed_query(f"task: search result | query: {query}")
# doc_vecs = emb.embed_documents([f'title: none | text: {t}' for t in docs])

# # cosine similarity
# D = np.array(doc_vecs); q = np.array(q_vec)
# sims = (D @ q) / (np.linalg.norm(D,axis=1) * np.linalg.norm(q))
# rank = np.argsort(-sims)
# print([docs[i] for i in rank])

def embed_themes(anchor_theme, user_theme):
    anchor_theme = [anchor_theme]
    anchor_vec = emb.embed_documents([f"title: none | text: {t}" for t in anchor_theme])
    user_vec = emb.embed_query(f"task: semantic search result based on sentiment | query: {user_theme}")
    
    return {"anchor": {"theme": anchor_theme, "vec": anchor_vec}, "user": {"theme": user_theme, "vec": user_vec}}
    



    