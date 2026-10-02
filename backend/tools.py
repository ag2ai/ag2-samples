"""The agent's tools. Each one turns Open-Meteo data into the cards the UI renders."""

from typing import Annotated

import httpx2
from ag2 import Context, Inject, Variable, tool
from pydantic import Field

from . import openmeteo
from .models import (
    Coordinates,
    CurrentWeather,
    ForecastDay,
    Location,
    ToolError,
    User,
    WeeklyForecast,
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
    http: Annotated[httpx2.AsyncClient, Inject()],
    city: Annotated[
        str, Field(description="The city name (e.g., 'London', 'New York', 'Tokyo')")
    ],
    country: Annotated[
        str, Field(description="Optional country code to disambiguate (e.g., 'US', 'GB')")
    ] = "",
) -> Location | ToolError:
    try:
        location = await openmeteo.geocode_city(http, city, country)
        context.variables["location"] = location
        return location
    except ValueError as e:
        return ToolError(str(e))
    except httpx2.HTTPError as e:
        return ToolError(f"Error fetching coordinates: {str(e)}")
    except Exception as e:
        return ToolError(f"Unexpected error: {str(e)}")


@tool(
    description=(
        "Get the current weather at a set of coordinates. Use this when you have "
        "coordinates, e.g. from get_coords_by_city or from the getUserLocation frontend "
        "tool. Returns temperature, humidity, wind, and conditions."
    ),
)
async def get_current_weather_by_coords(
    http: Annotated[httpx2.AsyncClient, Inject()],
    coords: Annotated[
        Coordinates, Field(description="The coordinates to report the weather for")
    ],
    location: Annotated[Location | None, Variable(default=None)] = None,
) -> CurrentWeather | ToolError:
    try:
        data = await openmeteo.fetch_current_weather(http, coords)
        current = data["current"]
        units = data["current_units"]
        return CurrentWeather(
            location=openmeteo.location_label("Current Weather", coords, location),
            conditions=openmeteo.describe_weather(current["weather_code"]),
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

    except httpx2.HTTPError as e:
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
    http: Annotated[httpx2.AsyncClient, Inject()],
    coords: Annotated[
        Coordinates, Field(description="The coordinates to report the forecast for")
    ],
    location: Annotated[Location | None, Variable(default=None)] = None,
) -> WeeklyForecast | ToolError:
    try:
        data = await openmeteo.fetch_weekly_forecast(http, coords)
        daily = data["daily"]
        units = data["daily_units"]
        days = [
            ForecastDay(
                date=daily["time"][i],
                conditions=openmeteo.describe_weather(daily["weather_code"][i]),
                tempMax=f"{daily['temperature_2m_max'][i]}{units['temperature_2m_max']}",
                tempMin=f"{daily['temperature_2m_min'][i]}{units['temperature_2m_min']}",
                precipitation=f"{daily['precipitation_sum'][i]} {units['precipitation_sum']}",
                precipitationProbability=f"{daily['precipitation_probability_max'][i]}{units['precipitation_probability_max']}",
            )
            for i in range(len(daily["time"]))
        ]
        return WeeklyForecast(
            location=openmeteo.location_label("Weekly Forecast", coords, location),
            timezone=data["timezone"],
            days=days,
        )

    except httpx2.HTTPError as e:
        return ToolError(f"Error fetching forecast: {str(e)}")
    except Exception as e:
        return ToolError(f"Unexpected error: {str(e)}")


@tool(
    description=(
        "Say who the user is that you are talking to: their id and display name. Use when "
        "the user asks who they are or what name they are signed in as."
    ),
)
async def get_current_user(user: Annotated[User, Inject()]) -> User:
    # The User comes from dependencies, which only the backend's route fills in — never
    # from shared state, which the client can write to.
    return user
