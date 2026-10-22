"""Search utilities for music requests."""

from typing import Dict, List

import requests


def is_song_query(query: str) -> bool:
    """Return whether a query explicitly asks for songs or music."""
    return any(
        word in (query or "").lower().split()
        for word in ("song", "songs", "music")
    )


def get_song_results(query: str, api_key: str, top_k: int = 5) -> List[Dict]:
    """Fetch music video results from SerpAPI's Google video search."""
    if not query or not api_key:
        return []

    response = requests.get(
        "https://serpapi.com/search.json",
        params={
            "engine": "google",
            "q": query,
            "tbm": "vid",
            "api_key": api_key,
            "num": max(1, min(top_k, 10)),
        },
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    results = payload.get("video_results") or payload.get("organic_results") or []

    songs = []
    for result in results:
        link = result.get("link") or result.get("url")
        title = result.get("title")
        if not link or not title or not link.startswith(("http://", "https://")):
            continue
        songs.append(
            {
                "title": title,
                "url": link,
                "description": result.get("snippet", ""),
                "source": result.get("source", "Video search"),
            }
        )
        if len(songs) >= top_k:
            break
    return songs
