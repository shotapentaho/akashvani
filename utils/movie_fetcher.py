"""Movie rating and review search helpers."""

import re
from typing import Dict, List, Optional
from urllib.parse import urlparse

import requests


SERPAPI_ENDPOINT = "https://serpapi.com/search.json"


def _google_search(query: str, api_key: str, num: int = 10) -> Dict:
    response = requests.get(
        SERPAPI_ENDPOINT,
        params={
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "num": max(1, min(num, 10)),
        },
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


def _is_domain(url: str, domain: str) -> bool:
    hostname = urlparse(url).netloc.lower().split(":")[0]
    return hostname == domain or hostname.endswith(f".{domain}")


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

    payload = _google_search(
        f'site:imdb.com "{movie_title}" reviews',
        api_key,
        num=top_k * 3,
    )

    reviews = []
    seen_urls = set()
    for result in payload.get("organic_results") or []:
        url = result.get("link") or result.get("url", "")
        parsed = urlparse(url)
        path = parsed.path.lower()
        is_imdb_review = (
            _is_domain(url, "imdb.com")
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
                "source": "IMDb",
            }
        )
        if len(reviews) >= top_k:
            break
    return reviews


def _display_text(value) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        return _display_text(value.get("name") or value.get("value") or "")
    if isinstance(value, list):
        return ", ".join(filter(None, (_display_text(item) for item in value)))
    return ""


def get_imdb_rating(movie_title: str, api_key: str) -> Optional[Dict[str, object]]:
    """Find IMDb rating and available movie credits in Google results."""
    if not movie_title or not api_key:
        return None

    payload = _google_search(
        f'site:imdb.com/title "{movie_title}" IMDb rating director producer cast writer',
        api_key,
    )
    rating_pattern = re.compile(r"(?<!\d)(\d(?:\.\d)?)/10\b", re.IGNORECASE)
    director_pattern = re.compile(
        r"\b(?:directed by|director(?:s)?\s*[:\-])\s*([^|.;\n]+)",
        re.IGNORECASE,
    )

    for result in payload.get("organic_results") or []:
        url = result.get("link") or result.get("url", "")
        if not _is_domain(url, "imdb.com") or "/title/" not in urlparse(url).path:
            continue

        rich_snippet = result.get("rich_snippet") or {}
        text = " ".join(
            part
            for part in (
                result.get("title", ""),
                result.get("snippet", ""),
                " ".join(
                    str(value)
                    for value in rich_snippet.values()
                ),
            )
            if part
        )
        rating_match = rating_pattern.search(text)
        knowledge_graph = payload.get("knowledge_graph") or {}
        details = {"url": url}
        if rating_match:
            details["rating"] = float(rating_match.group(1))

        credits = {
            "director": (("director", "directed_by", "directed by"), director_pattern),
            "producer": (
                ("producer", "producers", "produced_by", "produced by"),
                re.compile(
                    r"\b(?:produced by|producers?\s*[:\-])\s*([^|.;\n]+)",
                    re.IGNORECASE,
                ),
            ),
            "actors": (
                ("actors", "cast", "starring", "stars"),
                re.compile(
                    r"\b(?:starring|stars|cast\s*[:\-])\s*([^|.;\n]+)",
                    re.IGNORECASE,
                ),
            ),
            "writers": (
                ("writers", "writer", "written_by", "written by"),
                re.compile(
                    r"\b(?:written by|writers?\s*[:\-])\s*([^|.;\n]+)",
                    re.IGNORECASE,
                ),
            ),
        }
        for field, (aliases, pattern) in credits.items():
            credit = next(
                (
                    _display_text(knowledge_graph[key])
                    for key in aliases
                    if knowledge_graph.get(key)
                    and _display_text(knowledge_graph[key])
                ),
                None,
            )
            if not credit:
                credit_match = pattern.search(text)
                if credit_match:
                    credit = credit_match.group(1).strip()
            if credit:
                details[field] = credit
        if len(details) > 1:
            return details
    return None


def get_rotten_tomatoes_rating(
    movie_title: str,
    api_key: str,
) -> Optional[Dict[str, object]]:
    """Find a Rotten Tomatoes Tomatometer score in Google results."""
    if not movie_title or not api_key:
        return None

    payload = _google_search(
        f'site:rottentomatoes.com/m "{movie_title}" Tomatometer',
        api_key,
    )
    rating_pattern = re.compile(
        r"(?:Tomatometer\s*[:\-]?\s*(\d{1,3}(?:\.\d+)?)\s*%|"
        r"(\d{1,3}(?:\.\d+)?)\s*%\s*Tomatometer)",
        re.IGNORECASE,
    )

    for result in payload.get("organic_results") or []:
        url = result.get("link") or result.get("url", "")
        if (
            not _is_domain(url, "rottentomatoes.com")
            or "/m/" not in urlparse(url).path.lower()
        ):
            continue

        text = " ".join(
            part
            for part in (
                result.get("title", ""),
                result.get("snippet", ""),
                " ".join(
                    str(value)
                    for value in (result.get("rich_snippet") or {}).values()
                ),
            )
            if part
        )
        rating_match = rating_pattern.search(text)
        if rating_match:
            score = rating_match.group(1) or rating_match.group(2)
            return {"rating": float(score), "url": url}
    return None


def get_rotten_tomatoes_reviews(
    movie_title: str,
    api_key: str,
    top_k: int = 5,
) -> List[Dict]:
    """Find Rotten Tomatoes review excerpts through SerpAPI Google results."""
    if not movie_title or not api_key:
        return []

    payload = _google_search(
        f'site:rottentomatoes.com/m "{movie_title}" reviews',
        api_key,
        num=top_k * 3,
    )
    reviews = []
    seen_urls = set()
    for result in payload.get("organic_results") or []:
        url = result.get("link") or result.get("url", "")
        path = urlparse(url).path.lower()
        snippet = (result.get("snippet") or "").strip()
        if (
            not _is_domain(url, "rottentomatoes.com")
            or "/m/" not in path
            or "/reviews" not in path
            or not snippet
            or url in seen_urls
        ):
            continue

        seen_urls.add(url)
        reviews.append(
            {
                "title": result.get("title")
                or f"Rotten Tomatoes review of {movie_title}",
                "text": snippet,
                "url": url,
                "source": "Rotten Tomatoes",
            }
        )
        if len(reviews) >= top_k:
            break
    return reviews
