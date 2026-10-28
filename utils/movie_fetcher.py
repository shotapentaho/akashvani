"""IMDb review search helpers."""

import re
from typing import Dict, List
from urllib.parse import urlparse

import requests


SERPAPI_ENDPOINT = "https://serpapi.com/search.json"


def is_movie_review_query(query: str) -> bool:
    """Return whether a query asks for a movie review."""
    normalized = re.sub(r"\s+", " ", query or "").strip()
    has_review = re.search(r"\breviews?\b", normalized, re.IGNORECASE)
    if not has_review:
        return False
    has_movie = re.search(r"\b(?:movie|film)\b", normalized, re.IGNORECASE)
    return bool(
        has_movie
        or re.search(r"\breviews?\s*$", normalized, re.IGNORECASE)
        or re.search(r"^\s*reviews?\s+(?:of|for)\b", normalized, re.IGNORECASE)
    )


def extract_movie_title(query: str) -> str:
    """Extract the movie title from common movie-review search phrases."""
    title = re.sub(r"\s+", " ", query or "").strip()
    title = re.sub(
        r"^(?:(?:can you|please)\s+)?(?:movie|film)\s+reviews?"
        r"(?:\s+(?:of|for|about))?\s*",
        "",
        title,
        flags=re.IGNORECASE,
    )
    title = re.sub(
        r"^(?:reviews?|review)\s+(?:of|for)\s+(?:(?:the\s+)?(?:movie|film)\s+)?",
        "",
        title,
        flags=re.IGNORECASE,
    )
    title = re.sub(
        r"^(?:the\s+)?(?:movie|film)\s+",
        "",
        title,
        flags=re.IGNORECASE,
    )
    title = re.sub(r"\s+(?:movie\s+)?reviews?\s*$", "", title, flags=re.IGNORECASE)
    return title.strip(" \t\r\n.,!?")


def get_imdb_reviews(
    movie_title: str,
    api_key: str,
    top_k: int = 5,
) -> List[Dict]:
    """Find IMDb review excerpts through SerpAPI's Google search results."""
    if not movie_title or not api_key:
        return []

    response = requests.get(
        SERPAPI_ENDPOINT,
        params={
            "engine": "google",
            "q": f'site:imdb.com "{movie_title}" reviews',
            "api_key": api_key,
            "num": max(1, min(top_k * 3, 10)),
        },
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()

    reviews = []
    seen_urls = set()
    for result in payload.get("organic_results") or []:
        url = result.get("link") or result.get("url", "")
        parsed = urlparse(url)
        path = parsed.path.lower()
        is_imdb_review = (
            parsed.netloc.lower() in {"imdb.com", "www.imdb.com"}
            and ("/review/" in path or "/reviews/" in path)
        )
        snippet = (result.get("snippet") or "").strip()
        if not is_imdb_review or not snippet or url in seen_urls:
            continue

        seen_urls.add(url)
        reviews.append(
            {
                "title": result.get("title") or f"IMDb review of {movie_title}",
                "text": snippet,
                "url": url,
            }
        )
        if len(reviews) >= top_k:
            break
    return reviews
