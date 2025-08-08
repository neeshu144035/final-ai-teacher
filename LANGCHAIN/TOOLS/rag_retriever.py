# import json
# import numpy as np
# import faiss
# from sentence_transformers import SentenceTransformer

# class RAGRetriever:
#     def __init__(
#         self,
#         knowledge_path: str,
#         metadata_path: str,
#         embed_path: str,
#         index_path: str,
#         model_name: str = "msmarco-distilbert-base-v4"
#     ):
        
#         with open(knowledge_path, "r", encoding="utf-8") as f:
#             self.knowledge = json.load(f)

        
#         with open(metadata_path, "r", encoding="utf-8") as f:
#             self.metadata = json.load(f)

        
#         self.embed_model = SentenceTransformer(model_name)

        
#         self.embeddings = np.load(embed_path)

#         self.index = faiss.read_index(index_path)

#         faiss.normalize_L2(self.embeddings)

#     def search(self, query: str, top_k: int = 3, threshold: float = 0.5) -> list:
#         q_emb = self.embed_model.encode([query], convert_to_numpy=True)
#         faiss.normalize_L2(q_emb)


#         distances, indices = self.index.search(q_emb, top_k)

#         results = []
#         for dist, idx in zip(distances[0], indices[0]):
#             if dist >= threshold:
#                 meta = self.metadata[idx]
#                 results.append({
#                     "title": meta["title"],
#                     "chapter": meta["chapter"],
#                     "score": float(dist),
#                     "index": int(idx)
#                 })
#         return results

#     def get_explanations(self, search_results: list, top_n: int = 1) -> list:
        
#         explanations = []
#         for match in search_results[:top_n]:
#             title = match["title"]
#             chapter = match["chapter"]

#             # Navigate nested JSON for content
#             chapter_data = self.knowledge.get(chapter, {})
#             content = chapter_data.get(title)
#             if content:
#                 explanations.append(content)
#             else:
#                 explanations.append(f"[Warning] Content for '{title}' not found in chapter '{chapter}'.")
#         return explanations
