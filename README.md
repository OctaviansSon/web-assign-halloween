# Space Bounty Hunters API — Midterm Practical Assignment

REST API for space bounty hunters: a database of **wanted criminals** and a **journal of their own hunting attempts**
(hunt logs).

## Stack
FastAPI (Python 3.12) · SQLAlchemy · PostgreSQL 16 · Docker Compose — the same backend framework and database as in my
course project (DevOps Study Planner API). For quick local runs and unit tests the app can also use SQLite.

```
app/
  main.py          FastAPI app, startup (create tables + sample data), /health
  config.py        settings from environment variables
  database.py      engine, session, table creation
  models.py        WantedCriminal, HuntLog (one-to-many)
  schemas.py       request / response models (validation)
  deps.py          DB session dependency, safe lookup by id
  seed_data.py     sample data: 8 criminals, 14 hunt logs
  seed.py          database import script (python -m app.seed)
  routers/         criminals.py (list, filters, sort, details) · hunts.py (CRUD)
tests/             pytest tests (SQLite, no Docker needed)
postman/           exported Postman collection
```

## Run (Docker)
Requirements: Docker Desktop (or Docker Engine + Compose v2).
```bash
docker compose up --build
```
When the log shows `Uvicorn running on http://0.0.0.0:8000`:

- Swagger UI: http://localhost:8000/docs
- Health check: http://localhost:8000/health

That is all — the tables are created and the sample data is imported automatically (see below).
A `.env` file is optional (`cp .env.example .env` on Linux/macOS, `copy .env.example .env` on PowerShell) —
use it only to change the database password or the port.

Useful commands:
```bash
docker compose ps                       # status (api becomes "healthy")
docker compose logs -f api              # API logs
docker compose exec db psql -U bounty -d bounty -c "SELECT id, nickname, reward FROM wanted_criminals;"
docker compose down                     # stop, keep the data
docker compose down -v                  # stop and DELETE the database volume
```

## Database setup / import
1. **Tables** are created on every startup by SQLAlchemy (`Base.metadata.create_all`), nothing to run manually.
2. **Sample data** (8 wanted criminals + 14 hunt logs, defined in `app/seed_data.py`) is imported on startup **only if the
   database is empty**, so restarting never creates duplicates (switch off with `AUTO_SEED=false`).
3. **Manual import / reset** at any time:
   ```bash
   docker compose exec api python -m app.seed            # import only if the tables are empty
   docker compose exec api python -m app.seed --reset    # delete all rows and import the sample data again
   ```
   (`--reset` on PostgreSQL uses `TRUNCATE ... RESTART IDENTITY`, so ids start from 1 again.)

### Run without Docker (optional)
```bash
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload                            # uses a local SQLite file bounty.db
# or against your own PostgreSQL:
# DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/bounty uvicorn app.main:app --reload
```

## Data model
**WantedCriminal** (`wanted_criminals`)

| Field | Type | Notes |
|---|---|---|
| `id` | integer | primary key |
| `name` | string, nullable | real name, `null` = unknown |
| `nickname` | string | criminal alias |
| `reward` | integer | bounty amount (>= 0) |
| `latitude`, `longitude` | float, nullable | last known coordinates (both or none; -90..90 / -180..180) |
| `location_note` | text, nullable | last known position as a text note (can be used instead of, or together with, coordinates) |
| `difficulty` | integer | 1..10 |
| `armed`, `has_crew`, `escape_master` | boolean | default `false` |

**HuntLog** (`hunt_logs`)

| Field | Type | Notes |
|---|---|---|
| `id` | integer | primary key |
| `criminal_id` | integer | foreign key → `wanted_criminals.id` |
| `success` | boolean | `true` = the criminal was captured |
| `notes` | text | description of the encounter |
| `created_at` | timestamp | set by the server when the record is created |

Relationship: **one `WantedCriminal` → many `HuntLog`** (`criminal.hunts` / `hunt.criminal`). Constraints (difficulty
range, coordinates, foreign key) are enforced by the database as well as by the API.

## API

### Wanted criminals
| Method | URL | Description |
|---|---|---|
| GET | `/api/criminals/` | list of criminals (filters and sorting below) |
| GET | `/api/criminals/{id}/` | one criminal |

Query parameters of `GET /api/criminals/` (all optional, combined with AND):

| Parameter | Meaning |
|---|---|
| `min_reward`, `max_reward` | bounty range, both inclusive |
| `armed`, `has_crew`, `escape_master` | `true` / `false` |
| `sort` | `reward` (ascending) or `-reward` (descending); default order is by id |

```bash
curl "http://localhost:8000/api/criminals/?min_reward=5000&armed=true&sort=-reward"
curl "http://localhost:8000/api/criminals/3/"
```

### Hunt logs (journal)
| Method | URL | Description | Success |
|---|---|---|---|
| GET | `/api/hunts/` | list all logs; optional `?criminal_id=5` | 200 |
| GET | `/api/hunts/{id}/` | one log | 200 |
| POST | `/api/hunts/` | record a capture attempt | 201 |
| PATCH | `/api/hunts/{id}/` | update `success` and/or `notes` | 200 |
| DELETE | `/api/hunts/{id}/` | delete a log | 204 |

```bash
curl -X POST http://localhost:8000/api/hunts/ -H "Content-Type: application/json" \
  -d '{"criminal_id": 3, "success": false, "notes": "Target escaped through an asteroid field."}'
```
```json
{
  "id": 15,
  "criminal_id": 3,
  "success": false,
  "notes": "Target escaped through an asteroid field.",
  "created_at": "2026-10-31T10:15:42.123456Z"
}
```

### Status codes and validation
| Situation | Response |
|---|---|
| id does not exist (criminal or hunt log), also `0`, negative or huge ids | **404** |
| id is not a number (`/api/hunts/abc/`, `?criminal_id=abc`) | **422** |
| POST: `criminal_id` does not refer to an existing criminal | **422** |
| POST: missing / wrongly typed `criminal_id` or `success` (strict types: `"yes"` or `1` are not booleans), `notes` not a string or longer than 5000 chars, malformed JSON | **422** |
| PATCH: empty body, no `success`/`notes`, or `null` values | **422** |
| list: unknown `sort` value, non-numeric or negative reward, invalid boolean, `min_reward` > `max_reward` | **422** |

Decisions worth knowing:
- `created_at` is **always generated by the server**. If a client sends it in POST or PATCH, the value is ignored.
  `criminal_id` of an existing log cannot be changed either.
- `notes` is optional on POST (defaults to an empty string); `criminal_id` and `success` are required.
- `GET /api/hunts/?criminal_id=<unknown id>` is a filter, so it returns `200` with an empty list, not 404.
- URLs end with `/` exactly as in the assignment; without the slash FastAPI redirects (307) to the right URL.
- Error bodies look like `{"detail": ...}`.

## Postman
1. Start the API (`docker compose up --build`).
2. Postman → **Import** → `postman/Space-Bounty-Hunters.postman_collection.json`.
3. Open the collection → **Run** → keep the order → **Run Space Bounty Hunters API**.

The collection (27 requests, every request has tests) contains three folders:
1. **Wanted criminals** — list, the assignment's example query (`min_reward=5000&armed=true&sort=-reward`), range +
   several filters, `armed=false`, ascending sort, details.
2. **Hunt logs (CRUD)** — list, filter by `criminal_id`, create, create with a client-supplied `created_at` (ignored),
   get, update (full and partial), delete, get after delete (404). The requests create and delete their own logs, so the
   pre-filled data stays intact and the collection can be run repeatedly.
3. **Invalid requests** — unknown criminal, invalid body, empty PATCH, 404 for missing ids, non-numeric id, invalid
   `sort`, `min_reward` > `max_reward`, invalid `criminal_id` filter.

The base URL is the collection variable `baseUrl` (default `http://localhost:8000`).

## Tests (optional, no Docker needed)
```bash
pip install -r requirements-dev.txt
pytest -q
```
The tests run against a temporary SQLite database filled with the same sample data and cover filters (including
`armed=false` and combinations), sorting, details, full CRUD, the server-side timestamp, the one-to-many relationship
and all the error cases above.

## Environment variables
| Variable | Description |
|---|---|
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | database credentials (defaults are built into `docker-compose.yml`) |
| `API_PORT` | host port of the API, default `8000` |
| `AUTO_SEED` | `true` (default) = import sample data into an empty database on startup |
| `DATABASE_URL` | SQLAlchemy URL; set by Docker Compose, defaults to SQLite `sqlite:///./bounty.db` |
