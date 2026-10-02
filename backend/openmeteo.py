"""Open-Meteo access: geocoding, current weather and the weekly forecast.

Nothing here knows about AG2; it only talks HTTP and returns plain data.
"""

import httpx2

from .models import Coordinates, Location

# Geocoding API to convert city names to coordinates
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
# Open-Meteo weather API (free, no API key required)
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


def new_client() -> httpx2.AsyncClient:
    """The client the app shares: one per process, as a client per call would pay a TLS
    handshake per tool call."""
    return httpx2.AsyncClient(timeout=10.0)

# WMO weather interpretation codes.
WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def describe_weather(weather_code: int) -> str:
    """Convert a WMO weather code to a human-readable description."""
    return WEATHER_CODES.get(weather_code, "Unknown")


async def geocode_city(http: httpx2.AsyncClient, city: str, country: str = "") -> Location:
    """Convert a city name to a Location using the Open-Meteo geocoding API."""
    params = {"name": city, "count": "5", "language": "en", "format": "json"}
    response = await http.get(GEOCODING_URL, params=params)
    response.raise_for_status()
    data = response.json()
    if "results" not in data or not data["results"]:
        raise ValueError(
            f"City '{city}' not found. Please check the spelling or try a different city name."
        )
    results = data["results"]

    location = results[0]
    if country:
        for result in results:
            if result.get("country_code", "").upper() == country.upper():
                location = result

    return Location(
        name=location["name"],
        country=location["country"],
        region=location["admin1"],
        coordinates=Coordinates(
            latitude=location["latitude"],
            longitude=location["longitude"],
        ),
    )


async def fetch_current_weather(http: httpx2.AsyncClient, coords: Coordinates) -> dict:
    params = {
        "latitude": str(coords.latitude),
        "longitude": str(coords.longitude),
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "apparent_temperature",
            "weather_code",
            "wind_speed_10m",
            "wind_direction_10m",
            "precipitation",
        ],
        "timezone": "auto",
    }
    response = await http.get(WEATHER_URL, params=params)
    response.raise_for_status()
    return response.json()


async def fetch_weekly_forecast(http: httpx2.AsyncClient, coords: Coordinates) -> dict:
    """Fetch the 7-day daily forecast from Open-Meteo."""
    params = {
        "latitude": str(coords.latitude),
        "longitude": str(coords.longitude),
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "weather_code",
            "precipitation_sum",
            "precipitation_probability_max",
        ],
        "timezone": "auto",
        "forecast_days": 7,
    }
    response = await http.get(WEATHER_URL, params=params)
    response.raise_for_status()
    return response.json()


# Coordinates round-trip through the model as JSON numbers and can come back at a different
# precision, so the cached Location is matched on a tolerance rather than on equality. A
# hundredth of a degree is about a kilometre — close enough to be the same place.
_SAME_PLACE_DEGREES = 0.01


def is_same_place(a: Coordinates, b: Coordinates) -> bool:
    return (
        abs(a.latitude - b.latitude) <= _SAME_PLACE_DEGREES
        and abs(a.longitude - b.longitude) <= _SAME_PLACE_DEGREES
    )


def location_label(heading: str, coords: Coordinates, location: Location | None) -> str:
    """Name the place the numbers actually describe.

    The cached Location supplies its name only while its Coordinates agree with the
    Coordinates being reported on. Otherwise the label falls back to the Coordinates, so
    that the heading is vague rather than wrong.
    """
    if location and is_same_place(location.coordinates, coords):
        return f"{heading} at {location.name}, {location.country}"
    return f"{heading} at {coords.latitude:.2f}, {coords.longitude:.2f}"
