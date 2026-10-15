"""Current weather lookup using the Open-Meteo APIs (no API key required)."""
import re
import requests

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

_PREFIX = r"(?:what(?:'s|\s+is)?\s+(?:the\s+)?)?(?:(?:current|today'?s?)\s+)?"
_TOPIC = r"(?:weather|temperature)"
_PATTERNS = [
    # "weather in Mumbai", "what is the weather in Delhi", "current temperature for Chennai"
    re.compile(rf"^\s*{_PREFIX}{_TOPIC}\s+(?:in|at|for|of)\s+(?P<loc>.+?)\s*$", re.IGNORECASE),
    # "weather Mumbai"
    re.compile(rf"^\s*{_PREFIX}{_TOPIC}\s+(?P<loc>.+?)\s*$", re.IGNORECASE),
]
_EXTRA_WORDS = {"in", "at", "for", "of", "news", "report", "forecast", "today", "now", "update"}


def extract_weather_location(query):
    """Return the location from a location-specific weather query, else None."""
    if not query or not isinstance(query, str):
        return None
    for pattern in _PATTERNS:
        match = pattern.match(query)
        if match:
            location = re.sub(r"\s+", " ", match.group("loc")).strip(" ?.,!;:\"'")
            location = re.sub(r"\s+(?:right now|today|now)$", "", location, flags=re.IGNORECASE).strip(" ?.,!;:")
            if not location or not re.search(r"[^\W\d_]", location):
                return None
            if location.lower() in _EXTRA_WORDS:
                return None
            # Too long to be a place name: likely a general news query
            if len(location.split()) > 5:
                return None
            return location
    return None


def get_current_weather(location):
    """Return current weather dict for a place name, or None if not found.

    Raises requests exceptions on network/API errors.
    """
    if not location:
        return None

    geo = requests.get(
        GEOCODE_URL,
        params={"name": location, "count": 1, "language": "en", "format": "json"},
        timeout=10,
    )
    geo.raise_for_status()
    results = geo.json().get("results") or []
    if not results:
        # Retry with only the first comma-separated part, e.g. "Bengaluru, India"
        first = location.split(",")[0].strip()
        if first and first != location:
            return get_current_weather(first)
        return None

    place = results[0]
    resp = requests.get(
        FORECAST_URL,
        params={
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "current": "temperature_2m,apparent_temperature",
            "temperature_unit": "celsius",
            "timezone": "auto",
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    current = data.get("current") or {}

    return {
        "location": place.get("name", location),
        "region": place.get("admin1", ""),
        "country": place.get("country", ""),
        "temperature": current.get("temperature_2m"),
        "apparent_temperature": current.get("apparent_temperature"),
        "unit": "°C",
        "timestamp": current.get("time"),
        "timezone": data.get("timezone"),
    }
