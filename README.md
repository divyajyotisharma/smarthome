# SmartHome

SmartHome is a FastAPI backend for a home/client context that lets them register appliances, collect metrics, inspect historical readings, and generate daily or custom-range reports from the same seeded demo data.

## Tech Stack

- Python 3.12
- FastAPI
- SQLite
- SQLAlchemy
- Pydantic
- APScheduler
- pytest

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Run The App

```bash
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Swagger UI:

`http://127.0.0.1:8000/docs`

## Run Tests

```bash
.venv/bin/python -m pytest -v
```

## Reset Demo Data

Delete `data/smarthome.db` and restart the app.

The backend recreates tables and reseeds demo data on startup only when it is missing.

## Swagger Review Flow

1. Open `http://127.0.0.1:8000/docs`
2. Run `GET /health` to confirm the API is running.
3. Run `GET /homes/1` to view the seeded demo home/client context.
4. Run `GET /vendors` to view supported mock vendors and appliance types.
5. Run `GET /homes/1/appliances` to list appliances registered under the demo home.
6. Run `GET /homes/1/appliances/1` to view one appliance.
7. Run `POST /homes/1/appliances` to register a new appliance:

```json
{
  "display_name": "Bedroom AC",
  "vendor": "zenith_iot",
  "appliance_type": "air_conditioner",
  "vendor_device_id": "zenith-ac-404",
  "collection_interval_seconds": 60
}
```

8. Run `POST /homes/1/collect` to manually collect one metric reading for each active appliance.
9. Run `GET /homes/1/metrics` to view stored historical metric readings.
10. Run `GET /homes/1/metrics?start_date=2026-06-30&end_date=2026-06-30` to filter readings by date.
11. Run `GET /homes/1/reports/daily?date=2026-06-30` to generate one daily report from stored readings.
12. Run `GET /homes/1/reports/custom?start_date=2026-06-30&end_date=2026-06-30` to generate a report for a custom date range.
13. Run `DELETE /homes/1/appliances/1` to deactivate an appliance while keeping its history.

## Assumptions / Non-Goals

- `Home` is the client context for v1.
- No authentication or authorization.
- No client/home creation API.
- Vendor integrations are mocked only.
- No per-appliance manual collection endpoint.
- Reports are computed from metric history; report rows are not persisted.
- UI is intentionally minimal and Swagger is the primary review surface.

## Key Design Choices

- File-based SQLite at `data/smarthome.db`.
- Idempotent backend seeding for two demo homes, demo appliances, and sample metric readings.
- Home-scoped APIs throughout for future multi-client extensibility.
- Manual collection remains available in Swagger for demos/tests.
- Scheduled collection runs for the default home on a simple APScheduler interval job.
- Report endpoints summarize the same stored readings used by metrics history.

## AI Usage Note

I used spec-driven AI development for this assignment. I clarified requirements first, captured decisions in the context docs, built the backend feature by feature, and validated each feature with tests and Swagger. AI assisted with planning, implementation, review, and verification, while the final scope and design decisions were reviewed during development.
