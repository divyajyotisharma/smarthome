# 03 Appliance Management Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development while implementing this plan. Keep implementation scoped to this feature and update this checklist as work is completed.

**Goal:** Add home-scoped appliance management APIs for listing, registering, viewing, and soft deactivating appliances.

**Architecture:** This feature builds on the existing `Home` and `Appliance` models. It adds appliance request/response schemas, an appliance service for business rules, a static supported-device registry for registration validation, and home-scoped appliance routes. It does not add vendor metric collection, historical metrics APIs, reports, scheduler jobs, or UI behavior.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, SQLAlchemy, SQLite, pytest, FastAPI TestClient.

## Global Constraints

- Keep APIs home-scoped.
- Treat `Home` as the client context for v1.
- Do not add client/user auth.
- Do not add a client-facing home creation API.
- Register appliances only under an existing home.
- Treat registration as idempotent for the same `home_id + vendor + vendor_device_id`.
- Validate `vendor + appliance_type` against a static supported-device registry.
- Keep vendor interactions mocked/configured only; do not call real vendor APIs.
- Do not add appliance metadata update APIs.
- Use soft deactivation for appliance deletion.
- Keep route handlers thin and put appliance business rules in services.
- Keep schemas under `app/schemas/`, routes under `app/routers/`, services under `app/services/`, and vendor registry logic under `app/vendors/`.

---

## Logical App Structure

### Models

Use existing SQLAlchemy models in `app/models/core.py`.

- `Home`: validates that appliance operations are scoped to an existing home.
- `Appliance`: stores appliance registration details, status, collection interval, and deactivation timestamp.

No new persisted model is expected for this feature.

### Schemas

Extend `app/schemas/core.py` or create a domain-specific schema module under `app/schemas/` if the file starts becoming crowded.

Required schemas:

- `ApplianceCreateRequest`: request body for appliance registration.
- `ApplianceResponse`: response shape for list, create, detail, and delete responses.

Schema rules:

- `collection_interval_seconds` is optional in create requests.
- `collection_interval_seconds`, when provided, must be greater than zero.
- Responses include appliance metadata captured at registration.
- Responses include `status` and `deactivated_at` so soft deactivation is visible in Swagger.

### Routes

Create `app/routers/appliances.py`.

Routes:

- `GET /homes/{home_id}/appliances`
- `POST /homes/{home_id}/appliances`
- `GET /homes/{home_id}/appliances/{appliance_id}`
- `DELETE /homes/{home_id}/appliances/{appliance_id}`

Route rules:

- All routes must verify the home context.
- The detail route must ensure the appliance belongs to the requested home.
- Delete routes must ensure the appliance belongs to the requested home.
- Use clear `404` responses when the home or appliance does not exist.
- Use clear `400` responses for unsupported vendor/type combinations.

### Services

Create `app/services/appliances.py`.

Responsibilities:

- List appliances for a home.
- Fetch one appliance by ID within a home.
- Register an appliance under a home.
- Return the existing appliance when the same vendor device is registered again in the same home.
- Apply default collection interval when request omits it.
- Validate supported vendor/type combinations.
- Soft deactivate an appliance by setting inactive/decommissioned status and `deactivated_at`.
- Keep historical metric rows untouched when deactivating an appliance.
- Add one lifecycle metric reading when an active appliance is deactivated.

### Vendor Registry

Create `app/vendors/registry.py`.

Responsibilities:

- Define supported vendors and appliance types for registration validation.
- Support overlapping appliance types across vendors.
- Keep this as static in-code configuration for v1.

Required supported combinations:

- `acme_home` supports `air_conditioner`
- `acme_home` supports `refrigerator`
- `zenith_iot` supports `air_conditioner`
- `zenith_iot` supports `washer`

This preserves the design decision that vendor/device-type onboarding is out of scope for the assignment but modeled as a future production concern.

### App Startup

Update `app/main.py`.

- Register the appliances router.
- Keep existing health and home routes working.
- Do not change startup seed behavior except as needed to import the new router.

## API Contract

### `GET /homes/{home_id}/appliances`

Purpose:

- List appliances for a home.
- Let reviewers verify seeded appliances.

Response:

- List of `ApplianceResponse`.
- Include active and inactive appliances unless future requirements say otherwise.

### `GET /homes/{home_id}/appliances/{appliance_id}`

Purpose:

- View one appliance under a home.

Response:

- One `ApplianceResponse`.
- Return `404` when the appliance does not exist or does not belong to the home.

### `POST /homes/{home_id}/appliances`

Purpose:

- Register a new appliance under a home.

Request:

- `display_name`
- `vendor`
- `appliance_type`
- `vendor_device_id`
- `collection_interval_seconds` optional

Response:

- New appliance registration returns `201 Created` with `ApplianceResponse`.
- If the same `home_id + vendor + vendor_device_id` already exists, return `200 OK` with the existing `ApplianceResponse` without creating a duplicate row.

Validation:

- Home must exist.
- `vendor + appliance_type` must be supported.
- Idempotency key is `home_id + vendor + vendor_device_id`.
- Missing interval uses config default.
- Provided interval must be positive.
- Do not require vendor metadata beyond the requested fields.

### `DELETE /homes/{home_id}/appliances/{appliance_id}`

Purpose:

- Soft deactivate one appliance.

Response:

- Updated `ApplianceResponse`.

Validation:

- Home must exist.
- Appliance must exist and belong to that home.
- Historical metric readings are preserved.
- A deactivation metric reading is added once when an active appliance becomes inactive.
- The deactivation metric uses `operational_state = "deactivated"` and carries the latest known power and temperature values when available.
- Repeating delete on an already inactive appliance should stay safe and return the inactive appliance.

## Tests

Use TDD during implementation.

### List Seeded Appliances Test

Test behavior:

- Build app with a temporary SQLite database.
- Start app through TestClient.
- Call `GET /homes/1/appliances` and `GET /homes/1/appliances/1`.
- Assert `200`.
- Assert seeded appliances are returned.
- Assert the detail call returns the matching appliance.
- Assert response includes appliance registration fields and status.

### Register Appliance Test

Test behavior:

- Register a supported appliance under home `1`.
- Omit `collection_interval_seconds`.
- Assert `201`.
- Assert response uses config default interval.
- Call list endpoint and confirm the new appliance appears.

### Idempotent Register Appliance Test

Test behavior:

- Register a supported appliance under home `1`.
- Register again with the same `vendor_device_id` for the same vendor and home.
- Assert the second response returns the original appliance ID.
- Assert only one appliance row exists for that vendor device in the home.

### Unsupported Vendor/Type Test

Test behavior:

- Attempt to register an unsupported `vendor + appliance_type` combination.
- Assert `400`.
- Assert response message clearly identifies unsupported vendor/type.

### Request Validation Tests

Test behavior:

- Missing required registration fields return FastAPI validation errors.
- Non-positive `collection_interval_seconds` values are rejected.
- Missing homes and cross-home appliance access return `404`.

### Soft Deactivate Test

Test behavior:

- Delete an existing appliance.
- Assert `200`.
- Assert status is inactive/decommissioned.
- Assert `deactivated_at` is populated.
- Fetch the same appliance through `GET /homes/1/appliances/1` and confirm it remains visible with inactive status.
- Fetch metrics for the appliance and confirm one new `deactivated` lifecycle reading was added.
- Repeat delete and confirm another deactivation lifecycle reading is not added.

### Regression Test

Run Feature 1 and Feature 2 tests together with Feature 3 tests.

## Validation Commands

After implementation, run:

- `.venv/bin/python -m pytest tests/test_health.py tests/test_seed_startup.py tests/test_project_structure.py tests/test_appliances.py -v`
- Run an OpenAPI smoke check that confirms `/health`, `/homes/{home_id}`, and all appliance routes are present.

Live Swagger/API validation:

- Start the backend with `.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000`.
- Open `http://127.0.0.1:8000/docs`.
- Run `GET /homes/1/appliances` and confirm seeded appliances load.
- Run `GET /homes/1/appliances/1` and confirm the detail endpoint returns one appliance.
- Run `POST /homes/1/appliances` with a supported vendor/type.
- Run `POST /homes/1/appliances` with an unsupported vendor/type and confirm `400`.
- Run `DELETE /homes/1/appliances/{appliance_id}` and confirm soft deactivation.

## Implementation Checklist

- [x] Add static supported-device registry under `app/vendors/`.
- [x] Add appliance request/response schemas under `app/schemas/`.
- [x] Add appliance service under `app/services/`.
- [x] Add appliances router under `app/routers/`.
- [x] Register appliances router in `app/main.py`.
- [x] Add list seeded appliances test.
- [x] Add register supported appliance test.
- [x] Add idempotent register appliance test.
- [x] Add registration request validation tests.
- [x] Add unsupported vendor/type validation test.
- [x] Add appliance list filter test.
- [x] Add soft deactivate test.
- [x] Add deactivation lifecycle metric test.
- [x] Run Feature 1, Feature 2, structure, and Feature 3 tests.
- [x] Validate appliance APIs through Swagger UI.
- [x] Update `context/progress-tracker.md`.

## Out of Scope

- Creating homes through client-facing APIs.
- Multiple homes per client.
- Appliance metadata update APIs.
- Real vendor APIs.
- Dynamic vendor onboarding APIs.
- Metric collection APIs.
- Metrics history APIs.
- Report APIs.
- Scheduler jobs.
- UI changes.

## Self-Review

- Spec coverage: covers Feature 3 from `context/feature-design.md`, `context/architecture.md`, and `context/project-overview.md`.
- Scope check: keeps appliance management separate from metric collection and reporting.
- Structure check: follows logical app subsections under models, schemas, routers, services, and vendors.
- Code blocks: no actual implementation code is included in this plan.
