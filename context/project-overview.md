# SmartHome

## Overview

SmartHome is a backend-first FastAPI application for managing connected home appliances in a client/home context. Appliances can come from different mocked vendors, but the backend exposes consistent APIs for registration, metric collection, historical data, and reports.

## Goals

1. Provide a complete local demo of appliance registration, metric collection, historical storage, and reporting.
2. Demonstrate a simple vendor abstraction over different mock vendor payloads and overlapping appliance types.
3. Keep the implementation focused, reviewable, and easy to run locally without external infrastructure.

## Core User Flow

1. Client opens the app and views appliances for the default seeded demo home/client context.
2. Client registers a new appliance under that home.
3. Backend validates the requested vendor and appliance type against a static supported-device registry.
4. Backend collects metrics from mocked vendor adapters on configurable intervals.
5. Client can trigger home-level appliance collection for demo/testing.
6. Backend generates a daily report 1 minute after app startup from available seed data.
7. Client views historical metrics.
8. Client generates daily or custom date-range reports.

## Features

### Homes and Appliances

- Seed one default demo home/client context on startup if missing.
- Register appliances under a home.
- List and view appliances for a home.
- Soft deactivate appliances while preserving historical metrics.
- Display appliance metadata captured at registration; do not provide a separate metadata update API.

### Vendor Abstraction

- Support two mocked vendors in v1.
- Allow vendors to support overlapping appliance types.
- Validate `vendor + appliance_type` against a static supported-device registry.
- Normalize different vendor payloads into one internal metric shape.

### Metric Collection

- Use scheduled collection for active appliances.
- Use a configurable default collection interval defined in one config location.
- Allow per-appliance interval override at registration.
- Provide a home-level manual collection endpoint for demos/tests.

### Historical Metrics and Reports

- Store historical metric readings in SQLite.
- Expose read-only home-scoped historical metrics.
- Generate home-scoped daily reports.
- Generate home-scoped custom date-range reports.
- Return reports as standardized JSON that the UI can render as tables.

### Demo UI

- Use Swagger UI as the primary API documentation and testing surface.
- Provide a minimal static UI for viewing appliances, triggering collection, viewing metrics, and displaying report tables.
- The UI must not create seed data; seeding belongs to backend startup.

## Scope

### In Scope

- FastAPI backend.
- File-based SQLite database at `data/smarthome.db`.
- Backend startup seeding only when demo data is missing.
- SQLAlchemy persistence.
- Minimal Pydantic request/response validation.
- APScheduler in-process scheduled jobs.
- Mock vendor integrations.
- Minimal static UI.
- Tests or verification path for core workflow.

### Out of Scope

- Real authentication or user management.
- Real vendor APIs.
- Dynamic vendor onboarding or device schema registration APIs.
- Client-facing home creation UI.
- Appliance metadata update APIs.
- CSV/PDF report export.
- Distributed workers or production scheduler coordination.

## Success Criteria

1. Reviewer can run the backend locally and see demo data without manual setup.
2. Startup creates tables and seeds demo home, appliances, and enough metric readings only if missing.
3. Reviewer can register an appliance, trigger home-level collection, view metrics, and generate reports through Swagger/API.
4. Minimal UI can display appliances and report results in tables.
5. Restarting the app preserves SQLite data; deleting `data/smarthome.db` resets the demo.

## Build Approach

Build the app as vertical features. Each feature must have APIs, schemas, service behavior, and a Swagger UI validation path before moving to the next feature. The feature-by-feature design lives in `context/feature-design.md`.
