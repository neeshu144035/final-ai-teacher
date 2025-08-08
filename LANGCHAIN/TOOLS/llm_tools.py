import asyncio
import os
import google.generativeai as genai

# ✅ Configure Gemini API
genai.configure(api_key="AIzaSyBV6Vl8SvGMYyhaJDisF8zDYWa_7PZ82Lc")

# ✅ Set model
model = genai.GenerativeModel("gemini-1.5-flash-8b-latest")  # ✅ Correct

async def stream_chat(messages):
    queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def _worker():
        resp = model.chat(messages=messages, stream=True)
        for delta in resp:
            if getattr(delta, "text", None):
                asyncio.run_coroutine_threadsafe(queue.put(delta.text), loop)
        asyncio.run_coroutine_threadsafe(queue.put(None), loop)

    await loop.run_in_executor(None, _worker)

    while True:
        item = await queue.get()
        if item is None:
            break
        yield item


async def stream_grok(prompt: str):
    queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def sync_streaming(loop):
        try:
            response = model.generate_content(prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    asyncio.run_coroutine_threadsafe(queue.put(chunk.text), loop)
            asyncio.run_coroutine_threadsafe(queue.put(None), loop)
        except Exception as e:
            asyncio.run_coroutine_threadsafe(queue.put(f"[Error]: {str(e)}"), loop)
            asyncio.run_coroutine_threadsafe(queue.put(None), loop)

    await loop.run_in_executor(None, sync_streaming, loop)

    while True:
        item = await queue.get()
        if item is None:
            break
        yield item
        await asyncio.sleep(0.1)


async def summarize_text(text: str):
    prompt = (
        "You’re an expert teacher. Condense the following into 3–5 key bullet points:\n\n"
        f"{text}\n\n"
        "Format:\n• Point 1\n• Point 2\n• Point 3\n• Point 4\n• Point 5"
    )
    result = []
    async for chunk in stream_grok(prompt):
        result.append(chunk)
    return "".join(result)
