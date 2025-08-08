import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

class RAGRetriever:
    def __init__(
        self,
        knowledge_path: str,
        metadata_path: str,
        embed_path: str,
        index_path: str,
        model_name: str = "msmarco-distilbert-base-v4"
    ):
        # Load knowledge base (e.g., textbook content)
        with open(knowledge_path, "r", encoding="utf-8") as f:
            self.knowledge = json.load(f)

        # Load metadata (e.g., titles, chapters)``
        with open(metadata_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

        # Initialize the embedding model
        self.embed_model = SentenceTransformer(model_name)

        # Load precomputed embeddings
        self.embeddings = np.load(embed_path)

        # Load FAISS index
        self.index = faiss.read_index(index_path)

        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(self.embeddings)

    def retrieve(self, query: str, k: int = 5, threshold: float = 0.5):
        """
        Retrieves top-k relevant documents based on query using FAISS and SentenceTransformer.

        Args:
            query (str): The search query.
            k (int): The number of results to return.
            threshold (float): The similarity threshold to filter results.

        Returns:
            list: A list of relevant content based on the query.
        """
        # Encode the query into embedding using SentenceTransformer
        q_emb = self.embed_model.encode([query], convert_to_numpy=True)
        faiss.normalize_L2(q_emb)

        # Perform the FAISS search
        distances, indices = self.index.search(q_emb, k)

        # Collect search results
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if dist >= threshold:
                # Extract metadata and content based on the index
                meta = self.metadata[idx]
                content = self.knowledge.get(meta["chapter"], {}).get(meta["title"], None)
                if content:
                    results.append(content)
                else:
                    results.append(
                        f"[Warning] Content for '{meta['title']}' not found in chapter '{meta['chapter']}'."
                    )
        return results



rag_retriever = RAGRetriever(
    knowledge_path=r"C:\Users\neesh\OneDrive\Documents\Ai teacher robot\AI ROBOT AGENT\backend\knowledgebase.json",
    metadata_path=r"C:\Users\neesh\OneDrive\Documents\Ai teacher robot\AI ROBOT AGENT\backend\metadata.json",
    embed_path=r"C:\Users\neesh\OneDrive\Documents\Ai teacher robot\AI ROBOT AGENT\backend\title_embeddings.npy",
    index_path=r"C:\Users\neesh\OneDrive\Documents\Ai teacher robot\AI ROBOT AGENT\backend\faiss_index_ms_marco.index"
)

def get_lesson_prompt(subtopic: str, k: int = 5) -> str:
    
    passages = rag_retriever.retrieve(subtopic, k=k)
    if not passages:
        return "**[OUT_OF_SYLLABUS]** No matching content found."

    prompt = (
        "You are an engaging 8th-grade science teacher. "
        f"Use the following content to teach about **{subtopic}**:\n\n"
    )
    for i, p in enumerate(passages, start=1):
        prompt += f"Passage {i}:\n{p}\n\n"
    prompt += "Now deliver a clear, student-friendly lesson inline with this material."
    return prompt
