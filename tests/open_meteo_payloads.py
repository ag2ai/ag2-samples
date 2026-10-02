"""Canned Open-Meteo responses served by the fake upstream."""

GEOCODING = {
    "results": [
        {
            "name": "London",
            "country": "United Kingdom",
            "country_code": "GB",
            "admin1": "England",
            "latitude": 51.5,
            "longitude": -0.12,
        }
    ]
}

CURRENT = {
    "timezone": "Europe/London",
    "current_units": {
        "temperature_2m": "°C",
        "apparent_temperature": "°C",
        "relative_humidity_2m": "%",
        "wind_speed_10m": "km/h",
        "wind_direction_10m": "°",
        "precipitation": "mm",
    },
    "current": {
        "time": "2026-10-02T12:00",
        "temperature_2m": 14.0,
        "apparent_temperature": 12.5,
        "relative_humidity_2m": 70,
        "weather_code": 3,
        "wind_speed_10m": 11.0,
        "wind_direction_10m": 200,
        "precipitation": 0.0,
    },
}

DAILY = {
    "timezone": "Europe/London",
    "daily_units": {
        "temperature_2m_max": "°C",
        "temperature_2m_min": "°C",
        "precipitation_sum": "mm",
        "precipitation_probability_max": "%",
    },
    "daily": {
        "time": [f"2026-10-0{d}" for d in range(2, 9)],
        "weather_code": [61] * 7,
        "temperature_2m_max": [15.0] * 7,
        "temperature_2m_min": [8.0] * 7,
        "precipitation_sum": [1.2] * 7,
        "precipitation_probability_max": [60] * 7,
    },
}
