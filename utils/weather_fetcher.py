"""Current weather and three-day forecasts using Open-Meteo (no API key required)."""

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

_NON_LOCATION_WORDS = {
    "any",
    "inclement",
    "location",
    "locations",
    "severe",
    "with",
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

_WEATHER_CONDITIONS = {
    0: ("Sunny", "☀️"),
    1: ("Mostly sunny", "🌤️"),
    2: ("Partly cloudy", "🌤️"),
    3: ("Cloudy", "☁️"),
    45: ("Foggy", "🌫️"),
    48: ("Foggy", "🌫️"),
    51: ("Light drizzle", "🌦️"),
    53: ("Drizzle", "🌦️"),
    55: ("Heavy drizzle", "🌦️"),
    56: ("Freezing drizzle", "🌧️"),
    57: ("Heavy freezing drizzle", "🌧️"),
    61: ("Light rain", "🌧️"),
    63: ("Rainy", "🌧️"),
    65: ("Heavy rain", "🌧️"),
    66: ("Freezing rain", "🌧️"),
    67: ("Heavy freezing rain", "🌧️"),
    71: ("Light snow", "🌨️"),
    73: ("Snowy", "❄️"),
    75: ("Heavy snow", "❄️"),
    77: ("Snow grains", "❄️"),
    80: ("Light showers", "🌦️"),
    81: ("Showers", "🌦️"),
    82: ("Heavy showers", "🌧️"),
    85: ("Snow showers", "🌨️"),
    86: ("Heavy snow showers", "🌨️"),
    95: ("Thunderstorm", "⛈️"),
    96: ("Thunderstorm with hail", "⛈️"),
    99: ("Thunderstorm with heavy hail", "⛈️"),
}


def get_weather_condition(weather_code: int | None) -> tuple[str, str]:
    """Return a friendly label and visual icon for a WMO weather code."""
    return _WEATHER_CONDITIONS.get(weather_code, ("Weather unavailable", "🌡️"))


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

    location_words = set(re.findall(r"\b[a-z]+\b", location.lower()))
    if location.lower() in _EXTRA_WORDS or location_words & _NON_LOCATION_WORDS:
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
            "current": "temperature_2m,apparent_temperature,weather_code",
            "daily": "temperature_2m_max,temperature_2m_min,weather_code",
            "forecast_days": 3,
            "temperature_unit": "celsius",
            "timezone": "auto",
        },
        timeout=10,
    )
    response.raise_for_status()

    data = response.json()
    current = data.get("current") or {}
    daily = data.get("daily") or {}
    forecast = [
        {
            "date": forecast_date,
            "temperature_max": temperature_max,
            "temperature_min": temperature_min,
            "weather_code": weather_code,
        }
        for forecast_date, temperature_max, temperature_min, weather_code in zip(
            daily.get("time") or [],
            daily.get("temperature_2m_max") or [],
            daily.get("temperature_2m_min") or [],
            daily.get("weather_code") or [],
        )
    ]

    return {
        "location": place.get("name", location),
        "region": place.get("admin1", ""),
        "country": place.get("country", ""),
        "temperature": current.get("temperature_2m"),
        "apparent_temperature": current.get(
            "apparent_temperature"
        ),
        "weather_code": current.get("weather_code"),
        "unit": "°C",
        "timestamp": current.get("time"),
        "timezone": data.get("timezone"),
        "forecast": forecast,
    }