# Weather AG UI

AG2 weather agent with A2A server and UI. Ask for current weather by city name or use your location; the agent uses Open-Meteo (no API key) for weather data and an LLM for conversation.

## Prerequisites

- **Python** 3.10–3.13
- **Node.js** and **pnpm** (for the UI)
- **OpenAI API key** (for the agent LLM)

## Run the project

You need two processes: the Python backend (agent + API) and the Next.js frontend.

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

- “What’s the weather in London?”
- “Weather in Tokyo”
- “What’s the weather here?” (uses browser location if allowed)

## Summary

| Component   | Command              | URL                    |
|------------|----------------------|------------------------|
| Backend    | `uv run python weather.py` | http://localhost:8000 |
| Frontend   | `cd ui && pnpm dev`  | http://localhost:3000  |

Weather data is from [Open-Meteo](https://open-meteo.com/) (no API key). The chatbot uses the OpenAI API; set `OPENAI_API_KEY` before starting the backend.
