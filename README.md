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
# Install dependencies (uses uv). AG2 is installed from its main branch, which carries
# AG-UI 1.0, until a release with it is published.
uv sync

# Set your OpenAI API key and the secret shared with the frontend server
export OPENAI_API_KEY="your-openai-api-key"
export AUTH_SECRET="a-long-random-string"

# Start the backend on http://localhost:8000
uv run python -m backend
```

The backend serves the agent at `http://localhost:8000/weather/`. Every run needs an Access token
(see [Authorisation](#authorisation)).

#### Environment variables

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `OPENAI_API_KEY` | yes | — | Authenticates the agent's LLM calls. Read from the environment, never from source |
| `AUTH_SECRET` | yes | — | Signs and verifies Access tokens (HS256). **Backend and frontend server must use the same value**; there is no default, so a backend without it refuses every request |

### 2. Frontend (Next.js)

In a second terminal, from the project root:

```bash
cd ui
pnpm install
# The same AUTH_SECRET the backend uses
AUTH_SECRET="a-long-random-string" pnpm dev
```

The app will be at **http://localhost:3000**. The UI talks to the backend at `http://localhost:8000/weather/`, so keep the backend running.

### 3. Use the app

Open http://localhost:3000 in your browser, enter a name to sign in, and ask for weather, e.g.:

- "Who am I?" (the assistant answers with the name you signed in with)
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

## Authorisation

The backend serves the agent only to a signed-in **User**. A User is whoever a verified
**Access token** says they are — never anything the client merely claims.

1. The visitor enters a name in the UI.
2. A Next.js server route (`ui/app/api/token/route.ts`) signs an Access token — a JWT (HS256)
   carrying the User's id and display name — with `AUTH_SECRET`. The secret never reaches the
   browser.
3. The browser keeps the token and sends it as `Authorization: Bearer …` on every chat request.
   The CopilotKit runtime route builds its agent per request so it can forward that header to
   the backend.
4. The backend route in `backend/app.py` reads the header and calls `verify_access_token`. A missing,
   malformed, expired or wrongly signed token gets a `401` before the agent runs.
5. The resulting User is passed to the agent through its **dependencies**, not through shared
   state, so it is never echoed back to the browser and the client cannot supply or override it.
   The `get_current_user` tool reads it from there, which is how the assistant can say who it is
   talking to.

**This is a demonstration — do not ship it as is.** Signing in takes a name and checks nothing,
and the token sits in the browser's `localStorage`, where any script on the page can read it.
To use a real identity provider, replace `verify_access_token` in `backend/auth.py` (and the token
route in the UI): it is the only place that decides whether a token is valid, and the rest of
the backend only sees the `User` it returns.

## Tests

```bash
uv run pytest
```

The tests call the backend in process over HTTP with a scripted model and a stubbed weather
client, so they need no network, API key or running server.

## Summary

| Component | Command | URL |
|---|---|---|
| Backend | `uv run python -m backend` | http://localhost:8000 |
| Frontend | `cd ui && pnpm dev` | http://localhost:3000 |

Weather data is from [Open-Meteo](https://open-meteo.com/) (no API key). The chatbot uses the OpenAI API; set `OPENAI_API_KEY` and `AUTH_SECRET` before starting the backend.
