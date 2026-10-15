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
