import os
import re
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.agent import get_lesson_prompt, get_resume_prompt, rag_retriever
from backend.tools.llm_tools import stream_grok, summarize_text

app = FastAPI()

# Serve images
def get_image_dir():
    return os.path.join(os.path.dirname(__file__), "tools", "images")
app.mount("/images", StaticFiles(directory=get_image_dir()), name="images")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------- Helpers ---------

async def classify_confirmation(reply: str) -> bool:
    prompt = (
        f"You are a tutor. The student replied:\n\"{reply}\"\n"
        "Does this mean 'no more doubts'? Answer 'Yes' or 'No'."
    )
    response = ""
    async for chunk in stream_grok(prompt):
        response += chunk
    return response.strip().lower().startswith("y")

# --------- Chat Endpoint ---------

class ChatRequest(BaseModel):
    subtopic: str
    history: list[dict]
    question: str

@app.post("/chat")
async def chat(req: ChatRequest):
    q = req.question.strip()

    # Retrieve lesson context via RAG
    lesson_content = "\n".join(rag_retriever.retrieve(req.subtopic, k=5)).strip() or "⚠️ (No lesson content found)"

    # Unified system prompt—no hard-coded branches in code
    system_prompt = f"""
You are an expert 8th-grade science teacher. The lesson content on "{req.subtopic}" is:

---
{lesson_content}
---

When the student asks a question, follow these instructions exactly:

1. **Marks-based answers**:  
   - If the student’s question contains "for X marks", immediately produce X numbered, exam-style points (vary format, include analogies).  

2. **Content questions**:  
   - Otherwise, answer the question concisely or in detail based on its length.

3. **Grounding**:  
   - Always ground your answer in the lesson content above.  
   - If a question cannot be answered from that content, **start** with "⚠️ You are deviating from the lesson topic." then give a concise general answer.

4. **Check-in**:  
   - End every response with exactly one context-specific check-in question about what you just explained, for example:  
     • "Did this cover everything you needed on {req.subtopic}?"  
     • "Does that clarify how the brain integrates sensory inputs?"

5. **Doubt follow-ups**:  
   - If the student’s next reply is a substantive question (anything ending in “?” that isn’t just “yes”/“no”), treat it as a new content question and answer it per these rules.  
   - If they ask “nth point”—e.g. “5th point”—extract that point from your last marks-based answer and expand it, still grounding in lesson content.

6. **Resuming**:  
   - If the student replies to your check-in with “yes” or “no” (or equivalent indicating no more doubts), respond with exactly `[[RESUME_LESSON]]` and nothing else.

Here is the conversation so far:
{chr(10).join(f"{turn['role'].upper()}: {turn['text']}" for turn in req.history)}
STUDENT: {q}
"""

    async def event_stream():
        async for chunk in stream_grok(system_prompt):
            yield chunk

    return StreamingResponse(event_stream(), media_type="text/plain")

# --------- WebSocket Lesson Stream ---------

@app.websocket("/ws/lesson")
async def lesson_stream(websocket: WebSocket):
    await websocket.accept()
    data = await websocket.receive_json()
    print(f"[lesson_stream] Received payload: {data!r}")

    # Decide whether starting fresh or resuming
    subtopic = data.get("subtopic")
    resume_text = data.get("resumeFrom")
    if resume_text:
        print("[lesson_stream] Calling get_resume_prompt…")
        prompt = get_resume_prompt(resume_text, subtopic)
        print("[lesson_stream] Resumed prompt is:", prompt[:200], "...")
    else:
        print(f"[lesson_stream] → Starting fresh on topic: {subtopic!r}")
        
        prompt = get_lesson_prompt( subtopic)
    # If fallback warning
    if prompt.startswith("⚠️"):
        await websocket.send_text(f"\n{prompt}\n")

    buffer = ""
    async for chunk in stream_grok(prompt):
        buffer += chunk

        # Flush everything up through each [[HALT]] marker immediately
        while "[[HALT]]" in buffer:
            before, after = buffer.split("[[HALT]]", 1)
            await websocket.send_text(before + "[[HALT]]")
            buffer = after

        # Also flush on natural boundaries if buffer grows too large
        if len(buffer) > 300 or buffer.endswith((".", "!", "?")):
            await websocket.send_text(buffer)
            buffer = ""

    # Flush any remaining text
    if buffer:
        await websocket.send_text(buffer)

    # Lesson complete and summary
    await websocket.send_text("\n\n**Lesson Complete!**")
    summary = await summarize_text(buffer)
    await websocket.send_text(f"**Summary:** {summary}")
    await websocket.send_text("[[DONE]]")
    await websocket.close()
