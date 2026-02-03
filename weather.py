import json
from dataclasses import asdict, dataclass
from textwrap import dedent
from typing import Annotated

import httpx
from autogen import ConversableAgent, LLMConfig
from autogen.agentchat import ContextVariables, ReplyResult
from autogen.ag_ui import AGUIStream
from autogen.tools import tool
from fastapi import FastAPI

# Geocoding API to convert city names to coordinates
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
# Open-Meteo weather API (free, no API key required)
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


@dataclass(frozen=True)
class Coordinates:
    """Latitude and longitude for a location."""

    latitude: float
    longitude: float


@dataclass(frozen=True)
class Location:
    """Location name and coordinates."""

    name: str
    country: str
    region: str
    coordinates: Coordinates


def _geocode_city(city: str, country: str = "") -> Location:
    """Convert city name to coordinates using Open-Meteo geocoding API."""
    params = {"name": city, "count": "5", "language": "en", "format": "json"}
    with httpx.Client(timeout=10.0) as client:
        response = client.get(GEOCODING_URL, params=params)
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


@tool(
    description="Get latitude and longitude for a city (and optional country). Use when you need coordinates for a place name, e.g. to pass to other tools or to confirm a location.",
)
def get_coords_by_city(
    context_variables: ContextVariables,
    city: Annotated[
        str,
        "The city name (e.g., 'London', 'New York', 'Tokyo')",
    ],
    country: Annotated[
        str,
        "Optional country code to disambiguate (e.g., 'US', 'UK')",
    ] = "",
) -> ReplyResult:
    try:
        location = _geocode_city(city, country)
        context_variables.set("location", location)
        return ReplyResult(
            message=json.dumps(asdict(location.coordinates)),
            context_variables=context_variables,
        )
    except ValueError as e:
        return str(e)
    except httpx.HTTPError as e:
        return f"Error fetching coordinates: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


def _fetch_current_weather_at_coords(coords: Coordinates) -> dict:
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
    with httpx.Client(timeout=10.0) as client:
        response = client.get(WEATHER_URL, params=params)
        response.raise_for_status()
        return response.json()


@tool(
    description="Get the current weather at a location given its latitude and longitude. Use this when you have coordinates (e.g. from getUserLocation). Returns temperature, humidity, wind, and conditions.",
)
def get_current_weather_by_coords(
    context_variables: ContextVariables,
    coords: Annotated[Coordinates, "The coordinates of the location"],
) -> dict:
    """
    Get the current weather at coordinates (e.g. from user's device location).

    Args:
        latitude: Latitude (-90 to 90)
        longitude: Longitude (-180 to 180)

    Returns:
        A dict with current weather information
    """
    try:
        if location := context_variables.get("location"):
            coords = location.coordinates
            location_label = f"Current Weather at {location.name}, {location.country}"
        else:
            coords = coords
            location_label = f"Current Weather at your location ({coords.latitude:.2f}, {coords.longitude:.2f})"

        data = _fetch_current_weather_at_coords(coords)
        current = data["current"]
        units = data["current_units"]
        weather_desc = _get_weather_description(current["weather_code"])
        return {
            "location": location_label,
            "conditions": weather_desc,
            "temperature": f"{current['temperature_2m']}{units['temperature_2m']}",
            "feelsLike": f"{current['apparent_temperature']}{units['apparent_temperature']}",
            "humidity": f"{current['relative_humidity_2m']}{units['relative_humidity_2m']}",
            "wind": (
                f"{current['wind_speed_10m']} {units['wind_speed_10m']} "
                f"from {current['wind_direction_10m']}{units['wind_direction_10m']}"
            ),
            "precipitation": f"{current['precipitation']} {units['precipitation']}",
            "dataTime": f"{current['time']} ({data['timezone']})",
        }

    except httpx.HTTPError as e:
        return {"error": f"Error fetching weather data: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


agent = ConversableAgent(
    name="WeatherAgent",
    description=dedent("""
        Global weather information specialist providing real-time weather conditions
        for cities worldwide. Get current temperature, humidity, wind conditions, precipitation.

        Capabilities:

        Current Weather
        - Real-time temperature (actual and feels-like)
        - Weather conditions (clear, cloudy, rain, snow, etc.)
        - Humidity levels and precipitation
        - Wind speed and direction
        - Data for any city worldwide

        Location Support
        - Works with city names globally
        - Supports country codes for disambiguation
        - Automatic timezone detection
        - Coordinates-based precision
        - Whenever you need the user's current position: call the getUserLocation frontend tool
          first. If it succeeds, use get_current_weather_by_coords(coordinates).
          If getUserLocation fails (error returned), ask the user for their city name and use
          get_coords_by_city(city, country), then use get_current_weather_by_coords(coordinates).
    """),
    system_message=dedent("""You are a helpful weather assistant. When users ask about weather,
        use the available tools to fetch current conditions or forecasts.

        Getting the user's location:
        - For "weather here", "my location", "current location", "where I am", or similar: first
          call the getUserLocation frontend tool to get latitude and longitude.
        - If getUserLocation succeeds: use get_current_weather_by_coords(latitude, longitude) for
          current weather.
        - If getUserLocation fails (returns an error, e.g. permission denied or location unavailable):
          fall back to asking the user for their city name (e.g. "I couldn't get your location.
          Which city would you like the weather for?"). Then use get_coords_by_city(city, country),
          then use get_current_weather_by_coords(coordinates).

        For explicit city names: use get_coords_by_city(city, country), then use get_current_weather_by_coords(coordinates).
        Always be clear about which city you're reporting on. If a user's request is unclear
        (e.g. which city they mean), ask for clarification. Provide weather information in a
        clear, easy-to-read format.

        After calling any tool, keep your reply minimal so the UI can render the tool result.
        Prefer a short acknowledgment with no extra details."""),
    llm_config=LLMConfig({"model": "gpt-5"}),
    functions=[
        get_coords_by_city,
        get_current_weather_by_coords,
    ],
)


stream = AGUIStream(agent)

app = FastAPI()
app.mount("/weather", stream.build_asgi())


def _get_weather_description(weather_code: int) -> str:
    """Convert WMO weather code to human-readable description."""
    weather_codes = {
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
    return weather_codes.get(weather_code, "Unknown")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
