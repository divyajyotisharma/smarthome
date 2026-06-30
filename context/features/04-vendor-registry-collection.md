# 04 Vendor Registry Collection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development while implementing this plan. Keep implementation scoped to this feature and update this checklist as work is completed.

**Goal:** Add vendor capability listing and home-level manual metric collection for active appliances.

**Architecture:** This feature turns the static vendor registry into a reviewer-visible API and adds mocked vendor adapters that normalize different vendor payloads into stored `MetricReading` rows. It uses the existing `Home`, `Appliance`, and `MetricReading` models. It does not add scheduled collection, historical metrics listing, reports, or UI behavior.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, SQLAlchemy, SQLite, pytest, FastAPI TestClient.

## Global Constraints

- Keep collection home-scoped.
- Expose only home-level manual collection: `POST /homes/{home_id}/collect`.
- Do not add appliance-level collection APIs.
- Collect readings for active appliances only.
- Skip inactive appliances and include that count in the response.
- Use mocked vendor adapters only; do not call real vendor APIs.
- Normalize vendor-specific payloads into common metric fields.
- Preserve each raw vendor payload in `MetricReading.raw_payload`.
- Keep schemas under `app/schemas/`, routes under `app/routers/`, services under `app/services/`, and vendor logic under `app/vendors/`.
- Keep route handlers thin and put collection/vendor behavior in services and adapters.

---

## Logical App Structure

### Models

Use existing SQLAlchemy models in `app/models/core.py`.

- `Home`: scopes collection to one client/home context.
- `Appliance`: identifies active appliances and their vendor/type.
- `MetricReading`: stores normalized readings plus raw vendor payload.

No new persisted model is expected for this feature.

### Schemas

Extend `app/schemas/core.py` or create domain-specific schema modules under `app/schemas/` if the file starts becoming crowded.

Required schemas:

- `VendorCapabilityResponse`: response item for `GET /vendors`.
- `MetricReadingResponse`: response item for collected readings.
- `CollectionRunResponse`: response for `POST /homes/{home_id}/collect`.

Schema rules:

- Vendor capability responses include vendor, supported appliance types, and normalized metric fields.
- Metric reading responses include normalized values and raw payload.
- Collection response includes `home_id`, `collected_count`, `skipped_count`, and created readings.

### Routes

Create route modules as needed under `app/routers/`.

Routes:

- `GET /vendors`
- `POST /homes/{home_id}/collect`

Route rules:

- `GET /vendors` should be simple and deterministic.
- `POST /homes/{home_id}/collect` must verify the home exists.
- Return clear `404` when the home does not exist.
- Return a successful response even when no active appliances exist, with zero collected readings and skipped count reflecting inactive appliances.

### Services

Create `app/services/collection.py`.

Responsibilities:

- Fetch appliances for a home.
- Filter active appliances for collection.
- Skip inactive appliances.
- Select the correct vendor adapter for each active appliance.
- Store each normalized reading.
- Return collection counts and created readings.
- Keep the transaction boundary clear and commit once per home-level collection run.

### Vendor Registry and Adapters

Extend `app/vendors/`.

Responsibilities:

- Keep supported vendor/type definitions in the registry.
- Expose vendor capabilities for `GET /vendors`.
- Provide a common adapter interface/protocol for mocked vendors.
- Add one adapter for `acme_home`.
- Add one adapter for `zenith_iot`.
- Normalize vendor-specific payload fields into `power_watts`, `temperature_celsius`, `operational_state`, `recorded_at`, and `raw_payload`.

Required supported combinations:

- `acme_home` supports `air_conditioner`
- `acme_home` supports `refrigerator`
- `zenith_iot` supports `air_conditioner`
- `zenith_iot` supports `washer`

Normalization expectations:

- `acme_home` can return Celsius temperatures directly.
- `zenith_iot` can return Fahrenheit temperatures and must normalize to Celsius.
- Vendor states should normalize into consistent values such as `running`, `idle`, or `offline`.

### App Startup

Update `app/main.py`.

- Register vendors route.
- Register collection route.
- Keep existing health, home, and appliance routes working.
- Do not change startup seed behavior.

## API Contract

### `GET /vendors`

Purpose:

- Show supported mocked vendors and their appliance capabilities.
- Demonstrate overlapping appliance types across vendors.

Response:

- List of `VendorCapabilityResponse`.
- Each item includes `vendor`, `supported_appliance_types`, and `normalized_metrics`.

Validation:

- Response must include at least `acme_home` and `zenith_iot`.
- `air_conditioner` must appear under both vendors.

### `POST /homes/{home_id}/collect`

Purpose:

- Demo/test helper that collects one metric reading for each active appliance in a home.

Response:

- `home_id`
- `collected_count`
- `skipped_count`
- `readings`

Validation:

- Home must exist.
- Active appliances produce metric readings.
- Inactive appliances are skipped.
- Created readings are stored in the database.
- Raw payload is preserved on each reading.
- Normalized metric fields are returned consistently regardless of vendor.

## Tests

Use TDD during implementation.

### Vendor Capability Test

Test behavior:

- Call `GET /vendors`.
- Assert `200`.
- Assert at least two vendors are returned.
- Assert `acme_home` and `zenith_iot` are present.
- Assert both vendors support `air_conditioner`.
- Assert normalized metric fields are listed.

### Home-Level Collection Test

Test behavior:

- Build app with a temporary SQLite database.
- Start app through TestClient.
- Call `POST /homes/1/collect`.
- Assert `200`.
- Assert `collected_count` equals the number of active seeded appliances.
- Assert response includes created readings.
- Assert each reading has normalized metric fields and raw payload.

### Collection Persistence Test

Test behavior:

- Count readings for the seeded home before collection.
- Run `POST /homes/1/collect`.
- Count readings after collection.
- Assert the count increased by `collected_count`.

### Inactive Appliance Skip Test

Test behavior:

- Soft deactivate one appliance through the Feature 3 API.
- Run `POST /homes/1/collect`.
- Assert inactive appliance is skipped.
- Assert `skipped_count` is at least 1.
- Assert no collected reading is returned for the inactive appliance.

### Missing Home Test

Test behavior:

- Call `POST /homes/999/collect`.
- Assert `404`.
- Assert error message is clear.

### Regression Test

Run Feature 1, Feature 2, structure, and Feature 3 tests together with Feature 4 tests.

## Validation Commands

After implementation, run:

- `.venv/bin/python -m pytest tests/test_health.py tests/test_seed_startup.py tests/test_project_structure.py tests/test_appliances.py tests/test_collection.py -v`
- Run an OpenAPI smoke check that confirms `/vendors` and `/homes/{home_id}/collect` are present along with previous routes.

Live Swagger/API validation:

- Start the backend with `.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000`.
- Open `http://127.0.0.1:8000/docs`.
- Run `GET /vendors` and confirm both vendors and overlapping `air_conditioner` support.
- Run `POST /homes/1/collect` and confirm readings are created.
- Deactivate an appliance through `DELETE /homes/1/appliances/{appliance_id}`.
- Run `POST /homes/1/collect` again and confirm inactive appliance skipping.

## Implementation Checklist

- [x] Add vendor capability response schema.
- [x] Add metric reading response schema.
- [x] Add collection run response schema.
- [x] Extend vendor registry to expose capability data.
- [x] Add mocked vendor adapter interface/protocol.
- [x] Add `acme_home` mock adapter.
- [x] Add `zenith_iot` mock adapter.
- [x] Add collection service under `app/services/`.
- [x] Add vendor route under `app/routers/`.
- [x] Add collection route under `app/routers/`.
- [x] Register new routes in `app/main.py`.
- [x] Add vendor capability test.
- [x] Add home-level collection test.
- [x] Add collection persistence test.
- [x] Add inactive appliance skip test.
- [x] Add missing home test.
- [x] Run Feature 1 through Feature 4 tests.
- [x] Validate vendor and collection APIs through Swagger UI.
- [x] Update `context/progress-tracker.md`.

## Out of Scope

- Appliance-level collection endpoint.
- Scheduled/interval collection.
- APScheduler wiring.
- Historical metrics listing API.
- Report generation APIs.
- UI changes.
- Real vendor APIs.
- Dynamic vendor onboarding APIs.
- Vendor auth/rate-limit simulation beyond basic mock behavior.

## Self-Review

- Spec coverage: covers Feature 4 from `context/feature-design.md`, `context/architecture.md`, and `context/project-overview.md`.
- Scope check: keeps collection manual and home-level only.
- Structure check: follows logical app subsections under schemas, routers, services, and vendors.
- Code blocks: no actual implementation code is included in this plan.
