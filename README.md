# Weather AG UI

An AG2 weather agent exposed to a React chat over the **AG-UI** protocol. Ask for current
weather by city name or from your browser location; the agent uses
[Open-Meteo](https://open-meteo.com/) (no API key) for weather data and an LLM for conversation.

## Prerequisites

- **Python** 3.10–3.14
- **Node.js** and **pnpm** (for the UI)
- **OpenAI API key** (for the agent LLM)

## Run the project

You need two processes: the Python backend (agent + AG-UI endpoint) and the Next.js frontend.

### 1. Backend (Python)

From the project root:

```bash
# Install dependencies (uses uv)
uv sync

# Set your OpenAI API key
export OPENAI_API_KEY="your-openai-api-key"

# Start the backend on http://localhost:8000
uv run python weather.py
```

The backend serves the agent at `http://localhost:8000/weather/`.

#### Environment variables

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `OPENAI_API_KEY` | yes | — | Authenticates the agent's LLM calls |

### 2. Frontend (Next.js)

In a second terminal, from the project root:

```bash
cd ui
pnpm install
pnpm dev
```

The app will be at **http://localhost:3000**. The UI talks to the backend at `http://localhost:8000/weather/`, so keep the backend running.

### 3. Use the app

Open http://localhost:3000 in your browser and ask for weather, e.g.:

- "What's the weather in London?"
- "Weather in Tokyo"
- "What's the weather here?" (uses browser location if allowed)
- "What's the weather next week?" (seven-day forecast)

## What the agent does

- **Current conditions** — temperature and feels-like, conditions, humidity, precipitation, wind
  speed and direction, and the observation time in the location's own timezone.
- **Seven-day forecast** — daily high and low, conditions, precipitation total and probability.
- **By city name** — the city is geocoded first. Ambiguous names can be disambiguated with a
  country code ("Springfield, US"), and the reply states which city was matched.
- **By browser location** — the frontend supplies coordinates from the browser's Geolocation API.
  If that is denied or unavailable, the agent asks for a city name instead.

**Which place a result is reported for.** The coordinates passed to a weather tool always
determine which weather is fetched. The heading above a card names a previously resolved city
only while that city's coordinates match the ones being reported on; otherwise it falls back to
the coordinates themselves. So asking about London and then about your own location gives you
your own weather, never London's.

## Summary

| Component | Command | URL |
|---|---|---|
| Backend | `uv run python weather.py` | http://localhost:8000 |
| Frontend | `cd ui && pnpm dev` | http://localhost:3000 |

Weather data is from [Open-Meteo](https://open-meteo.com/) (no API key). The chatbot uses the OpenAI API; set `OPENAI_API_KEY` before starting the backend.
