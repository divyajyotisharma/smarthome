# Reviewer Test Scenarios

Use this as a quick review map for the SmartHome assignment. Swagger UI remains the primary manual review surface.

Swagger URL: `http://127.0.0.1:8000/docs`

## 1. Service Starts And Seeds Demo Data

What we are proving:

- The backend starts locally and exposes documented APIs.
- Startup prepares reviewer-friendly demo data before the workflow begins.
- Seed data exists only so reviewers can immediately test metrics and reports.

What is seeded:

- Two home/client contexts:
  - `Demo Home` as home `1`
  - `Weekend Home` as home `2`
- Demo appliances across supported vendors.
- Historical metric readings across known dates so metrics and reports work immediately.

How seeding works:

- Tables are created on app startup if needed.
- Seed records are inserted only when missing.
- Restarting the app does not duplicate homes, appliances, or readings.
- To restart with a fresh demo, delete `data/smarthome.db` and start the app again.

Try:

- `GET /health`
- `GET /homes/1`
- `GET /homes/1/appliances`
- `GET /homes/1/metrics`

Expected:

- `200 OK`
- `{"status": "ok", "service": "smarthome"}`
- Home `1` exists.
- Seeded appliances exist.
- Historical metrics exist immediately.

What can go wrong:

- App cannot start, dependencies are missing, or route registration failed.
- Startup seeding duplicates rows or reports have no data.

Guardrail:

- Health endpoint test and OpenAPI route tests verify the API shell.
- Seed service is idempotent.
- Tests verify seeded homes, appliances, and readings are not duplicated.

## 2. Supported Vendors Are Explicit

What we are proving:

- The backend exposes a consistent abstraction over mocked vendor differences.

Try:

- `GET /vendors`

Expected:

- `acme_home` and `zenith_iot` are returned.
- `air_conditioner` appears under both vendors.
- Normalized metric fields are listed.

What can go wrong:

- Vendor-specific differences leak into client API design.

Guardrail:

- Static registry defines supported vendor/type combinations.
- Vendor adapters normalize payloads into common metric columns.

## 3. Register Appliance

What we are proving:

- A client can register a supported appliance under a home.

Try:

- `POST /homes/1/appliances`

Sample body:

```json
{
  "display_name": "Bedroom AC",
  "vendor": "zenith_iot",
  "appliance_type": "air_conditioner",
  "vendor_device_id": "zenith-ac-review-001",
  "collection_interval_seconds": 60
}
```

Expected:

- New appliance returns `201 Created`.
- Response includes `appliance_id`, `home_id`, `status`, and timestamps.

What can go wrong:

- Unsupported appliance types are registered.
- Invalid intervals break scheduled collection.
- Duplicate registrations create duplicate rows.

Guardrail:

- Unsupported vendor/type returns `400`.
- Missing fields and non-positive intervals return `422`.
- Duplicate registration for the same `home_id + vendor + vendor_device_id` returns `200 OK` with the existing appliance.

## 4. Collect Metrics

What we are proving:

- The backend can collect metrics for active appliances using mocked vendors.

Try:

- `POST /homes/1/collect`
- `GET /homes/1/metrics`

Expected:

- Collection response shows `collected_count` and `skipped_count`.
- Metrics history includes new readings.
- Readings use normalized fields: `power_watts`, `temperature_celsius`, `operational_state`.

What can go wrong:

- Inactive appliances keep producing metrics.
- Vendor raw payload shape leaks into report logic.

Guardrail:

- Collection skips inactive appliances.
- Raw payload is preserved for traceability, but normalized columns drive metrics and reports.

## 5. Deactivate Appliance

What we are proving:

- Clients can stop managing an appliance without losing history.

Try:

- `DELETE /homes/1/appliances/1`
- `GET /homes/1/appliances/1`
- `GET /homes/1/metrics?appliance_id=1`

Expected:

- Appliance status becomes `inactive`.
- Appliance remains visible.
- Historical metrics remain visible.
- A latest lifecycle metric appears with `operational_state = "deactivated"`.

What can go wrong:

- Deactivation deletes history.
- Repeated deactivation creates duplicate lifecycle events.
- Inactive appliances still collect new vendor readings.

Guardrail:

- Soft deactivation updates status only.
- One deactivation metric is written only on the active-to-inactive transition.
- Collection tests verify inactive appliances are skipped.

## 6. View Historical Metrics

What we are proving:

- Clients can inspect stored appliance readings with useful filters.

Try:

- `GET /homes/1/metrics`
- `GET /homes/1/metrics?appliance_id=1`
- `GET /homes/1/metrics?start_date=2026-06-29&end_date=2026-06-30`

Expected:

- Metrics are returned newest first.
- Appliance and date filters narrow results.
- Invalid date ranges return `400`.

What can go wrong:

- Metrics from another home leak into a client's response.
- Date filters behave inconsistently.

Guardrail:

- All metrics APIs are home-scoped.
- Date range filtering is inclusive and validated.

## 7. Generate Reports

What we are proving:

- Reports are generated from the same stored metric history.

Try:

- `GET /homes/1/reports/daily?date=2026-06-30`
- `GET /homes/1/reports/custom?start_date=2026-06-29&end_date=2026-06-30`

Expected:

- Reports include total appliance count, total metric readings, per-appliance summaries, numeric stats, state counts, and latest reading timestamp.

What can go wrong:

- Reports use separate stale data.
- Empty ranges fail instead of returning an empty summary.
- Invalid ranges produce confusing results.

Guardrail:

- Reports are computed on demand from `MetricReading`.
- Empty ranges return appliance summaries with zero readings.
- Invalid ranges return `400`.

## 8. Scheduled Collection

What we are proving:

- The app can collect metrics automatically on configurable intervals.

Try:

- Start the app.
- Wait for the configured interval.
- Run `GET /homes/1/metrics`.

Expected:

- Metrics increase without manually calling `POST /homes/1/collect`.

What can go wrong:

- One slow appliance controls all scheduling.
- New appliances are ignored until restart.

Guardrail:

- Scheduler runs a lightweight tick.
- Due appliances are selected by each appliance's own interval.
- New due appliances are picked up without per-appliance scheduler jobs.

## 9. Error Cases To Check

| Case | API | Expected |
| --- | --- | --- |
| Missing home | `GET /homes/999` | `404 Home not found` |
| Missing appliance | `GET /homes/1/appliances/999` | `404 Appliance not found` |
| Wrong-home appliance | `GET /homes/2/appliances/1` | `404 Appliance not found` |
| Unsupported vendor/type | `POST /homes/1/appliances` | `400` with clear vendor/type message |
| Missing required field | `POST /homes/1/appliances` | `422` validation error |
| Non-positive interval | `POST /homes/1/appliances` | `422` validation error |
| Invalid metrics range | `GET /homes/1/metrics?start_date=2026-07-01&end_date=2026-06-30` | `400` |
| Invalid report range | `GET /homes/1/reports/custom?start_date=2026-07-01&end_date=2026-06-30` | `400` |

## Review Signal

The assignment asks for a focused local backend that demonstrates registration, management, metric collection, history, and reports. These scenarios cover the main workflow and the edge cases that protect data correctness.
