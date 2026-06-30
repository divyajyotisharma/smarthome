# Architecture Context

## Stack

| Layer | Technology | Role |
| --- | --- | --- |
| API | FastAPI | Backend APIs, Swagger docs, static UI serving |
| Validation | Pydantic | Minimal request and response validation |
| Database | SQLite | Local file-based persistence at `data/smarthome.db` |
| ORM | SQLAlchemy | Models, sessions, and database queries |
| Scheduler | APScheduler | In-process scheduled metric collection and startup daily report job |
| UI | Static HTML/CSS/JS | Minimal demo UI rendered by FastAPI |
| Tests | pytest | API/service verification |

## System Boundaries

- `app/main.py` - FastAPI app setup, router registration, startup/shutdown lifecycle.
- `app/config.py` - Centralized config, including database path, default demo home, and default collection interval.
- `app/db.py` - SQLAlchemy engine, session factory, and table initialization.
- `app/models/` - SQLAlchemy entity modules grouped by domain area.
- `app/models/__init__.py` - Public model exports used by services, routes, and tests.
- `app/models/core.py` - Core entities for homes, appliances, and metric readings.
- `app/schemas/` - Pydantic request and response schema modules grouped by API/domain area.
- `app/schemas/__init__.py` - Public schema exports used by routes and tests.
- `app/schemas/core.py` - Foundation and home response schemas.
- `app/routers/` - Thin API route handlers.
- `app/services/` - Business logic for appliances, collection, reports, and seeding.
- `app/vendors/` - Vendor adapter interface, supported-device registry, and mock vendor implementations.
- `app/scheduler.py` - APScheduler jobs for appliance polling and the startup daily report.
- `app/static/` - Minimal demo UI assets.
- `data/` - Local runtime SQLite files; DB files are not committed.

## Storage Model

- SQLite database file: `data/smarthome.db`.
- The app creates the `data/` folder and database file locally when it runs.
- Database files must not be committed. Ignore `data/*.db` and `data/*.sqlite`.
- Keep `data/.gitkeep` if the folder needs to exist in the repo.
- Tables are created on startup if needed.

## Core Entities

- `Home`: default demo client/home context used to group appliances, metrics, and reports.
- `Appliance`: registered appliance instance for a home.
- `MetricReading`: historical normalized metric record collected from a vendor adapter.
- `VendorAdapter`: code-level abstraction for vendor-specific mock payloads and normalization.

## API Surface

APIs are designed feature by feature and remain home-scoped for future multi-client support.

- Foundation: `GET /health`
- Homes: `GET /homes/{home_id}`
- Appliances: `GET /homes/{home_id}/appliances`, `POST /homes/{home_id}/appliances`, `GET /homes/{home_id}/appliances/{appliance_id}`, `DELETE /homes/{home_id}/appliances/{appliance_id}`
- Vendors: `GET /vendors`
- Collection: `POST /homes/{home_id}/collect`
- Metrics: `GET /homes/{home_id}/metrics`
- Reports: `GET /homes/{home_id}/reports/daily`, `GET /homes/{home_id}/reports/custom`

Detailed request/response schemas and validation paths live in `context/feature-design.md`.

## Startup Seeding

On app startup, backend seeding must run only if demo data is missing.

Startup should:

1. Create database tables if needed.
2. Create one default demo home/client context if missing.
3. Create 2-3 demo appliances if missing.
4. Create enough sample metric readings for reports to work immediately.
5. Avoid duplicating demo records on restart.

The UI must not create seed data. Swagger/API testing and the UI should use the same backend-seeded data.

Because SQLite is file-based, data stays after app restart. For a fresh demo, delete `data/smarthome.db` and restart the app.

## Metric Storage

Use a hybrid metric model:

- Fixed normalized columns for reporting, such as `power_watts`, `temperature_celsius`, `operational_state`, and `recorded_at`.
- `raw_payload` JSON for preserving vendor-specific source data.

This keeps reports queryable while retaining vendor traceability.

## Auth and Access Model

- No real authentication in v1.
- A seeded default home/client context is used for the local demo.
- APIs remain home-scoped for future extensibility, but the UI can default to the seeded home.

## Scheduler Model

- Use APScheduler inside the FastAPI process.
- Schedule active appliances using their `collection_interval_seconds`.
- The default interval is configurable in one place.
- Generate a daily report 1 minute after app startup using available seed data.
- Document that production multi-instance deployments would move scheduled work to a dedicated worker or distributed scheduler.

## Invariants

1. Routes stay thin: validate input, call services, return responses.
2. Services own business logic and database state changes.
3. Vendor-specific payload differences stay inside vendor adapters.
4. Clients can register only supported `vendor + appliance_type` combinations.
5. Startup seeding must be idempotent.
6. UI must consume backend APIs and must not create seed data.
7. Deactivated appliances keep historical metrics but are excluded from future scheduled collection.
8. Models and schemas stay in package submodules, with `__init__.py` exposing stable imports.
