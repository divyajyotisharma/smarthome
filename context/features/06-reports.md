# 06 Reports Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development while implementing this plan. Keep implementation scoped to this feature and update this checklist as work is completed.

**Goal:** Add home-scoped daily and custom date-range report APIs generated from historical metric readings.

**Architecture:** This feature computes report responses from existing `Appliance` and `MetricReading` rows. It adds report schemas, a reports service for aggregation, thin report routes, and a small APScheduler startup job that generates the default demo daily report 1 minute after app startup. It does not add report persistence, exports, authentication, UI behavior, or real vendor integrations.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, SQLAlchemy, SQLite, APScheduler, pytest, FastAPI TestClient.

## Global Constraints

- Keep report APIs home-scoped.
- Treat `Home` as the client context for v1.
- Generate reports from stored metric history.
- Do not add a report table for v1.
- Do not export reports to files.
- Do not add UI behavior in this feature.
- Do not add real vendor integrations.
- Reuse existing normalized metric columns for report calculations.
- Preserve route/service separation: routes handle HTTP concerns, services handle report aggregation.
- Keep schemas under `app/schemas/`, routes under `app/routers/`, services under `app/services/`, and scheduler wiring in `app/scheduler.py`.

---

## Logical App Structure

### Models

Use existing SQLAlchemy models in `app/models/core.py`.

- `Home`: validates that reports are scoped to an existing client/home context.
- `Appliance`: provides appliance identity and display metadata for report rows.
- `MetricReading`: provides historical normalized readings used for report aggregation.

No new persisted model is expected for this feature.

### Schemas

Extend `app/schemas/core.py` or create report-focused schema modules under `app/schemas/` if `core.py` becomes crowded.

Required schemas:

- `MetricStats`: metric aggregate values for one numeric metric.
- `ApplianceReportSummary`: per-appliance report row.
- `ReportResponse`: top-level report response.

Schema rules:

- `MetricStats` includes `avg`, `min`, and `max`.
- `MetricStats` values are nullable when a metric has no numeric readings in the selected range.
- `ApplianceReportSummary` includes appliance ID, display name, vendor, appliance type, reading count, power stats, temperature stats, state counts, and latest reading timestamp.
- `ReportResponse` includes report type, home ID, start date, end date, generated timestamp, total appliance count, total metric reading count, and appliance summaries.

### Routes

Create `app/routers/reports.py`.

Routes:

- `GET /homes/{home_id}/reports/daily`
- `GET /homes/{home_id}/reports/custom`

Route rules:

- Verify the home exists through the reports service.
- Return clear `404` when the home does not exist.
- Daily reports accept one required `date` query parameter.
- Custom reports accept required `start_date` and `end_date` query parameters.
- Invalid custom date ranges return clear `400`.
- Return `ReportResponse`.

### Services

Create `app/services/reports.py`.

Responsibilities:

- Verify the home exists.
- Query appliances for the home.
- Query metric readings within an inclusive date range.
- Group readings by appliance.
- Include appliances with zero readings so the report shows full home context.
- Calculate total appliance count.
- Calculate total metric reading count.
- Calculate per-appliance reading count.
- Calculate `avg`, `min`, and `max` for `power_watts`.
- Calculate `avg`, `min`, and `max` for `temperature_celsius`.
- Count operational states per appliance.
- Calculate latest reading timestamp per appliance.
- Return Pydantic-friendly report objects.

Date behavior:

- Daily report uses the same value for `start_date` and `end_date`.
- Custom report uses inclusive `start_date` and `end_date`.
- `start_date` means beginning of that date.
- `end_date` means end of that date.
- `start_date` must be earlier than or equal to `end_date`.

### Scheduler

Create `app/scheduler.py`.

Responsibilities:

- Own APScheduler startup/shutdown wiring.
- Schedule one startup daily report job 1 minute after app startup.
- Use `settings.default_home_id`.
- Use the seed metric date for the demo report when available, so a fresh database produces a meaningful startup report.
- Call the same reports service used by the API.
- Log or retain only a lightweight in-process reference to the generated report for observability.

Configuration:

- Add a centralized setting for startup report delay in seconds.
- Default startup report delay is `60`.
- Keep the delay customizable in one place for demos.

Implementation boundary:

- Do not store generated reports in SQLite.
- Do not expose scheduler internals through public API in this feature.
- Do not block application startup while waiting for the delayed report job.

### App Startup

Update `app/main.py`.

- Register reports router.
- Start the scheduler after tables are created and seed data exists.
- Shut the scheduler down during app shutdown.
- Keep existing health, home, appliance, vendor, collection, and metrics routes working.

## API Contract

### `GET /homes/{home_id}/reports/daily`

Purpose:

- Generate a report for one date using historical metrics.

Query parameters:

- `date`: required date.

Response:

- `ReportResponse` with `report_type` set to `daily`.
- `start_date` and `end_date` both match the requested date.

Validation:

- Home must exist.
- Report can return zero readings when no metrics exist for the requested date.
- Appliance summaries still include registered appliances for the home.

### `GET /homes/{home_id}/reports/custom`

Purpose:

- Generate a report for a custom inclusive date range.

Query parameters:

- `start_date`: required date.
- `end_date`: required date.

Response:

- `ReportResponse` with `report_type` set to `custom`.

Validation:

- Home must exist.
- `start_date` must be earlier than or equal to `end_date`.
- Invalid ranges return `400`.

## Report Calculation Rules

- `total_appliances` counts all appliances under the home, including inactive appliances, because historical reports should preserve past context.
- `total_metric_readings` counts readings in the selected date range.
- Per-appliance `readings_count` counts readings for that appliance in the selected date range.
- Numeric stats ignore `None` values.
- Numeric stats are `null` when all selected values for that metric are `None`.
- `state_counts` counts non-null `operational_state` values.
- `latest_reading_at` is `null` when the appliance has no readings in the range.

## Tests

Use TDD during implementation.

### Daily Report Test

Test behavior:

- Build app with a temporary SQLite database.
- Start app through TestClient.
- Call `GET /homes/1/reports/daily` with the seeded metric date.
- Assert `200`.
- Assert report type is `daily`.
- Assert total appliances equals seeded appliance count.
- Assert total metric readings equals seeded readings for that date.
- Assert appliance summaries include power stats, temperature stats, state counts, and latest reading timestamp.

### Custom Report Test

Test behavior:

- Call `GET /homes/1/reports/custom` with a range that includes seeded readings.
- Assert `200`.
- Assert report type is `custom`.
- Assert start and end dates match the request.
- Assert totals match available metric readings.

### Empty Range Report Test

Test behavior:

- Call daily or custom report for a date with no metric readings.
- Assert `200`.
- Assert total metric readings is `0`.
- Assert appliance summaries are still present with zero reading counts and nullable metric stats.

### Invalid Custom Range Test

Test behavior:

- Call `GET /homes/1/reports/custom` with `start_date` after `end_date`.
- Assert `400`.
- Assert the error message clearly identifies the invalid date range.

### Missing Home Test

Test behavior:

- Call both report endpoints for a missing home.
- Assert `404`.
- Assert error message is clear.

### Scheduler Wiring Test

Test behavior:

- Test scheduler setup without waiting 60 seconds.
- Assert the startup daily report job is registered with the configured delay.
- Assert the scheduled job calls the report service using the default home context.
- Assert scheduler shutdown is safe.

### Regression Test

Run Feature 1 through Feature 6 tests together.

## Validation Commands

After implementation, run:

- `.venv/bin/python -m pytest tests/test_health.py tests/test_seed_startup.py tests/test_project_structure.py tests/test_appliances.py tests/test_collection.py tests/test_metrics.py tests/test_reports.py -v`
- Run an OpenAPI smoke check that confirms `/homes/{home_id}/reports/daily` and `/homes/{home_id}/reports/custom` are present along with previous routes.

Live Swagger/API validation:

- Start the backend with `.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000`.
- Open `http://127.0.0.1:8000/docs`.
- Run `GET /homes/1/reports/daily?date=2026-06-30`.
- Run `GET /homes/1/reports/custom?start_date=2026-06-30&end_date=2026-06-30`.
- Run `GET /homes/1/reports/custom` with an invalid date range and confirm `400`.
- Confirm report tables in Swagger show totals and per-appliance summaries.
- Confirm startup logs show the delayed daily report job was scheduled.

## Implementation Checklist

- [x] Add APScheduler dependency if it is not already installed.
- [x] Add startup report delay setting with default `60`.
- [x] Add report response schemas.
- [x] Add reports service for aggregation.
- [x] Add reports router with daily and custom endpoints.
- [x] Register reports router in app startup.
- [x] Add scheduler setup and shutdown wiring.
- [x] Add startup daily report job.
- [x] Add daily report tests.
- [x] Add custom report tests.
- [x] Add empty range report tests.
- [x] Add invalid range tests.
- [x] Add missing home tests.
- [x] Add scheduler wiring tests.
- [x] Run regression tests.
- [x] Run OpenAPI route smoke check.
- [x] Validate through live API checks.
- [ ] Validate through Swagger UI.

## Out of Scope

- Persisting report rows.
- Exporting reports to files.
- UI report table rendering.
- Authentication or authorization.
- Real vendor APIs.
- Distributed scheduler or multi-process scheduler coordination.
- Report pagination.

## Self-Review

- Spec coverage: Covers daily reports, custom date-range reports, report response structure, startup daily report generation, and Swagger/API validation path.
- Scope control: Keeps reports computed from metric history and avoids adding storage that is not needed for the assignment.
- Extensibility: Keeps aggregation in a service and scheduler wiring isolated so later UI and production scheduler decisions can build on it.
