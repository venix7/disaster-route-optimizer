# Disaster Evacuation Route Optimizer

A full-stack disaster-aware evacuation system that calculates safer routes on
a Manhattan road network, reacts to simulated flooding, recommends reachable
shelters, and explains deterministic results through a Groq-powered natural
language assistant.

The language model never calculates a route or invents hazard data. It selects
tools, receives structured facts from the existing Python services, and turns
those facts into a readable explanation.

## Project status

| Phase | Capability | Status |
| --- | --- | --- |
| 1 | Manhattan road network | Complete |
| 2 | Road attributes and dynamic costs | Complete |
| 3 | Custom Dijkstra routing engine | Complete |
| 4 | Flood simulation and dynamic rerouting | Complete |
| 5 | FastAPI backend | Complete |
| 6 | PostgreSQL, PostGIS, shelters, and route history | Complete |
| 7 | React, Vite, and Leaflet dashboard | Complete |
| 8 | Groq natural-language interface and deterministic explanations | Complete |
| 9 | Combined deployment, Neon, Railway, health checks, and CI | Deployment-ready |

## Architecture

```mermaid
flowchart TB
    Browser["React + Leaflet"] --> API["FastAPI"]
    API --> Evacuation["EvacuationService"]
    API --> Assistant["Groq + LangChain tools"]
    Evacuation --> Engine["Routing, flood, and shelter services"]
    Assistant --> Evacuation
    API --> Database["PostgreSQL + PostGIS"]
```

In production, Vite compiles the React application during the Docker build.
FastAPI then serves both the API and the compiled frontend from one container
and one public Railway URL.

## Main features

- Select a start and destination directly on the map.
- Calculate a route with the custom Dijkstra implementation.
- Rank roads using distance, travel time, traffic, and risk.
- Simulate a flood with affected and severe radii.
- Block severe-zone roads and increase risk on affected-zone roads.
- Recalculate routes against the current road-network state.
- Recommend the reachable active shelter with the lowest route cost.
- Store route history and shelter data in PostgreSQL/PostGIS.
- Ask grounded questions about the current route, flood, or shelter.
- Issue natural-language route and shelter commands using selected map points.

## Deterministic assistant design

The assistant has tools for route calculation, shelter recommendation, hazard
status, route explanation, and shelter explanation. Every tool calls the same
services used by the standard dashboard controls.

```mermaid
flowchart TB
    Question["Natural-language question"] --> Groq["Groq chooses a tool"]
    Groq --> Tool["LangChain tool"]
    Tool --> Algorithm["Existing deterministic service"]
    Algorithm --> Facts["Structured result and analysis"]
    Facts --> Answer["Groq explains the facts"]
```

The route cost weights are defined by the existing `CostCalculator`:

| Factor | Weight |
| --- | ---: |
| Distance | 0.30 |
| Travel time | 0.25 |
| Traffic | 0.10 |
| Risk | 0.35 |

## Technology stack

- Backend: Python, FastAPI, SQLAlchemy, GeoAlchemy2
- Routing: NetworkX/OSMnx graph data and a custom Dijkstra engine
- Database: PostgreSQL with PostGIS
- Assistant: LangChain and Groq
- Frontend: React, Vite, Axios, Leaflet, React Leaflet
- Deployment: Docker, Railway, Neon
- CI: GitHub Actions

## Repository layout

```text
.
├── .github/workflows/ci.yml
├── data/manhattan_graph.graphml
├── frontend/
│   ├── src/components/
│   ├── src/services/api.js
│   └── package.json
├── src/
│   ├── api/
│   ├── database/
│   ├── disaster/
│   ├── graph/
│   ├── llm/
│   ├── routing/
│   └── services/
├── tests/
├── .dockerignore
├── .env.example
├── DEPLOYMENT.md
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Environment variables

Copy `.env.example` to `.env` for local development. Never commit `.env`.

| Variable | Required | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | Yes | PostgreSQL connection string. Railway should receive the Neon URL. |
| `GROQ_API_KEY` | For assistant | Backend-only Groq API key. |
| `GROQ_MODEL` | No | Defaults to `openai/gpt-oss-20b`. |
| `GROQ_TIMEOUT_SECONDS` | No | Groq request timeout; defaults to 30 seconds. |
| `ASSISTANT_MAX_TOOL_ROUNDS` | No | Maximum tool-calling rounds; defaults to 4. |
| `DB_CONNECT_TIMEOUT_SECONDS` | No | Database connection timeout; defaults to 10 seconds. |
| `DB_RETRY_ATTEMPTS` | No | Startup connection attempts; defaults to 8. |
| `DB_RETRY_DELAY_SECONDS` | No | Initial retry delay; defaults to 2 seconds. |
| `ALLOWED_ORIGINS` | No | Extra comma-separated origins for split local hosting. |

The backend accepts both `postgresql://` and `postgresql+psycopg://` connection
strings and uses the installed psycopg v3 driver. It enables PostGIS and creates
the required tables during startup.

## Fastest local test: one command

Requirements: Docker Desktop must be running.

1. Create `.env` from `.env.example` and replace the Groq placeholder if you
   want to test the assistant.
2. From the project root, run:

   ```powershell
   docker compose up --build
   ```

3. Open <http://localhost:8000>.

This starts a local PostGIS database and the combined frontend/backend image.
The Compose project generates its own container names, so it does not conflict
with a hard-coded `evacuation_postgres` container. To use different host ports,
put values such as these in `.env`:

```dotenv
APP_PORT=8080
POSTGRES_PORT=5440
```

Then open `http://localhost:8080`. Stop the stack with `Ctrl+C`, followed by
`docker compose down`. The database volume remains available for the next run.

## Separate developer mode

Use this mode when changing React code and you want Vite hot reload.

### 1. Start PostgreSQL/PostGIS

```powershell
docker compose up database -d
```

### 2. Start FastAPI

```powershell
py -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
$env:PYTHONPATH="src"
python -m uvicorn api.main:app --reload
```

Set `GROQ_API_KEY` in `.env` before starting the backend if you want assistant
responses. FastAPI runs at <http://127.0.0.1:8000> and its OpenAPI UI is at
<http://127.0.0.1:8000/docs>.

### 3. Start Vite in another terminal

```powershell
cd frontend
npm ci
npm run dev
```

Vite runs at <http://localhost:5173>. Development requests use the local
FastAPI URL; production requests automatically use the same Railway origin.

## API endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Application and database readiness |
| `GET` | `/network/info` | Road network statistics |
| `POST` | `/route` | Deterministic evacuation route |
| `GET` | `/routes/history` | Recent route calculations |
| `POST` | `/disaster/flood` | Apply flood conditions |
| `POST` | `/disaster/reset` | Reset hazard state |
| `GET` | `/shelters` | Active shelters |
| `POST` | `/shelters` | Create a shelter |
| `POST` | `/evacuation/best-shelter` | Lowest-cost reachable shelter |
| `POST` | `/assistant/chat` | Grounded Groq assistant |

## Tests and CI

Run the small backend suite:

```powershell
$env:PYTHONPATH="src"
python -m unittest discover -s tests -v
```

Run frontend checks:

```powershell
cd frontend
npm ci
npm run lint
npm run build
```

GitHub Actions performs those checks and builds the combined Docker image on
pushes and pull requests to `main`. Railway's GitHub integration can wait for
all checks to pass before automatically deploying that commit.

## Production deployment

The finished production topology is one Railway web service connected to one
Neon PostgreSQL database. There is no separate frontend hosting service and no
Railway database container to wake manually.

Follow [DEPLOYMENT.md](DEPLOYMENT.md) for the remaining account-level steps:
push to GitHub, create Neon, connect Railway, add two secrets, enable the health
check and Serverless mode, and generate the single public domain.

## Operational behavior

- Startup retries temporary database connection failures with capped
  exponential backoff.
- Database connections have a finite connection timeout and are not retained
  in an application-side idle pool, helping Railway become inactive.
- `/health` returns success only after the routing service is initialized and a
  database query succeeds.
- Railway supplies `PORT`; the container listens on it automatically.
- A sleeping Railway service wakes when its public URL receives a request.
- A cold first request can be slower than normal and may occasionally require a
  browser refresh.

## Security notes

- `GROQ_API_KEY` and `DATABASE_URL` remain backend-only Railway variables.
- Do not create variables beginning with `VITE_` for either secret.
- `.env`, virtual environments, caches, `node_modules`, and compiled frontend
  output are ignored by Git and by the Docker build context.
- The repository includes no production credentials.
