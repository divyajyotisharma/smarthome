# 05 Historical Metrics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development while implementing this plan. Keep implementation scoped to this feature and update this checklist as work is completed.

**Goal:** Add a read-only, home-scoped metrics history API with optional filters for date range and appliance.

**Architecture:** This feature exposes metric readings already created by seed data and home-level collection. It uses the existing `MetricReading`, `Home`, and `Appliance` models, adds a thin metrics route, and keeps query/filter behavior in a metrics service. It does not add direct metric creation, reports, scheduled collection, exports, or UI behavior.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, SQLAlchemy, SQLite, pytest, FastAPI TestClient.

## Global Constraints

- Keep metrics APIs home-scoped.
- Treat `Home` as the client context for v1.
- Expose only read-only historical metric listing in this feature.
- Do not add direct metric creation APIs.
- Do not add appliance-level collection APIs.
- Do not add report generation in this feature.
- Preserve normalized metric fields and raw vendor payloads in responses.
- Reuse existing `MetricReadingResponse` unless implementation exposes a clear need for another schema.
- Keep route handlers thin and put metrics query behavior in services.
- Keep schemas under `app/schemas/`, routes under `app/routers/`, and services under `app/services/`.

---

## Logical App Structure

### Models

Use existing SQLAlchemy models in `app/models/core.py`.

- `Home`: validates that historical metrics are scoped to an existing home.
- `Appliance`: supports appliance filter validation within a home context.
- `MetricReading`: stores normalized metric fields plus `raw_payload`.

No new persisted model is expected for this feature.

### Schemas

Reuse `MetricReadingResponse` from `app/schemas/core.py`.

Schema rules:

- Responses include the normalized fields: `power_watts`, `temperature_celsius`, and `operational_state`.
- Responses include `raw_payload` so reviewer can compare original mock vendor payloads with normalized values.
- Responses include `vendor` and `appliance_type` so overlapping appliance types across vendors stay visible.

### Routes

Create `app/routers/metrics.py`.

Route:

- `GET /homes/{home_id}/metrics`

Route rules:

- Verify the home exists before querying metrics.
- Return clear `404` when the home does not exist.
- Accept optional `start_date`, `end_date`, and `appliance_id` query parameters.
- Return a list of `MetricReadingResponse`.
- Return an empty list when filters match no readings.
- Keep the endpoint read-only.

### Services

Create `app/services/metrics.py`.

Responsibilities:

- Verify the home exists.
- Query metric readings for a home.
- Apply optional appliance filter.
- Apply optional inclusive date range filter.
- Validate that `start_date` is not after `end_date`.
- Order readings deterministically, newest first.
- Keep the service focused on read behavior only.

Filter behavior:

- `start_date` means beginning of that date.
- `end_date` means end of that date.
- Date filtering is inclusive.
- If `appliance_id` is provided and does not belong to the requested home, return an empty list because it is being used as a filter.
- If the appliance exists but has no metrics in the selected range, return an empty list.

### App Startup

Update `app/main.py`.

- Register the metrics router.
- Keep existing health, home, appliance, vendor, and collection routes working.
- Do not change startup seed behavior.

## API Contract

### `GET /homes/{home_id}/metrics`

Purpose:

- Let the client view historical metric readings for appliances in their home.
- Let reviewers confirm seed readings and collection-created readings through Swagger.

Query parameters:

- `start_date`: optional date filter for readings recorded on or after the date.
- `end_date`: optional date filter for readings recorded on or before the date.
- `appliance_id`: optional appliance filter.

Response:

- List of `MetricReadingResponse`.

Validation:

- Home must exist.
- `start_date` and `end_date` can be provided independently.
- If both dates are provided, `start_date` must be earlier than or equal to `end_date`.
- Invalid date ranges return a clear `400`.
- The response must expose normalized fields consistently for all vendors.
- The response must preserve `raw_payload`.

## Tests

Use TDD during implementation.

### List Seeded Metrics Test

Test behavior:

- Build app with a temporary SQLite database.
- Start app through TestClient.
- Call `GET /homes/1/metrics`.
- Assert `200`.
- Assert seeded readings are returned.
- Assert response includes normalized fields and raw payload.

### Collection Then Metrics Test

Test behavior:

- Call `POST /homes/1/collect`.
- Call `GET /homes/1/metrics`.
- Assert the metrics list includes the newly collected readings.
- Assert readings from different vendors share the same normalized response shape.

### Appliance Filter Test

Test behavior:

- Pick a seeded appliance from `GET /homes/1/appliances`.
- Call `GET /homes/1/metrics` with that `appliance_id`.
- Assert `200`.
- Assert all returned readings belong to the requested appliance.

### Date Range Filter Test

Test behavior:

- Call `GET /homes/1/metrics` with a date range that includes seeded readings.
- Assert `200`.
- Assert returned readings fall within the inclusive date range.

### Invalid Date Range Test

Test behavior:

- Call `GET /homes/1/metrics` with `start_date` after `end_date`.
- Assert `400`.
- Assert the error message clearly identifies the invalid date range.

### Missing Home Test

Test behavior:

- Call `GET /homes/999/metrics`.
- Assert `404`.
- Assert error message is clear.

### Regression Test

Run Feature 1, Feature 2, structure, Feature 3, and Feature 4 tests together with Feature 5 tests.

## Validation Commands

After implementation, run:

- `.venv/bin/python -m pytest tests/test_health.py tests/test_seed_startup.py tests/test_project_structure.py tests/test_appliances.py tests/test_collection.py tests/test_metrics.py -v`
- Run an OpenAPI smoke check that confirms `/homes/{home_id}/metrics` is present along with previous routes.

Live Swagger/API validation:

- Start the backend with `.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000`.
- Open `http://127.0.0.1:8000/docs`.
- Run `POST /homes/1/collect`.
- Run `GET /homes/1/metrics` and confirm readings are returned.
- Run `GET /homes/1/metrics` with `appliance_id`.
- Run `GET /homes/1/metrics` with `start_date` and `end_date`.
- Confirm normalized fields and raw payload are visible in each response row.

## Implementation Checklist

- [x] Add metrics service for home-scoped reading queries.
- [x] Add metrics router with `GET /homes/{home_id}/metrics`.
- [x] Register metrics router in app startup.
- [x] Reuse `MetricReadingResponse` for API responses.
- [x] Add tests for seeded metrics listing.
- [x] Add tests for collection-created metrics visibility.
- [x] Add tests for appliance filtering.
- [x] Add tests for date range filtering.
- [x] Add tests for invalid date ranges.
- [x] Add tests for missing home behavior.
- [x] Run regression tests.
- [x] Run OpenAPI route smoke check.
- [x] Validate through live API checks.
- [ ] Validate through Swagger UI.

## Out of Scope

- Direct metric creation APIs.
- Appliance-level manual collection.
- Report generation.
- Scheduled/background collection.
- UI changes.
- Pagination, exports, or stored report records.

## Self-Review

- Spec coverage: Covers the Feature 5 API, query parameters, response schema, and validation path from `context/feature-design.md`.
- Scope control: Keeps this feature read-only and does not add reports or UI behavior.
- Extensibility: Keeps home-scoped API shape and separates route/service responsibilities for later report implementation.
