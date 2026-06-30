# Progress Tracker

Update this file after every meaningful implementation change.

## Current Phase

- Implementation in progress.

## Current Goal

- Prepare Feature 7: minimal demo UI.

## Completed

- Chose Python + FastAPI.
- Chose a backend-first modular monolith.
- Chose SQLite + SQLAlchemy for local persistence.
- Chose APScheduler for in-process scheduled metric collection.
- Chose minimal static UI plus Swagger UI.
- Chose two mock vendors with overlapping appliance types.
- Chose static supported-device registry validation.
- Chose home-scoped APIs for extensibility.
- Chose backend-owned idempotent seed data.
- Chose hybrid metric storage with normalized columns plus raw vendor payload.
- Added feature-wise API/schema design and Swagger validation paths.
- Chose concrete mock vendors: `acme_home` and `zenith_iot`.
- Replaced UI context placeholder with minimal static dashboard guidance.
- Completed Feature 1 foundation health endpoint.
- Completed Feature 2 startup database setup and idempotent seed data.
- Refactored app structure into logical `models`, `schemas`, `routers`, and `services` packages.
- Completed Feature 3 appliance management APIs.
- Completed Feature 4 vendor registry and home-level metric collection.
- Completed Feature 5 historical metrics API.
- Completed Feature 6 report APIs and startup daily report scheduler wiring.
- Completed default-home scheduled metric collection using an APScheduler interval job.
- Restored appliance read APIs to use separate list and detail routes: `GET /homes/{home_id}/appliances` and `GET /homes/{home_id}/appliances/{appliance_id}`.

## In Progress

- Preparing Feature 7 minimal demo UI planning.

## Next Up

- Begin Feature 7 minimal demo UI implementation plan.
- Keep UI read-only/consumer-focused except existing appliance registration and home-level collection actions.
- Verify UI through browser/manual workflow after API coverage remains green.

## Open Questions

- None currently.

## Architecture Decisions

- Use `data/smarthome.db` as the local SQLite database file.
- Ignore local DB files with `data/*.db` and `data/*.sqlite`.
- Keep `data/.gitkeep` if the folder should exist in the repo.
- Startup creates tables if needed.
- Startup seeds one default demo home/client context only if missing.
- Startup seeds 2-3 demo appliances only if missing.
- Startup seeds enough sample metric readings for immediate report generation only if missing.
- Startup seeding must not duplicate data after app restart.
- UI must not create seed data.
- Deleting `data/smarthome.db` and restarting the app is the reset path for a fresh demo.
- Seed data is only for reviewer convenience; the actual workflow must still support registration, home-level collection, historical metrics, and reports.
- Pydantic should be used in a minimal way for FastAPI request and response validation.
- Reports are generated from metric history on demand; report rows are not persisted for v1.
- Startup daily report job should use the same report service and run 1 minute after app startup for reviewer/demo visibility.
- Scheduled metric collection uses one home-level APScheduler interval job for `default_home_id` every `default_collection_interval_seconds`.
- `POST /homes/{home_id}/collect` remains as a manual Swagger/demo helper.
- Per-appliance scheduler jobs remain out of scope; appliance-level interval fields stay in the model for future extensibility.

## Session Notes

- The assignment is judged primarily on working backend code, so design should support a small but complete local workflow.
- Keep APIs centered on assignment requirements and avoid unnecessary appliance-level manual collection.
- Build feature by feature and verify each feature through Swagger UI before starting the next one.
- Feature 1 verification: `.venv/bin/python -m pytest tests/test_health.py -v` passed with 1 test and 1 deprecation warning from FastAPI/Starlette TestClient; OpenAPI smoke check for `/health` passed.
- Feature plans should stay high level: app subsections, responsibilities, API contracts, tests, validation commands, and scope boundaries without embedded implementation code.
- Feature 2 verification: `.venv/bin/python -m pytest tests/test_health.py tests/test_seed_startup.py -v` passed with 3 tests and 1 FastAPI/Starlette TestClient deprecation warning; OpenAPI smoke check for `/health` and `/homes/{home_id}` passed; live `GET /homes/1` returned the seeded `Demo Home`.
- Structure verification: `tests/test_project_structure.py` confirms core layer packages and existing OpenAPI routes remain available.
- Feature 3 verification: `.venv/bin/python -m pytest tests/test_health.py tests/test_seed_startup.py tests/test_project_structure.py tests/test_appliances.py -v` passed with 10 tests and 1 FastAPI/Starlette TestClient deprecation warning; OpenAPI smoke check for appliance routes passed; live API validation on port 8001 confirmed list, filtered list, create, unsupported create, and soft deactivate behavior.
- Feature 4 verification: `.venv/bin/python -m pytest tests/test_health.py tests/test_seed_startup.py tests/test_project_structure.py tests/test_appliances.py tests/test_collection.py -v` passed with 15 tests and 1 FastAPI/Starlette TestClient deprecation warning; OpenAPI smoke check for `/vendors` and `/homes/{home_id}/collect` passed; live API validation on port 8001 confirmed vendor capabilities, home-level collection, inactive skipping, and missing-home `404`.
- Feature 5 verification: `.venv/bin/python -m pytest tests/test_health.py tests/test_seed_startup.py tests/test_project_structure.py tests/test_appliances.py tests/test_collection.py tests/test_metrics.py -v` passed with 21 tests and 1 FastAPI/Starlette TestClient deprecation warning; OpenAPI structure test confirms `/homes/{home_id}/metrics`; metrics API tests confirm seeded metrics, collection-created metrics, appliance filtering, inclusive date filtering, invalid date range `400`, and missing-home `404`; live API checks on port 8001 confirmed unfiltered metrics, filtered metrics, and OpenAPI schema output.
- Feature 6 verification: `.venv/bin/python -m pytest tests/test_health.py tests/test_seed_startup.py tests/test_project_structure.py tests/test_appliances.py tests/test_collection.py tests/test_metrics.py tests/test_reports.py -v` passed with 28 tests and 1 FastAPI/Starlette TestClient deprecation warning; OpenAPI structure test confirms `/homes/{home_id}/reports/daily` and `/homes/{home_id}/reports/custom`; report tests confirm daily/custom summaries, empty ranges, invalid range `400`, missing-home `404`, and startup scheduler job registration; live API checks on port 8001 confirmed daily report, custom report, invalid range `400`, and OpenAPI schema output.
- Scheduled collection verification: TDD red phase confirmed the `default-home-collection` scheduler job was missing while manual `POST /homes/1/collect` still passed; final regression `.venv/bin/python -m pytest tests/test_health.py tests/test_seed_startup.py tests/test_project_structure.py tests/test_appliances.py tests/test_collection.py tests/test_metrics.py tests/test_reports.py -v` passed with 30 tests and 1 FastAPI/Starlette TestClient deprecation warning; live API validation on port 8001 showed `GET /homes/1/metrics` increasing from 16 to 22 after the configured 60-second interval without manual collection, then `POST /homes/1/collect` immediately added 3 more readings with IDs 23-25.
