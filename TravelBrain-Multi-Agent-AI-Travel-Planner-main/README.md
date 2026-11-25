# TravelBrain: Multi-Agent AI Travel Planner

TravelBrain is a conversational travel-planning web app. It uses a LangGraph workflow to gather flight-related reference data, hotel research, and weather information, then asks a language model to produce a day-by-day itinerary and a concise final plan.

## Features

- Natural-language trip requests and a structured trip prompt builder
- Sequential specialist workflow for flights, hotels, weather, itinerary, and final response
- Groq-hosted language model calls through LangChain
- MCP integrations for AviationStack, Tavily, and OpenWeather
- PostgreSQL-backed LangGraph checkpoints for conversation state
- Optional Redis cache for external data lookups
- Browser controls to copy, download as Markdown, or print a plan
- Session-only browser settings for Groq and PostgreSQL credentials
- FastAPI health endpoint at `/health`

## How the agent workflow works

```text
Trip request
    |
    v
Flight agent -> Hotel research -> Weather lookup -> Itinerary agent -> Final response
    |                 |                 |                |                  |
    +-- AviationStack +-- Tavily         +-- OpenWeather  +-- Groq            +-- Groq
                      
             LangGraph state and checkpoints -> PostgreSQL
             Optional external-call cache   -> Redis
```

The nodes currently run in sequence. The flight agent uses AviationStack airport and airline reference tools and Groq to provide route guidance. Hotel research uses Tavily web search. The weather agent extracts a destination with Groq and retrieves current conditions and forecast data from OpenWeather. Groq then combines the available research into an itinerary and final response. LangGraph stores state against a thread ID in PostgreSQL.

## Important limitations

- Flight information is planning guidance based on airport/airline reference data and model-generated estimates. The current workflow does not retrieve live ticket inventory or confirm fares.
- Hotel results are web research, not booking inventory or verified availability.
- Generated budgets, routes, and itineraries are estimates. Verify details with providers before making travel decisions.
- PostgreSQL stores LangGraph checkpoints, but the frontend does not currently provide a saved-trip browser or reopen screen.
- The progress display is an estimate; agent stages are not streamed live from the backend.
- Public deployment exposes an unauthenticated planning endpoint. Configure provider usage limits and consider adding rate limits or an access gate before sharing the demo widely.

## Technology stack

Python 3.11 · FastAPI · LangGraph · LangChain · Groq · MCP · PostgreSQL · Psycopg · Redis (optional) · HTML · CSS · JavaScript · Docker

## Run locally on Windows

### Prerequisites

- Windows 10 or 11
- Python 3.11
- [uv](https://docs.astral.sh/uv/)
- A PostgreSQL database (a hosted PostgreSQL service such as Neon works)
- API keys for [Groq](https://console.groq.com/keys), [Tavily](https://app.tavily.com/home), [AviationStack](https://aviationstack.com/), and [OpenWeather](https://home.openweathermap.org/)

### Install and configure

Open PowerShell in the directory containing `pyproject.toml` and run:

```powershell
uv sync
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
```

Set these values in `.env`:

```dotenv
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b
DATABASE_URL=your_postgresql_connection_url
TAVILY_API_KEY=your_tavily_api_key
AVIATIONSTACK_API_KEY=your_aviationstack_api_key
OPENWEATHER_API_KEY=your_openweather_api_key

# Optional; disable if Redis is not running locally.
REDIS_URL=
CACHE_ENABLED=false
```

Keep real credentials in `.env`; never commit them. For hosted PostgreSQL such as Neon, use the provider's connection string. The app adds `sslmode=require` when the URL does not specify an SSL mode. The app uses PostgreSQL for its LangGraph checkpointer; SQLite is not configured as a substitute.

Start the app:

```powershell
uv run python app.py
```

Open <http://127.0.0.1:8000>. Check server status at <http://127.0.0.1:8000/health>. Keep the PowerShell process running while using the app.

The Settings panel can validate and hold `GROQ_API_KEY` and `DATABASE_URL` in server memory for the current browser session. The Tavily, AviationStack, and OpenWeather keys must be set in the server environment.

## Run with Docker

Docker Compose starts the app and Redis. Copy and configure `.env` first, then run:

```powershell
docker compose up --build
```

Open <http://127.0.0.1:8000>. To stop the services, press **Ctrl+C**. The Compose file also defines an optional local PostgreSQL service under the `local-db` profile; it is not started by default.

## Deploy to Render

The included Dockerfile binds to `0.0.0.0` and uses Render's `PORT`. In Render, create a **Web Service** with the **Docker** runtime:

- **Root Directory:** the directory containing `Dockerfile` and `pyproject.toml`; leave blank if those files are at the repository root.
- **Dockerfile Path:** `Dockerfile` (relative to the Root Directory).
- **Docker Command:** leave blank to use the Dockerfile's start command.
- **Health Check Path:** `/health`.
- **Environment:** add `GROQ_API_KEY`, `DATABASE_URL`, `TAVILY_API_KEY`, `AVIATIONSTACK_API_KEY`, and `OPENWEATHER_API_KEY` in the Render dashboard. `GROQ_MODEL` is optional.
- Leave `REDIS_URL` unset and set `CACHE_ENABLED=false` unless you have provisioned Redis.

Do not set `PORT` manually; Render provides it. Use a PostgreSQL connection URL with SSL enabled, such as the Neon connection string. Do not upload or commit your local `.env` file. See [Render's Docker deployment guide](https://render.com/docs/docker) and [environment variable guide](https://render.com/docs/configure-environment-variables).

## Repository layout

```text
app.py                 FastAPI app and local server entry point
src/agents/            Specialist agent implementations and prompts
src/graph/             LangGraph state, workflow, and runner
src/mcp_servers/       AviationStack, Tavily, and weather MCP integrations
src/clients/           Groq client, PostgreSQL checkpointer, Redis cache
src/config/            Environment and session credential configuration
src/api/               API credential validation and session storage
frontend/              HTML template, CSS, and browser JavaScript
pyproject.toml          Project metadata and dependencies
uv.lock                 Locked dependency versions
Dockerfile              Container image for the web service
docker-compose.yml      Local app, Redis, and optional PostgreSQL setup
LICENSE                 GNU GPL-3.0 license
```

## Verification status

The Windows application has been started locally by the project maintainer. The Docker Compose configuration parses successfully. A Render deployment and a complete end-to-end hosted API workflow have not been verified yet. No automated test suite is currently included in the repository.

