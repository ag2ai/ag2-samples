# Weather Agent

AI-powered weather information specialist that provides current conditions and forecasts for any location using the Open-Meteo API.

## Overview

The Weather Agent retrieves real-time weather data and multi-day forecasts for locations worldwide. It provides temperature, precipitation, wind conditions, humidity, and other meteorological data through natural language queries, making weather information accessible without manual lookups.

## Authentication

No API key required. The agent uses the Open-Meteo API, which provides free weather data without authentication.

## Tools

The agent has direct access to weather data through the following tools:

| Tool | Description |
|------|-------------|
| `get_current_weather` | Retrieve current weather conditions for a location |
| `get_weather_forecast` | Get multi-day weather forecast for a location |

## Capabilities

### Current Conditions

#### Temperature Data
- Current temperature in Celsius or Fahrenheit
- Feels-like temperature (wind chill/heat index)
- Daily high and low temperatures
- Temperature trends

#### Precipitation
- Current precipitation status
- Rain probability
- Snowfall information
- Precipitation intensity

#### Wind Conditions
- Wind speed and direction
- Gust speeds
- Wind chill effects
- Beaufort scale interpretation

#### Atmospheric Data
- Humidity levels
- Barometric pressure
- Visibility conditions
- Cloud cover percentage

### Weather Forecasts

#### Daily Forecasts
- Multi-day temperature predictions
- Precipitation probability by day
- Expected conditions summary
- Sunrise and sunset times

#### Hourly Breakdowns
- Hour-by-hour temperature changes
- Precipitation timing
- Wind pattern changes
- Detailed condition progression

#### Extended Outlooks
- 7-day forecast summaries
- Weather trend analysis
- Seasonal pattern context
- Long-range predictions

### Location Support

#### Geographic Queries
- City and country lookups
- Coordinate-based queries
- Region and state searches
- Landmark references

#### Multiple Locations
- Compare weather across locations
- Travel route conditions
- Multi-city summaries
- Regional overviews

### Weather Alerts

#### Condition Warnings
- Severe weather notifications
- Temperature extremes
- High wind alerts
- Precipitation warnings

#### Activity Planning
- Outdoor activity recommendations
- Travel condition advisories
- Event weather planning
- Safety considerations

### Data Interpretation

#### Natural Language Summaries
- Plain English weather descriptions
- Activity-relevant summaries
- Contextual recommendations
- Comparative analysis

#### Trend Analysis
- Temperature change patterns
- Storm system tracking
- Seasonal comparisons
- Historical context

## Usage Examples

```
"What's the weather in New York?"
"Will it rain in London tomorrow?"
"Get the 5-day forecast for Tokyo"
"What's the temperature in Paris right now?"
"Is it going to snow in Denver this week?"
"Compare weather between Miami and Seattle"
"What should I wear for outdoor activities in Chicago today?"
"What's the humidity level in Singapore?"
```

## Output Formats

| Format | Content Type |
|--------|--------------|
| Text | `text/plain` |

## Model

Uses `gpt-4o-mini` for efficient, cost-effective responses.

## Endpoint

`/weather/` - Weather information and forecast operations
