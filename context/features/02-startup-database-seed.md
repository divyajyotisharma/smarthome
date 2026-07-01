# 02 Startup Database Seed Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development while implementing this plan. Keep implementation scoped to this feature and update this checklist as work is completed.

**Goal:** Add SQLite persistence, create tables on startup, seed deterministic demo data only when missing, and expose the seeded default home through `GET /homes/{home_id}`.

**Architecture:** This feature introduces the persistence foundation used by later features. It adds database configuration, SQLAlchemy entities, an idempotent seed service, and a thin home route. It does not add appliance registration, vendor collection, metrics listing, reports, scheduler jobs, or UI behavior.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, SQLAlchemy, SQLite, pytest, FastAPI TestClient.

## Global Constraints

- Use the file-based SQLite database at `data/smarthome.db` for local runtime.
- Create the `data/` directory and DB file locally when the app runs.
- Create tables on app startup.
- Seed demo data only if missing.
- Do not duplicate homes, appliances, or metric readings after restart.
- UI must not seed data.
- Keep APIs home-scoped for future extensibility.
- Treat `Home` as the client context for v1. Multiple homes per client remain out of scope.
- Use Pydantic minimally for request and response validation.
- Keep route handlers thin and put database/seed behavior in services.

---

## Logical App Structure

### Models

Create SQLAlchemy models in `app/models/core.py` and export them from `app/models/__init__.py`.

- `Home`: represents the client/home context for grouping appliances, metrics, and reports.
- `Appliance`: represents one registered appliance instance that belongs to a home.
- `MetricReading`: represents one historical normalized metric reading for an appliance.

Add concise comments/docstrings near each entity explaining its role in the domain. Keep comments descriptive, not noisy.

### Schemas

Extend `app/schemas/core.py` and export public schemas from `app/schemas/__init__.py`.

- Keep `HealthResponse`.
- Add `HomeResponse` for `GET /homes/{home_id}`.
- Use Pydantic `from_attributes` support so SQLAlchemy model instances can be returned cleanly.

### Routes

Create `app/routers/homes.py`.

- Add `GET /homes/{home_id}`.
- Return `HomeResponse`.
- Return `404` with a clear message when a home does not exist.
- Keep route logic limited to request handling and calling the database/session dependency.

### Services

Create `app/services/seed.py`.

- Own all demo seed behavior.
- Seed the default home only if missing.
- Seed demo appliances only if missing for the default home.
- Seed sample metric readings only if missing for the default home.
- Commit the transaction once the seed operation is complete.
- Keep seed data deterministic so Swagger examples and tests are predictable.

### Database

Create `app/db.py`.

- Own SQLAlchemy engine creation.
- Own session factory creation.
- Own table creation.
- Ensure parent directory for `data/smarthome.db` exists.
- Provide a request-scoped session dependency for routes.

### Config

Create `app/config.py`.

- Centralize `database_url`.
- Centralize `default_home_id`.
- Centralize `default_home_name`.
- Centralize `default_collection_interval_seconds`.

### App Startup

Update `app/main.py`.

- Keep `GET /health` working.
- Add an app factory so tests can inject a temporary SQLite database.
- Register the homes router.
- On startup, create tables and run idempotent seed data.

## Data Model

### Home

Fields:

- `id`
- `name`
- `created_at`

Purpose comment to include in code: `Home groups the appliances and readings for one client/home context in the demo.`

### Appliance

Fields:

- `id`
- `home_id`
- `display_name`
- `vendor`
- `appliance_type`
- `vendor_device_id`
- `status`
- `collection_interval_seconds`
- `created_at`
- `deactivated_at`

Purpose comment to include in code: `Appliance is a registered device instance under a home; vendor-specific behavior remains outside this model.`

### MetricReading

Fields:

- `id`
- `home_id`
- `appliance_id`
- `vendor`
- `appliance_type`
- `power_watts`
- `temperature_celsius`
- `operational_state`
- `recorded_at`
- `raw_payload`

Purpose comment to include in code: `MetricReading stores normalized metric columns for reporting plus the raw vendor payload for traceability.`

## Seed Data

Use deterministic seed data:

- Default home: `id = 1`, `name = "Demo Home"`
- Appliance 1: `Living Room AC`, `acme_home`, `air_conditioner`, `acme-ac-101`
- Appliance 2: `Kitchen Refrigerator`, `acme_home`, `refrigerator`, `acme-fridge-202`
- Appliance 3: `Laundry Washer`, `zenith_iot`, `washer`, `zenith-washer-303`

Seed metric readings:

- At least 2 metric readings per appliance.
- Fixed timestamps on `2026-06-30`.
- Include values for normalized fields where meaningful.
- Include `raw_payload` with enough source detail to show traceability.

## API Contract

### `GET /homes/{home_id}`

Purpose:

- Verify the seeded/default home exists.
- Provide a simple Swagger validation point for startup database and seed behavior.

Response:

- `id`
- `name`
- `created_at`

Errors:

- `404` when the home ID does not exist.

## Tests

Use TDD during implementation.

### Seed Idempotency Test

Test behavior:

- Use a temporary SQLite database path.
- Create tables.
- Run the seed service twice.
- Assert exactly one home exists.
- Assert the default home ID is `1`.
- Assert the default home name is `Demo Home`.
- Assert exactly 3 seeded appliances exist.
- Assert exactly 6 seeded metric readings exist.

### Startup API Test

Test behavior:

- Build the FastAPI app with a temporary SQLite database path.
- Start the app through TestClient.
- Call `GET /homes/1`.
- Assert `200`.
- Assert the response includes `home_id = 1`, `name = "Demo Home"`, and `created_at`.

### Regression Test

Run Feature 1 health tests together with Feature 2 tests.

## Validation Commands

After implementation, run:

- `.venv/bin/python -m pytest tests/test_health.py tests/test_seed_startup.py -v`
- Run an OpenAPI smoke check that confirms `/health` and `/homes/{home_id}` are present.

Live Swagger/API validation:

- Start the backend with `.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000`.
- Open `http://127.0.0.1:8000/docs`.
- Run `GET /homes/1`.
- Confirm the response shows the seeded default home.
- Restart the backend and confirm `GET /homes/1` still works without duplicated seed data.

## Implementation Checklist

- [x] Update dependency list with SQLAlchemy.
- [x] Add app config.
- [x] Add SQLAlchemy database setup.
- [x] Add SQLAlchemy models with concise entity comments under `app/models/`.
- [x] Add `HomeResponse` schema under `app/schemas/`.
- [x] Add idempotent seed service.
- [x] Add homes router.
- [x] Wire table creation and seed service into app startup.
- [x] Add seed idempotency test.
- [x] Add startup API test.
- [x] Run Feature 1 and Feature 2 tests.
- [x] Validate `/homes/1` through Swagger UI.
- [x] Update `context/progress-tracker.md`.

## Out of Scope

- Creating homes through client-facing APIs.
- Multiple homes per client.
- Appliance registration APIs.
- Appliance list/detail/deactivate APIs.
- Vendor registry APIs.
- Collection APIs.
- Metrics APIs.
- Report APIs.
- Scheduler jobs.
- UI changes.

## Self-Review

- Spec coverage: covers Feature 2 from `context/feature-design.md`, `context/architecture.md`, and `context/project-overview.md`.
- Scope check: keeps client-as-home grouping for v1 and leaves multi-home client schema changes out of scope.
- Code blocks: no actual implementation code is included in this plan.
