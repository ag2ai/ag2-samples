from dataclasses import dataclass
from textwrap import dedent
from typing import Annotated

import httpx
from ag2 import Agent, Context, Variable, tool
from ag2.ag_ui import AGUIStream
from ag2.config import OpenAIResponsesConfig
from fastapi import FastAPI
from pydantic import Field

# Geocoding API to convert city names to coordinates
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
# Open-Meteo weather API (free, no API key required)
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

# One client for the process: a client per call would pay a TLS handshake per tool call.
_http = httpx.AsyncClient(timeout=10.0)


@dataclass(frozen=True)
class Coordinates:
    """A latitude and longitude pair, and nothing else."""

    latitude: float
    longitude: float


@dataclass(frozen=True)
class Location:
    """A resolved place: its name, country, region, and its coordinates."""

    name: str
    country: str
    region: str
    coordinates: Coordinates


@dataclass(frozen=True)
class ToolError:
    """A failed upstream call, reported to the model and the UI as data."""

    error: str


# The field names below are the wire contract the UI cards read, hence the camelCase.
@dataclass(frozen=True)
class CurrentWeather:
    """Current conditions at a set of coordinates."""

    location: str
    conditions: str
    temperature: str
    feelsLike: str
    humidity: str
    wind: str
    precipitation: str
    dataTime: str


@dataclass(frozen=True)
class ForecastDay:
    """One day of a weekly forecast."""

    date: str
    conditions: str
    tempMax: str
    tempMin: str
    precipitation: str
    precipitationProbability: str


@dataclass(frozen=True)
class WeeklyForecast:
    """A seven-day forecast at a set of coordinates."""

    location: str
    timezone: str
    days: list[ForecastDay]


async def _geocode_city(city: str, country: str = "") -> Location:
    """Convert a city name to a Location using the Open-Meteo geocoding API."""
    params = {"name": city, "count": "5", "language": "en", "format": "json"}
    response = await _http.get(GEOCODING_URL, params=params)
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
    description=(
        "Resolve a city (and optional country code) to a location: its name, country, "
        "region and coordinates. Use when you need coordinates for a place name, e.g. to "
        "pass to the weather tools, or to confirm which city was matched."
    ),
)
async def get_coords_by_city(
    context: Context,
    city: Annotated[
        str, Field(description="The city name (e.g., 'London', 'New York', 'Tokyo')")
    ],
    country: Annotated[
        str, Field(description="Optional country code to disambiguate (e.g., 'US', 'GB')")
    ] = "",
) -> Location | ToolError:
    try:
        location = await _geocode_city(city, country)
        context.variables["location"] = location
        return location
    except ValueError as e:
        return ToolError(str(e))
    except httpx.HTTPError as e:
        return ToolError(f"Error fetching coordinates: {str(e)}")
    except Exception as e:
        return ToolError(f"Unexpected error: {str(e)}")


# Coordinates round-trip through the model as JSON numbers and can come back at a different
# precision, so the cached Location is matched on a tolerance rather than on equality. A
# hundredth of a degree is about a kilometre — close enough to be the same place.
_SAME_PLACE_DEGREES = 0.01


def _location_label(heading: str, coords: Coordinates, location: Location | None) -> str:
    """Name the place the numbers actually describe.

    The cached Location supplies its name only while its Coordinates agree with the
    Coordinates being reported on. Otherwise the label falls back to the Coordinates, so
    that the heading is vague rather than wrong.
    """
    if location and _is_same_place(location.coordinates, coords):
        return f"{heading} at {location.name}, {location.country}"
    return f"{heading} at {coords.latitude:.2f}, {coords.longitude:.2f}"


def _is_same_place(a: Coordinates, b: Coordinates) -> bool:
    return (
        abs(a.latitude - b.latitude) <= _SAME_PLACE_DEGREES
        and abs(a.longitude - b.longitude) <= _SAME_PLACE_DEGREES
    )


async def _fetch_current_weather_at_coords(coords: Coordinates) -> dict:
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
    response = await _http.get(WEATHER_URL, params=params)
    response.raise_for_status()
    return response.json()


async def _fetch_weekly_forecast_at_coords(coords: Coordinates) -> dict:
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
    response = await _http.get(WEATHER_URL, params=params)
    response.raise_for_status()
    return response.json()


@tool(
    description=(
        "Get the current weather at a set of coordinates. Use this when you have "
        "coordinates, e.g. from get_coords_by_city or from the getUserLocation frontend "
        "tool. Returns temperature, humidity, wind, and conditions."
    ),
)
async def get_current_weather_by_coords(
    coords: Annotated[
        Coordinates, Field(description="The coordinates to report the weather for")
    ],
    location: Annotated[Location | None, Variable(default=None)] = None,
) -> CurrentWeather | ToolError:
    try:
        data = await _fetch_current_weather_at_coords(coords)
        current = data["current"]
        units = data["current_units"]
        return CurrentWeather(
            location=_location_label("Current Weather", coords, location),
            conditions=_get_weather_description(current["weather_code"]),
            temperature=f"{current['temperature_2m']}{units['temperature_2m']}",
            feelsLike=f"{current['apparent_temperature']}{units['apparent_temperature']}",
            humidity=f"{current['relative_humidity_2m']}{units['relative_humidity_2m']}",
            wind=(
                f"{current['wind_speed_10m']} {units['wind_speed_10m']} "
                f"from {current['wind_direction_10m']}{units['wind_direction_10m']}"
            ),
            precipitation=f"{current['precipitation']} {units['precipitation']}",
            dataTime=f"{current['time']} ({data['timezone']})",
        )

    except httpx.HTTPError as e:
        return ToolError(f"Error fetching weather data: {str(e)}")
    except Exception as e:
        return ToolError(f"Unexpected error: {str(e)}")


@tool(
    description=(
        "Get the 7-day weather forecast at a set of coordinates. Use when the user asks "
        "about the weather next week, the week ahead, or the upcoming days. Use after "
        "get_coords_by_city, or with coordinates from the getUserLocation frontend tool."
    ),
)
async def get_weather_next_week(
    coords: Annotated[
        Coordinates, Field(description="The coordinates to report the forecast for")
    ],
    location: Annotated[Location | None, Variable(default=None)] = None,
) -> WeeklyForecast | ToolError:
    try:
        data = await _fetch_weekly_forecast_at_coords(coords)
        daily = data["daily"]
        units = data["daily_units"]
        days = [
            ForecastDay(
                date=daily["time"][i],
                conditions=_get_weather_description(daily["weather_code"][i]),
                tempMax=f"{daily['temperature_2m_max'][i]}{units['temperature_2m_max']}",
                tempMin=f"{daily['temperature_2m_min'][i]}{units['temperature_2m_min']}",
                precipitation=f"{daily['precipitation_sum'][i]} {units['precipitation_sum']}",
                precipitationProbability=f"{daily['precipitation_probability_max'][i]}{units['precipitation_probability_max']}",
            )
            for i in range(len(daily["time"]))
        ]
        return WeeklyForecast(
            location=_location_label("Weekly Forecast", coords, location),
            timezone=data["timezone"],
            days=days,
        )

    except httpx.HTTPError as e:
        return ToolError(f"Error fetching forecast: {str(e)}")
    except Exception as e:
        return ToolError(f"Unexpected error: {str(e)}")


agent = Agent(
    "WeatherAgent",
    prompt=dedent("""
        You are a helpful weather assistant. Answer weather questions with the available
        tools; each tool's own description says when it applies.

        A weather tool needs coordinates, so resolve the place first.
        - For "weather here", "my location", "where I am", or similar: call the
          getUserLocation frontend tool, then pass the coordinates it returns to the
          weather tool the question calls for.
        - If getUserLocation fails (e.g. permission denied or location unavailable): ask
          the user for their city name ("I couldn't get your location. Which city would
          you like the weather for?").
        - For a city name: resolve it with get_coords_by_city, passing a country code when
          the name is ambiguous.

        Always be clear about which city you're reporting on — get_coords_by_city tells you
        which one it matched, and it is not always the one you asked for. If a request is
        unclear, ask for clarification.

        After calling a tool, reply with a single paragraph summarising the result, not a
        list of items. The UI renders the tool result as a card, so keep your text answer a
        concise, informative summary."""),
    config=OpenAIResponsesConfig(
        model="gpt-5.6-sol",
        streaming=True,
    ),
    tools=[
        get_coords_by_city,
        get_current_weather_by_coords,
        get_weather_next_week,
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
