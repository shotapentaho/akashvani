"""Live web search fallbacks for news queries."""

import os
from datetime import datetime
from typing import Dict, List
from urllib.parse import urlparse

import requests


GEMINI_MODEL = (os.getenv("GEMINI_MODEL") or "gemini-2.5-flash").strip()
GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)
SERPAPI_ENDPOINT = "https://serpapi.com/search.json"


def _article(
    title: str,
    description: str,
    source: str,
    url: str,
    author: str = "",
) -> Dict:
    return {
        "title": title or "Web result",
        "description": description or "",
        "content": description or "",
        "source": source,
        "publishedAt": datetime.utcnow().isoformat() + "Z",
        "author": author or source,
        "url": url or "#",
        "urlToImage": "",
    }


def get_gemini_search_results(
    query: str,
    api_key: str,
    top_k: int = 5,
) -> List[Dict]:
    """Search with Gemini's Google Search grounding and expose its citations."""
    if not query or not api_key:
        return []

    prompt = (
        f"Find the latest reliable information about: {query}\n"
        "Answer briefly, prioritize recent reporting, and distinguish "
        "confirmed facts from uncertainty."
    )
    try:
        response = requests.post(
            GEMINI_ENDPOINT,
            params={"key": api_key},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "tools": [{"google_search": {}}],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1000},
            },
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError):
        return []

    candidates = payload.get("candidates") or []
    if not candidates:
        return []
    candidate = candidates[0]
    parts = (candidate.get("content") or {}).get("parts") or []
    answer = " ".join(
        part.get("text", "").strip()
        for part in parts
        if isinstance(part, dict) and part.get("text")
    ).strip()

    results = []
    if answer:
        results.append(_article(f"Gemini result: {query}", answer, "Gemini", "#", "Gemini"))

    metadata = candidate.get("groundingMetadata") or {}
    chunks = metadata.get("groundingChunks") or []
    seen = set()
    for chunk in chunks:
        web = chunk.get("web") if isinstance(chunk, dict) else None
        if not isinstance(web, dict):
            continue
        url = web.get("uri", "")
        if not url or url in seen:
            continue
        seen.add(url)
        results.append(
            _article(
                web.get("title") or "Gemini web source",
                "Source found through Gemini Google Search grounding.",
                "Gemini / Google Search",
                url,
            )
        )
        if len(results) >= top_k:
            break
    return results[:top_k]


def _serpapi_results(query: str, api_key: str, **params) -> List[Dict]:
    if not query or not api_key:
        return []
    try:
        response = requests.get(
            SERPAPI_ENDPOINT,
            params={"engine": "google", "q": query, "api_key": api_key, **params},
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError):
        return []
    return payload.get("organic_results") or payload.get("video_results") or []


def get_serpapi_news_results(
    query: str,
    api_key: str,
    top_k: int = 5,
) -> List[Dict]:
    """Find current news articles through SerpAPI's Google News engine."""
    if not query or not api_key:
        return []

    try:
        response = requests.get(
            SERPAPI_ENDPOINT,
            params={
                "engine": "google_news",
                "q": query,
                "api_key": api_key,
                "gl": "in",
                "hl": "en",
                "num": max(1, min(top_k, 10)),
            },
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError):
        return []

    articles = []
    for result in payload.get("news_results") or []:
        if not isinstance(result, dict):
            continue
        url = result.get("link") or result.get("url", "")
        if not url:
            continue
        source = result.get("source") or {}
        if isinstance(source, dict):
            source_name = source.get("name", "SerpAPI News")
        else:
            source_name = str(source) or "SerpAPI News"
        articles.append(
            _article(
                result.get("title", "News article"),
                result.get("snippet", ""),
                source_name,
                url,
                source_name,
            )
        )
        if len(articles) >= top_k:
            break
    return articles


def get_bbc_search_results(query: str, api_key: str, top_k: int = 5) -> List[Dict]:
    """Find BBC News article pages, including the current /news/articles/ path."""
    results = _serpapi_results(
        f"site:bbc.com/news/articles/ {query}",
        api_key,
        num=max(1, min(top_k * 2, 10)),
    )
    articles = []
    for result in results:
        url = result.get("link") or result.get("url", "")
        parsed = urlparse(url)
        if parsed.netloc not in {"bbc.com", "www.bbc.com"} or not parsed.path.startswith(
            "/news/articles/"
        ):
            continue
        articles.append(
            _article(
                result.get("title", "BBC News article"),
                result.get("snippet", ""),
                "BBC News",
                url,
                "BBC News",
            )
        )
        if len(articles) >= top_k:
            break
    return articles


def get_youtube_search_results(
    query: str,
    api_key: str,
    top_k: int = 5,
) -> List[Dict]:
    """Find relevant YouTube videos through SerpAPI's Google video search."""
    results = _serpapi_results(
        query,
        api_key,
        tbm="vid",
        num=max(1, min(top_k, 10)),
    )
    videos = []
    for result in results:
        url = result.get("link") or result.get("url", "")
        if "youtube.com/" not in url and "youtu.be/" not in url:
            continue
        videos.append(
            _article(
                result.get("title", "YouTube result"),
                result.get("snippet", ""),
                "YouTube",
                url,
                result.get("channel", "YouTube"),
            )
        )
        if len(videos) >= top_k:
            break
    return videos
