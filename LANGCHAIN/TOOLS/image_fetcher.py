import json
import os
import faiss
import torch
from sentence_transformers import SentenceTransformer

FIGURE_JSON = r"C:\Users\neesh\OneDrive\Documents\Ai teacher robot\AI ROBOT AGENT\backend\tools\output.json"
IMAGE_DIR = r"C:\Users\neesh\OneDrive\Documents\Ai teacher robot\AI ROBOT AGENT\backend\tools\images"
FAISS_INDEX_FILE = r"C:\Users\neesh\OneDrive\Documents\Ai teacher robot\AI ROBOT AGENT\backend\subchapter_faiss.index"
METADATA_FILE = r"C:\Users\neesh\OneDrive\Documents\Ai teacher robot\AI ROBOT AGENT\backend\subchapter_metadata.json"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
image_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2").to(device)

with open(FIGURE_JSON, "r", encoding="utf-8") as f:
    figures_data = json.load(f)

with open(METADATA_FILE, "r", encoding="utf-8") as f:
    metadata_figures = json.load(f)

index_figures = faiss.read_index(FAISS_INDEX_FILE)

def get_image_path(figure_ref, image_dir=IMAGE_DIR):
    base_name = figure_ref.replace(" ", "_")
    attempts = [
        f"{base_name}.png",
        f"{base_name}.jpg",
        f"figure_{base_name}.png"
    ]
    for attempt in attempts:
        test_path = os.path.join(image_dir, attempt)
        if os.path.exists(test_path):
            return test_path
    return None

def fetch_figures_only(subchapter_name):
    figures = [fig for fig in figures_data if fig["subchapter"] == subchapter_name]
    figure_blocks = []
    for fig in figures:
        fig_path = get_image_path(fig['figure'])
        if fig_path:
            figure_blocks.append({
                "name": fig['figure'],
                "path": fig_path, # Corrected: use fig_path instead of fig['path']
                "desc": fig['description']
            })
    return figure_blocks

def search_subchapter_by_query(query, top_k=1):
    query_embedding = image_model.encode([query], convert_to_numpy=True).astype('float32')
    _, indices = index_figures.search(query_embedding.reshape(1, -1), top_k)
    best_match_index = str(indices[0][0])
    return metadata_figures.get(best_match_index, None)

def fetch_images_for_topic(query):
    subchapter = search_subchapter_by_query(query)
    if not subchapter:
        return []
    return fetch_figures_only(subchapter)
