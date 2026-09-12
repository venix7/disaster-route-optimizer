# Railway + Neon deployment

The repository is already prepared to build React and FastAPI into one Docker
image. These are the only remaining steps that require your GitHub, Neon, Groq,
or Railway account.

## 1. Push this version to GitHub

Commit the Phase 9 files on your project branch, merge them into `main`, and
push `main`. Confirm that the **CI** workflow succeeds in the Actions tab.

Do not commit `.env`, `venv`, `node_modules`, `dist`, `cache`, or `__pycache__`.
The included ignore files already cover them.

## 2. Create the Neon database

1. Create a Neon project and database.
2. In **Connect**, copy its PostgreSQL connection string. A direct connection
   is suitable for this single low-traffic service because startup also creates
   the schema. Keep `sslmode=require` in the URL.
3. You do not need to create tables manually. On first startup, the application
   runs `CREATE EXTENSION IF NOT EXISTS postgis`, creates the tables, and seeds
   the initial shelters.

Optional verification in the Neon SQL Editor after the first successful start:

```sql
SELECT PostGIS_Version();
SELECT COUNT(*) FROM shelters;
```

## 3. Create the one Railway service

1. In Railway, choose **New Project** and **Deploy from GitHub repo**.
2. Select this repository and keep the root directory as `/`.
3. Open the service's **Variables** page and add:

   ```text
   DATABASE_URL=<the Neon connection string>
   GROQ_API_KEY=<your Groq API key>
   GROQ_MODEL=openai/gpt-oss-20b
   ```

   The first two values are secrets. Do not prefix them with `VITE_`.

4. In service settings, set the health-check path to `/health`. The default
   300-second health-check timeout is appropriate for the initial graph load.
5. In the service's deployment settings, select the `main` branch, keep GitHub
   autodeploy enabled, and enable **Wait for CI**. Railway will then deploy a
   `main` commit only after the included GitHub Actions checks pass.
6. Enable **Serverless** for the service, then redeploy once so the setting is
   applied to the new container.
7. In **Networking**, generate a Railway domain.

Railway detects the root `Dockerfile`; no build or start command needs to be
entered. Do not add a Railway PostgreSQL service—the production database is
Neon.

There is intentionally no `railway.toml`. Railway has
[deprecated Config as Code](https://docs.railway.com/config-as-code) for new
services, while [Serverless](https://docs.railway.com/deployments/serverless)
and **Wait for CI** are one-time service settings. Keeping those two switches
in the dashboard avoids committing a legacy file that a new Railway service
would ignore.

## 4. Run the final smoke test

Open only the generated Railway URL. The first request wakes Railway; FastAPI
then connects to Neon, which wakes the database if necessary. A cold start can
take longer than a normal request. If Railway returns a one-time 502 during the
first wake, wait several seconds and refresh.

Check the following:

- The dashboard loads from the Railway URL.
- Selecting start and destination points produces a route.
- A flood blocks/raises risk on roads and a new route avoids the changed roads.
- Resetting the disaster clears the flood state.
- Best shelter returns a shelter and route.
- “Why was this route selected?” returns a grounded Groq explanation.
- `<your-railway-url>/health` returns `status: healthy` and
  `database: connected`.
- After enough inactivity for Railway to sleep, opening the same URL wakes the
  application again without visiting Neon or another service first.

## If deployment fails

- `DATABASE_URL environment variable is not set`: add it to Railway Variables.
- Database retry messages: verify the complete Neon URL and `sslmode=require`.
- PostGIS permission error: run `CREATE EXTENSION IF NOT EXISTS postgis;` once
  in the Neon SQL Editor with the project owner role, then redeploy.
- Assistant returns 503: add `GROQ_API_KEY` and redeploy.
- Health check times out: verify the path is `/health`, the service uses the
  injected `PORT`, and the Neon database is reachable.
- Frontend opens but API calls target localhost: rebuild from this Phase 9
  version; production API requests are configured to use the same origin.
