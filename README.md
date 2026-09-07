# Disaster Evacuation Route Optimizer

A disaster-aware Manhattan routing application with a FastAPI backend,
custom Dijkstra routing, PostgreSQL/PostGIS shelters, flood simulation,
and a React + Leaflet dashboard.

Phase 8 adds a Groq natural-language interface through LangChain. Groq
does not calculate routes or hazard values. It calls the existing Python
services and explains their deterministic results.

## Phase 8 flow

```text
User message + current dashboard context
                 |
                 v
         Groq tool selection
                 |
                 v
 find_route / find_best_shelter / get_hazards
       explain_route / explain_shelter
                 |
                 v
 Existing services + deterministic route analysis
                 |
                 v
       Grounded response + optional UI action
```

Natural-language route commands use only the start and destination already
selected on the map. Place names are not converted into guessed coordinates.

## Backend setup

1. Create and activate a Python virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Start PostgreSQL/PostGIS:

   ```bash
   docker compose up -d
   ```

4. Copy `.env.example` to `.env`, then replace the Groq placeholder:

   ```env
   DATABASE_URL=postgresql+psycopg://evacuation_user:evacuation_password@localhost:5433/evacuation_db
   GROQ_API_KEY=your_real_key
   GROQ_MODEL=openai/gpt-oss-20b
   ```

5. Start FastAPI from the project root:

   ```bash
   PYTHONPATH=src uvicorn api.main:app --reload
   ```

The Groq key stays in the backend environment. Do not create a
`VITE_GROQ_API_KEY` variable.

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Assistant API

`POST /assistant/chat`

```json
{
  "message": "Why was this route selected?",
  "context": {
    "start_location": {
      "latitude": 40.731,
      "longitude": -74.001
    },
    "destination_location": {
      "latitude": 40.738,
      "longitude": -73.992
    },
    "route": {
      "nodes": [1, 2],
      "edges": [[1, 2, 0]],
      "total_cost": 0.25,
      "metrics": {
        "total_distance": 100,
        "total_travel_time": 12,
        "average_risk": 0.1,
        "maximum_risk": 0.1,
        "road_count": 1
      }
    },
    "flood": {
      "active": false
    }
  },
  "history": []
}
```

The response contains the assistant reply, a `tools_used` audit trail, and
optional deterministic `actions` that let the frontend display a route or
shelter recommendation returned by the existing backend.

## Tests

The Phase 8 deterministic tests do not call Groq:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```
