# Code Standards

## General

- Keep modules small and single-purpose.
- Prefer simple, explicit code over framework-heavy abstractions.
- Do not add vendor, auth, export, or distributed-job scope unless the design is updated first.
- Fix root causes instead of layering workarounds.
- Keep demo convenience behavior clearly documented as demo/test support.
- Do not overengineer implementations.
- Keep code changes iterative, minimal, logically correct and to the point.

## Python

- Use Python type hints for public functions and service boundaries.
- Keep functions focused and easy to test.
- Use timezone-aware UTC datetimes for stored metric timestamps.
- Avoid global mutable state except centralized configuration or adapter registries.

## FastAPI

- Use Pydantic minimally for request and response validation.
- Keep route handlers thin.
- Put business logic in services.
- Return consistent JSON response shapes.
- Use Swagger/OpenAPI descriptions where they clarify demo workflow.

## SQLAlchemy and SQLite

- Store local runtime data in `data/smarthome.db`.
- Create tables on startup if needed.
- Do not commit SQLite database files.
- Keep seed logic idempotent.
- Keep query logic readable; avoid premature repository abstractions.

## Vendor Adapters

- Each vendor adapter converts one vendor's mock payload into the normalized metric model.
- The supported-device registry defines valid `vendor + appliance_type` combinations.
- Preserve raw vendor payloads in metric readings for traceability.
- Do not let routes or report code depend on vendor-specific field names.

## API Routes

- Validate unknown external input at API boundaries.
- Register appliances only under a home.
- Reject unsupported vendors or unsupported appliance types with clear 400 responses.
- Use soft deactivation for appliance deletion.
- Provide home-scoped metrics and reports.
- Provide only home-level manual collection for demo/testing.

## Data and Storage

- `Home` groups appliances, metrics, and reports.
- `Appliance` stores registration details and collection interval.
- `MetricReading` stores normalized fixed columns plus raw vendor payload.
- Seed data is for reviewer convenience; the actual workflow must still work through APIs.

## File Organization

- `app/main.py` - app factory, route registration, startup/shutdown lifecycle.
- `app/config.py` - centralized runtime settings.
- `app/db.py` - SQLAlchemy engine/session/table helpers.
- `app/models/` - SQLAlchemy entities, split by domain as the model layer grows.
- `app/models/__init__.py` - stable public model exports.
- `app/schemas/` - Pydantic request/response schemas, split by API/domain area as the schema layer grows.
- `app/schemas/__init__.py` - stable public schema exports.
- `app/routers/` - API routes.
- `app/services/` - application logic.
- `app/vendors/` - vendor abstraction and mocks.
- `app/static/` - minimal UI.
- `tests/` - verification tests.
- `data/` - local runtime database files, ignored except `.gitkeep`.

## Structure Rules

- Add new SQLAlchemy entities under `app/models/`, not as flat root modules.
- Add new Pydantic schemas under `app/schemas/`, not as flat root modules.
- Re-export commonly used models and schemas from the package `__init__.py` files to keep imports stable.
- Keep routes grouped by resource under `app/routers/`.
- Keep business logic grouped by feature/service under `app/services/`.
- Add structure or import regression tests when moving modules.
