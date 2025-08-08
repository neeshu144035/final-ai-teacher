# retriever.py
from sentence_transformers import SentenceTransformer
import faiss
import pickle

# Load FAISS index and texts
index = faiss.read_index("backend/faiss_index_ms_marco.index")
with open("texts.pkl", "rb") as f:
    texts = pickle.load(f)

model = SentenceTransformer('all-MiniLM-L6-v2')

def retrieve(query, k=5):
    embedding = model.encode([query])
    D, I = index.search(embedding, k)
    return [texts[i] for i in I[0]]
