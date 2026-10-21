"""Helpers for auto-submitting searches after the user pauses typing."""
import re

DEBOUNCE_MS = 700
MIN_QUERY_LENGTH = 3

# Weather phrases that still lack a location, e.g. "weather", "weather in".
_INCOMPLETE_WEATHER = re.compile(
    r"^(?:(?:what(?:'s| is)?|how(?:'s| is))\s+)?(?:the\s+)?(?:current\s+)?"
    r"(?:weather|temperature|temp)(?:\s+(?:in|at|for|of|near|around|like))*$",
    re.IGNORECASE,
)


def normalize_query(query):
    """Trim and collapse whitespace; None becomes an empty string."""
    return re.sub(r"\s+", " ", query or "").strip()


def news_query_variants(query):
    """Return the original query and, when useful, a query without ``news``."""
    original = query or ""
    if re.fullmatch(r"severe\s+weather", normalize_query(original), re.IGNORECASE):
        return (original, "weather")

    if not re.search(r"\bnews\b", original, re.IGNORECASE):
        return (original,)

    without_news = normalize_query(
        re.sub(r"\bnews\b", "", original, flags=re.IGNORECASE)
    )
    return (original,) if not without_news else (original, without_news)


def is_auto_eligible(query):
    """True if a query is meaningful enough to run without a manual click."""
    q = normalize_query(query).strip(" ?.,!;:")
    if len(q) < MIN_QUERY_LENGTH or not re.search(r"[^\W\d_]", q):
        return False
    return not _INCOMPLETE_WEATHER.match(q)


def query_fingerprint(query, *settings):
    """Stable fingerprint of the normalized query plus settings that affect output."""
    return (normalize_query(query).lower(),) + tuple(settings)


def should_auto_run(query, fingerprint, last_fingerprint):
    """Auto-run only for eligible queries that were not already processed."""
    return is_auto_eligible(query) and fingerprint != last_fingerprint
