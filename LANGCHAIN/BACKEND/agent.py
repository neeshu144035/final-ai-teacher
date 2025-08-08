import os
import re
from langchain.agents import Tool
from backend.tools.llm_tools import stream_grok
from backend.tools.refactored_retriever import RAGRetriever
from backend.tools.image_fetcher import fetch_figures_only, search_subchapter_by_query
from backend.tools.video_fetcher import fetch_animated_videos

# Initialize RAG retriever
rag_retriever = RAGRetriever(
    knowledge_path="backend/knowledgebase.json",
    metadata_path="backend/metadata.json",
    embed_path="backend/title_embeddings.npy",
    index_path="backend/faiss_index_ms_marco.index"
)


def custom_retrieve_tool(input_text: str) -> str:
    """
    Retrieve top-k textbook passages for the input query.
    """
    results = rag_retriever.retrieve(input_text, k=5)
    return "\n".join(results)


def strip_figure_mentions(text: str) -> str:
    """
    Remove textual figure references like 'Figure 1.3' from retrieved content.
    """
    return re.sub(r"Figure[\s_]*\d+(?:\.\d+)?", "", text, flags=re.IGNORECASE)

# Tools available to LangChain agents
tools = [
    Tool(
        name="RetrieveTextbook",
        func=custom_retrieve_tool,
        description="Retrieve textbook explanation for a given topic"
    ),
]


def get_lesson_prompt(subtopic: str) -> str:
    """
    Constructs the base lesson prompt for streaming a lesson sentence-by-sentence.
    Media tags and halting logic are handled here; resume logic is in get_resume_prompt.
    """
    retrieved = custom_retrieve_tool(subtopic)
    if not retrieved.strip():
        return (
            f"⚠️ You are deviating from the lesson topic. "
            f"Here’s a general, engaging explanation of '{subtopic}'—"  
            "stream it sentence by sentence, and after each sentence emit the token [[HALT]]."
        )

    retrieved_cleaned = strip_figure_mentions(retrieved)
    exact_subchapter = search_subchapter_by_query(subtopic)
    figures = fetch_figures_only(exact_subchapter) if exact_subchapter else []
    video = fetch_animated_videos(subtopic)

    image_list = (
        "\n".join(f"<<image:{os.path.basename(f['path'])}>>" for f in figures)
        if figures else "- None found"
    )
    video_tag = f"<<video:{video['id']}>>" if video and video.get("id") else "None"

    return (
        f"You are a fun and interactive 8th-grade science teacher.\n"
        f"Topic: '{subtopic}'.\n\n"
        "Use the textbook content below (ground every explanation in it). "
        "Stream your lesson one complete sentence at a time, and after each sentence output the token [[HALT]]. "
        "That signal tells the front end it can pause for student questions.\n\n"
        "# Lesson Content:\n"
        f"{retrieved_cleaned}\n\n"
        "# Available images (embed with <<image:NAME>>):\n"
        f"{image_list}\n\n"
        "# Available video (embed with <<video:ID>>):\n"
        f"{video_tag}\n\n"
        "Now, begin your flowing lesson. Whenever it makes sense to illustrate visually, "
        "insert the exact inline tag (<<image:...>> or <<video:...>>). "
        "Avoid repeating media. After each two or three related points, "
        "pose a follow-up question (e.g., 'Still with me?' or 'Need more detail?') "
        "as part of your streaming—always finishing each question sentence with [[HALT]]."
    )


def get_resume_prompt(last_halt: str, subtopic: str) -> str:
    
    print(f"[get_resume_prompt] last_halt={last_halt!r}, subtopic={subtopic!r}")
    retrieved = custom_retrieve_tool(subtopic)
    retrieved_cleaned = strip_figure_mentions(retrieved)
    exact_subchapter = search_subchapter_by_query(subtopic)
    figures = fetch_figures_only(exact_subchapter) if exact_subchapter else []
    video = fetch_animated_videos(subtopic)

    image_list = (
        "\n".join(f"<<image:{os.path.basename(f['path'])}>>" for f in figures)
        if figures else "- None found"
    )
    video_tag = f"<<video:{video['id']}>>" if video and video.get("id") else "None"

    return (
        f"You are a friendly 8th-grade science teacher continuing the lesson on '{subtopic}'.\n"
        f"The last thing I said was:\n\n"
        f"    \"{last_halt}\"\n\n"
        "First, welcome the student back with a natural bridge that recalls that point, ending with [[HALT]].\n"
        "Then continue the lesson, one complete sentence at a time, each ending with [[HALT]].\n\n"
        "# Lesson Context (do not repeat):\n"
        f"{retrieved_cleaned}\n\n"
        "# Available images (embed with <<image:NAME>>):\n"
        f"{image_list}\n\n"
        "# Available video (embed with <<video:ID>>):\n"
        f"{video_tag}\n"
    )