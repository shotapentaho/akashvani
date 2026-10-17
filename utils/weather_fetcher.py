"""Current weather lookup using the Open-Meteo APIs (no API key required)."""

import re

import requests


GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


_PREFIX = (
    r"(?:what(?:'s|\s+is)?\s+(?:the\s+)?)?"
    r"(?:(?:current|today'?s?)\s+)?"
)

_TOPIC = r"(?:weather|temperature)"

_PATTERNS = [
    # weather in Mumbai
    # what is the weather in Delhi
    # current temperature for Chennai
    re.compile(
        rf"^\s*{_PREFIX}{_TOPIC}\s+(?:in|at|for|of)\s+"
        r"(?P<loc>.+?)\s*$",
        re.IGNORECASE,
    ),

    # weather Mumbai
    re.compile(
        rf"^\s*{_PREFIX}{_TOPIC}\s+(?P<loc>.+?)\s*$",
        re.IGNORECASE,
    ),

    # Boston weather
    # Boston temperature
    # New Delhi current weather
    re.compile(
        r"^\s*(?P<loc>.+?)\s+"
        r"(?:(?:current|today'?s?)\s+)?"
        r"(?:weather|temperature)\s*$",
        re.IGNORECASE,
    ),
]

_EXTRA_WORDS = {
    "in",
    "at",
    "for",
    "of",
    "news",
    "report",
    "forecast",
    "today",
    "now",
    "update",
}

_US_STATE_CODES = {
    "al": "alabama", "ak": "alaska", "az": "arizona", "ar": "arkansas",
    "ca": "california", "co": "colorado", "ct": "connecticut",
    "de": "delaware", "fl": "florida", "ga": "georgia", "hi": "hawaii",
    "id": "idaho", "il": "illinois", "in": "indiana", "ia": "iowa",
    "ks": "kansas", "ky": "kentucky", "la": "louisiana", "me": "maine",
    "md": "maryland", "ma": "massachusetts", "mi": "michigan",
    "mn": "minnesota", "ms": "mississippi", "mo": "missouri",
    "mt": "montana", "ne": "nebraska", "nv": "nevada",
    "nh": "new hampshire", "nj": "new jersey", "nm": "new mexico",
    "ny": "new york", "nc": "north carolina", "nd": "north dakota",
    "oh": "ohio", "ok": "oklahoma", "or": "oregon", "pa": "pennsylvania",
    "ri": "rhode island", "sc": "south carolina", "sd": "south dakota",
    "tn": "tennessee", "tx": "texas", "ut": "utah", "vt": "vermont",
    "va": "virginia", "wa": "washington", "wv": "west virginia",
    "wi": "wisconsin", "wy": "wyoming",
}

_LOCATION_ALIASES = {
    "uk": "united kingdom",
    "gb": "united kingdom",
    "us": "united states",
    "usa": "united states",
}


def _clean_location(value: str) -> str | None:
    """Normalize and validate an extracted location."""
    location = re.sub(r"\s+", " ", value).strip(
        ' ?.,!;:"\''
    )

    location = re.sub(
        r"\s+(?:right now|today|now)$",
        "",
        location,
        flags=re.IGNORECASE,
    ).strip(" ?.,!;:")

    if not location:
        return None

    if not re.search(r"[^\W\d_]", location):
        return None

    if location.lower() in _EXTRA_WORDS:
        return None

    # Avoid treating long news sentences as place names.
    if len(location.split()) > 5:
        return None

    return location


def extract_weather_location(query: str | None) -> str | None:
    """
    Return the location from a location-specific weather query.

    Supported examples:
    - weather in Mumbai
    - what is the weather in Delhi
    - temperature at Bengaluru
    - weather Mumbai
    - Boston weather
    - Boston temperature
    - New Delhi current weather
    """
    if not query or not isinstance(query, str):
        return None

    for pattern in _PATTERNS:
        match = pattern.match(query)

        if match:
            return _clean_location(match.group("loc"))

    return None


def _normalise_place_part(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _location_hints(location: str) -> set[str]:
    """Return explicit region and country hints supplied with a location."""
    normalised = _normalise_place_part(location)
    parts = [_normalise_place_part(part) for part in location.split(",")[1:]]
    parts.extend(
        alias
        for short, alias in _LOCATION_ALIASES.items()
        if re.search(rf"\b{re.escape(short)}\b", normalised)
    )

    hints = {part for part in parts if part}
    for hint in tuple(hints):
        if len(hint) == 2 and hint in _US_STATE_CODES:
            hints.add(_US_STATE_CODES[hint])
    return hints


def _matching_place(results: list[dict], location: str) -> dict | None:
    hints = _location_hints(location)
    if not hints:
        return None

    for place in results:
        candidates = {
            _normalise_place_part(str(place.get("admin1", ""))),
            _normalise_place_part(str(place.get("admin2", ""))),
            _normalise_place_part(str(place.get("country", ""))),
            _normalise_place_part(str(place.get("country_code", ""))),
        }
        if hints.intersection(candidates):
            return place
    return None


def _select_place(results: list[dict], location: str) -> dict:
    """Prefer a geocoding result matching an explicit region or country hint."""
    return _matching_place(results, location) or results[0]


def _geocode_location(location: str) -> list[dict]:
    geo = requests.get(
        GEOCODE_URL,
        params={
            "name": location,
            "count": 10,
            "language": "en",
            "format": "json",
        },
        timeout=10,
    )
    geo.raise_for_status()

    results = geo.json().get("results") or []
    if not results:
        first = location.split(",")[0].strip()
        if first and first != location:
            return _geocode_location(first)
    return results


def get_weather_locations(location: str) -> list[dict]:
    """Return matching places, preserving ambiguity unless a hint disambiguates."""
    if not location:
        return []

    results = _geocode_location(location)
    if not results:
        return []

    matching = _matching_place(results, location)
    if matching:
        return [matching]

    unique = {}
    for place in results:
        identity = (
            _normalise_place_part(str(place.get("name", ""))),
            _normalise_place_part(str(place.get("admin1", ""))),
            _normalise_place_part(str(place.get("country", ""))),
        )
        unique.setdefault(identity, place)
    return list(unique.values())


def get_current_weather(location: str, place: dict | None = None):
    """Return current weather for a place or None if it is not found."""
    if not location:
        return None

    if place is None:
        places = get_weather_locations(location)
        if len(places) != 1:
            return None
        place = places[0]

    if not place:
        return None

    response = requests.get(
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
    response.raise_for_status()

    data = response.json()
    current = data.get("current") or {}

    return {
        "location": place.get("name", location),
        "region": place.get("admin1", ""),
        "country": place.get("country", ""),
        "temperature": current.get("temperature_2m"),
        "apparent_temperature": current.get(
            "apparent_temperature"
        ),
        "unit": "°C",
        "timestamp": current.get("time"),
        "timezone": data.get("timezone"),
    }