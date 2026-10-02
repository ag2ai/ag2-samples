"""Data shapes shared by the tools, the agent and the UI."""

from dataclasses import dataclass


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
class User:
    """The person on the client, as established from a verified Access token."""

    id: str
    name: str


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
