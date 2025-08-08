# backend/tools/video_fetcher.py
import yt_dlp

def fetch_animated_videos(topic, num_videos=1):
    search_query = f"ytsearch{num_videos}:{topic} animation explained in english"
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "force_generic_extractor": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search_query, download=False)
        if "entries" in info and len(info["entries"]) > 0:
            video = info["entries"][0]
            if video.get("duration", 301) <= 300:
                return {
                    "title": video["title"],
                    "url": video["url"],
                    "id": video["id"]
                }
    return None
