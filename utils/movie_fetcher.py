"""Movie rating and review search helpers."""

import re
from typing import Dict, List, Optional
from urllib.parse import urlparse

import requests

from utils.web_search_fetcher import GEMINI_ENDPOINT


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


def is_movie_query(query: str) -> bool:
    """Return whether a query explicitly asks about a movie or its rating."""
    normalized = re.sub(r"\s+", " ", query or "").strip()
    if not normalized:
        return False

    if is_movie_review_query(normalized):
        return True

    has_rating = re.search(
        r"\b(?:ratings?|rated|tomatometer)\b",
        normalized,
        re.IGNORECASE,
    )
    has_movie_marker = re.search(r"\b(?:movie|film)\b", normalized, re.IGNORECASE)
    if not has_rating and not has_movie_marker:
        return False

    title = extract_movie_title(normalized)
    return bool(title and title.casefold() not in {"news", "rating", "ratings"})


def extract_movie_title(query: str) -> str:
    """Extract the movie title from common movie-review search phrases."""
    title = re.sub(r"\s+", " ", query or "").strip()
    title = re.sub(
        r"^(?:(?:can you|please)\s+)?(?:movie|film)\s+"
        r"(?:(?:reviews?|ratings?)\s*)?(?:of|for|about)?\s*",
        "",
        title,
        flags=re.IGNORECASE,
    )
    title = re.sub(
        r"^(?:reviews?|review|ratings?|rating)\s+(?:of|for)\s+"
        r"(?:(?:the\s+)?(?:movie|film)\s+)?",
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
    title = re.sub(
        r"\s+(?:(?:movie|film)\s+)?(?:reviews?|ratings?|rated)\s*$",
        "",
        title,
        flags=re.IGNORECASE,
    )
    title = re.sub(r"\s+(?:movie|film)\s*$", "", title, flags=re.IGNORECASE)
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


def _extract_imdb_rating(value) -> Optional[float]:
    if isinstance(value, dict):
        for key in ("ratingValue", "rating", "value", "aggregateRating"):
            if key in value:
                rating = _extract_imdb_rating(value[key])
                if rating is not None:
                    return rating
        return None
    if isinstance(value, list):
        for item in value:
            rating = _extract_imdb_rating(item)
            if rating is not None:
                return rating
        return None
    if isinstance(value, (int, float)):
        rating = float(value)
    else:
        match = re.search(
            r"(?<![\d.])((?:10(?:\.0+)?|[0-9](?:\.\d+)?))"
            r"(?:\s*(?:/10|out of 10))?(?![\d.])",
            str(value),
            re.IGNORECASE,
        )
        if not match:
            return None
        rating = float(match.group(1))
    if not 0 <= rating <= 10:
        return None
    return rating


def _flatten_search_text(value) -> str:
    if isinstance(value, dict):
        return " ".join(
            f"{key} {_flatten_search_text(item)}"
            for key, item in value.items()
        )
    if isinstance(value, list):
        return " ".join(_flatten_search_text(item) for item in value)
    return str(value) if value is not None else ""


def _find_google_imdb_rating(payload: Dict) -> Optional[float]:
    for container in (
        payload.get("knowledge_graph"),
        payload.get("answer_box"),
    ):
        if not isinstance(container, dict):
            continue
        for key in (
            "rating",
            "ratingValue",
            "rating_value",
            "aggregateRating",
            "rating_summary",
        ):
            if container.get(key) is not None:
                rating = _extract_imdb_rating(container[key])
                if rating is not None:
                    return rating
    return None


def _extract_labeled_rating(text: str, label: str, scale: int) -> Optional[float]:
    rating = r"(\d{1,3}(?:\.\d+)?)"
    patterns = (
        rf"{rating}\s*%?\s*{label}",
        rf"{label}[^0-9]{{0,30}}{rating}\s*%?",
    )
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            score = float(match.group(1))
            if 0 <= score <= scale:
                return score
    return None


def _extract_out_of_ten_rating(text: str, source: str) -> Optional[float]:
    rating = r"(\d(?:\.\d+)?)"
    patterns = (
        rf"\b{source}\b[^.\n]{{0,100}}?{rating}\s*(?:out of 10|/10)\b",
        rf"{rating}\s*(?:out of 10|/10)\s*[^.\n]{{0,60}}\b{source}\b",
    )
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            score = float(match.group(1))
            if 0 <= score <= 10:
                return score
    return None


def _parse_gemini_movie_ratings(answer: str) -> List[Dict[str, object]]:
    """Extract clearly labeled movie ratings from Gemini's grounded answer."""
    ratings = []
    sources = (
        (
            "Rotten Tomatoes",
            "Tomatometer",
            _extract_labeled_rating(
                answer,
                r"(?:Tomatometer|Rotten Tomatoes(?:\s+critic(?:s)?(?:\s+score)?)?)",
                100,
            ),
            100,
        ),
        (
            "Rotten Tomatoes",
            "Popcornmeter",
            _extract_labeled_rating(answer, r"Popcornmeter", 100),
            100,
        ),
        (
            "IMDb",
            "IMDb rating",
            _extract_out_of_ten_rating(answer, r"IMDb"),
            10,
        ),
        (
            "BookMyShow",
            "BookMyShow user rating",
            _extract_out_of_ten_rating(answer, r"BookMyShow"),
            10,
        ),
    )
    for source, label, rating, scale in sources:
        if rating is not None:
            ratings.append(
                {
                    "source": source,
                    "label": label,
                    "rating": rating,
                    "scale": scale,
                }
            )
    return ratings


def get_gemini_movie_ratings(
    movie_title: str,
    api_key: str,
) -> Optional[Dict[str, object]]:
    """Find grounded movie ratings and consensus using Gemini Google Search."""
    if not movie_title or not api_key:
        return None

    prompt = (
        f"Search the web for current ratings and critical/audience consensus for "
        f"the movie {movie_title!r}. Report only ratings you can verify from "
        "the search results. Include Rotten Tomatoes Tomatometer and "
        "Popcornmeter percentages when available, IMDb and BookMyShow scores "
        "out of 10 when available, and review or vote counts. Clearly label "
        "each source and distinguish ratings from different films or editions. "
        "Do not guess or fill in missing ratings."
    )
    response = requests.post(
        GEMINI_ENDPOINT,
        params={"key": api_key},
        json={
            "contents": [{"parts": [{"text": prompt}]}],
            "tools": [{"google_search": {}}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 1200},
        },
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    candidates = payload.get("candidates") or []
    if not candidates:
        return None

    candidate = candidates[0]
    parts = (candidate.get("content") or {}).get("parts") or []
    answer = " ".join(
        part.get("text", "").strip()
        for part in parts
        if isinstance(part, dict) and part.get("text")
    ).strip()
    if not answer:
        return None

    sources = []
    seen_urls = set()
    metadata = candidate.get("groundingMetadata") or {}
    for chunk in metadata.get("groundingChunks") or []:
        web = chunk.get("web") if isinstance(chunk, dict) else None
        if not isinstance(web, dict):
            continue
        url = web.get("uri", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            sources.append(
                {
                    "title": web.get("title") or "Google Search source",
                    "url": url,
                }
            )

    return {
        "answer": answer,
        "ratings": _parse_gemini_movie_ratings(answer),
        "sources": sources,
    }


def get_imdb_rating(movie_title: str, api_key: str) -> Optional[Dict[str, object]]:
    """Find an IMDb rating and available movie details in Google results."""
    if not movie_title or not api_key:
        return None

    queries = (
        f'site:imdb.com/title "{movie_title}" IMDb rating release date language '
        "director cast",
        f'"{movie_title}" IMDb rating',
    )
    rating_pattern = re.compile(
        r"(?:(?:IMDb\s+)?rating\s*[:\-]?\s*)?(\d(?:\.\d)?)(?:/10)\b",
        re.IGNORECASE,
    )
    labeled_rating_pattern = re.compile(
        r"\bIMDb\s+(?:rating|score)\s*[:\-]?\s*(\d(?:\.\d)?)\b",
        re.IGNORECASE,
    )
    best_details = {}
    graph_rating = None

    director_pattern = re.compile(
        r"\b(?:directed by|director(?:s)?\s*[:\-])\s*([^|.;\n]+)",
        re.IGNORECASE,
    )
    release_date_pattern = re.compile(
        r"\b(?:release date|released)\s*[:\-]?\s*([^|.;\n]+)",
        re.IGNORECASE,
    )
    language_pattern = re.compile(
        r"\b(?:languages?|original language)\s*[:\-]?\s*([^|.;\n]+)",
        re.IGNORECASE,
    )
    for query in queries:
        payload = _google_search(query, api_key)
        knowledge_graph = payload.get("knowledge_graph") or {}
        current_graph_rating = _find_google_imdb_rating(payload)
        if current_graph_rating is not None:
            graph_rating = current_graph_rating

        for result in payload.get("organic_results") or []:
            url = result.get("link") or result.get("url", "")
            if (
                not _is_domain(url, "imdb.com")
                or "/title/" not in urlparse(url).path
            ):
                continue

            rich_snippet = result.get("rich_snippet") or {}
            text = " ".join(
                part
                for part in (
                    result.get("title", ""),
                    result.get("snippet", ""),
                    _flatten_search_text(rich_snippet),
                )
                if part
            )
            rating = _extract_imdb_rating(rich_snippet)
            if rating is None:
                rating_match = rating_pattern.search(text)
                if rating_match:
                    rating = float(rating_match.group(1))
            if rating is None:
                labeled_rating_match = labeled_rating_pattern.search(text)
                if labeled_rating_match:
                    rating = float(labeled_rating_match.group(1))
            if rating is None:
                rating = current_graph_rating

            details = {"url": url}
            if rating is not None:
                details["rating"] = rating

            credits = {
                "release_date": (
                    ("release_date", "release date", "datePublished"),
                    release_date_pattern,
                ),
                "language": (
                    ("language", "languages", "inLanguage", "original language"),
                    language_pattern,
                ),
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
            if details.get("actors"):
                details["lead_cast"] = details["actors"]
            if rating is not None:
                return details
            if len(details) > len(best_details):
                best_details = details

    if graph_rating is not None:
        best_details["rating"] = graph_rating
    return best_details or None


def get_rotten_tomatoes_rating(
    movie_title: str,
    api_key: str,
) -> Optional[Dict[str, object]]:
    """Find a Rotten Tomatoes Tomatometer score in Google results."""
    if not movie_title or not api_key:
        return None

    queries = (
        f'site:rottentomatoes.com/m "{movie_title}" Tomatometer',
        f'"{movie_title}" Rotten Tomatoes Tomatometer',
    )
    rating_pattern = re.compile(
        r"(?:(?:Tomatometer|critic(?:s)?\s+score)[^0-9]{0,40}"
        r"(\d{1,3}(?:\.\d+)?)\s*%?|"
        r"(\d{1,3}(?:\.\d+)?)\s*%?[^.!?\n]{0,40}"
        r"(?:Tomatometer|critic(?:s)?\s+score))",
        re.IGNORECASE,
    )

    for query in queries:
        payload = _google_search(query, api_key)
        for result in payload.get("organic_results") or []:
            url = result.get("link") or result.get("url", "")
            path = urlparse(url).path.lower()
            is_movie_page = "/m/" in path or "/movies/" in path
            if not _is_domain(url, "rottentomatoes.com") or not is_movie_page:
                continue

            text = _flatten_search_text(result)
            rating_match = rating_pattern.search(text)
            if rating_match:
                score = rating_match.group(1) or rating_match.group(2)
                return {"rating": float(score), "url": url}

        structured_text = " ".join(
            _flatten_search_text(payload.get(key))
            for key in ("knowledge_graph", "answer_box")
        )
        rating_match = rating_pattern.search(structured_text)
        if rating_match:
            score = rating_match.group(1) or rating_match.group(2)
            return {"rating": float(score)}
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
