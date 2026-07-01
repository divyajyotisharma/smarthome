# Feature Design

Build SmartHome feature by feature. Each feature should be independently verifiable through Swagger UI before starting the next one.

## Feature 1: Project Foundation

### Purpose

Create the smallest runnable FastAPI backend with Swagger, health check, config, and database wiring.

### APIs

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Verify the service is running. |

### Response Schemas

`HealthResponse`

- `status: str`
- `service: str`

### Validation Path

1. Start the backend.
2. Open Swagger UI.
3. Run `GET /health`.
4. Confirm response is `200` with `status = "ok"`.

## Feature 2: Startup Database and Seed Data

### Purpose

Create local SQLite tables and seed reviewer-friendly demo data without duplicating records on restart.

### Behavior

- Use file-based SQLite at `data/smarthome.db`.
- Create tables on app startup.
- Seed one default demo home/client context if missing.
- Seed 2-3 appliances if missing.
- Seed enough historical metric readings for reports to work immediately.
- Do not seed from the UI.

### APIs

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/homes/{home_id}` | Verify the seeded/default home exists. |

### Response Schemas

`HomeResponse`

- `home_id: int`
- `name: str`
- `created_at: datetime`

### Validation Path

1. Delete `data/smarthome.db` for a fresh demo if needed.
2. Start the backend.
3. Run `GET /homes/{home_id}` using the documented default demo home ID.
4. Restart the backend.
5. Run the same API and confirm seed data is not duplicated.

## Feature 3: Appliance Management

### Purpose

Allow a client to view, register, and deactivate appliances under a home.

### APIs

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/homes/{home_id}/appliances` | List appliances for a home. |
| `POST` | `/homes/{home_id}/appliances` | Register a new appliance under a home. |
| `GET` | `/homes/{home_id}/appliances/{appliance_id}` | View one appliance. |
| `DELETE` | `/homes/{home_id}/appliances/{appliance_id}` | Soft deactivate one appliance. |

### Request Schemas

`ApplianceCreateRequest`

- `display_name: str`
- `vendor: str`
- `appliance_type: str`
- `vendor_device_id: str`
- `collection_interval_seconds: int | None`

### Response Schemas

`ApplianceResponse`

- `appliance_id: int`
- `home_id: int`
- `display_name: str`
- `vendor: str`
- `appliance_type: str`
- `vendor_device_id: str`
- `status: str`
- `collection_interval_seconds: int`
- `created_at: datetime`
- `deactivated_at: datetime | None`

### Validation Rules

- `vendor + appliance_type` must exist in the static supported-device registry.
- `collection_interval_seconds` defaults from config when omitted.
- `DELETE` sets status to inactive/decommissioned; it does not remove history.

### Validation Path

1. List seeded appliances.
2. Register a supported appliance.
3. Confirm it appears in the list.
4. Try registering an unsupported `vendor + appliance_type` and confirm a clear `400`.
5. Deactivate an appliance and confirm it remains visible with inactive status.

## Feature 4: Vendor Registry and Metric Collection

### Purpose

Demonstrate consistent collection across mocked vendors with different payload shapes and overlapping appliance types.

### APIs

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/vendors` | List supported vendors, appliance types, and normalized metric fields. |
| `POST` | `/homes/{home_id}/collect` | Demo/test helper that collects one reading for each active appliance in a home. |

### Response Schemas

`VendorCapabilityResponse`

- `vendor: str`
- `supported_appliance_types: list[str]`
- `normalized_metrics: list[str]`

`CollectionRunResponse`

- `home_id: int`
- `collected_count: int`
- `skipped_count: int`
- `readings: list[MetricReadingResponse]`

### Vendor Design

- Vendor adapters expose a common method that returns a normalized metric object.
- Mock vendors may return different raw payload field names.
- Vendors may support overlapping appliance types.
- Raw payload is stored on each metric reading for traceability.

### Mock Vendor Plan

Use these concrete vendors unless the design changes:

- `acme_home`: supports `air_conditioner` and `refrigerator`.
- `zenith_iot`: supports `air_conditioner` and `washer`.

`air_conditioner` intentionally overlaps across both vendors to demonstrate abstraction.

Example `acme_home` raw payload:

```json
{
  "device_id": "acme-ac-101",
  "power_watts": 820,
  "temp_celsius": 23.5,
  "status": "cooling"
}
```

Example `zenith_iot` raw payload:

```json
{
  "id": "zenith-ac-9",
  "energyUsageW": 790,
  "temperatureF": 74.3,
  "state": "RUNNING"
}
```

Both normalize into `power_watts`, `temperature_celsius`, `operational_state`, `recorded_at`, and `raw_payload`.

### Validation Path

1. Run `GET /vendors`.
2. Confirm at least two vendors exist and at least one appliance type overlaps.
3. Run `POST /homes/{home_id}/collect`.
4. Confirm readings are created for active appliances only.

## Feature 5: Historical Metrics

### Purpose

Expose stored metric history in a home-scoped, read-only way.

### APIs

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/homes/{home_id}/metrics` | List historical metrics for a home. |

### Query Parameters

- `start_date: date | None`
- `end_date: date | None`
- `appliance_id: int | None`

### Response Schemas

`MetricReadingResponse`

- `metric_reading_id: int`
- `home_id: int`
- `appliance_id: int`
- `vendor: str`
- `appliance_type: str`
- `power_watts: float | None`
- `temperature_celsius: float | None`
- `operational_state: str | None`
- `recorded_at: datetime`
- `raw_payload: dict`

### Validation Path

1. Run home-level collection.
2. Run `GET /homes/{home_id}/metrics`.
3. Filter by date and by appliance.
4. Confirm normalized fields exist regardless of vendor.

## Feature 6: Reports

### Purpose

Generate home-scoped reports from historical metric readings.

### APIs

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/homes/{home_id}/reports/daily` | Generate a report for one date. |
| `GET` | `/homes/{home_id}/reports/custom` | Generate a report for a custom date range. |

### Query Parameters

`/reports/daily`

- `date: date`

`/reports/custom`

- `start_date: date`
- `end_date: date`

### Response Schemas

`ReportResponse`

- `report_type: str`
- `home_id: int`
- `start_date: date`
- `end_date: date`
- `generated_at: datetime`
- `total_appliances: int`
- `total_metric_readings: int`
- `appliances: list[ApplianceReportSummary]`

`ApplianceReportSummary`

- `appliance_id: int`
- `display_name: str`
- `vendor: str`
- `appliance_type: str`
- `readings_count: int`
- `power_watts: MetricStats`
- `temperature_celsius: MetricStats`
- `state_counts: dict[str, int]`
- `latest_reading_at: datetime | None`

`MetricStats`

- `avg: float | None`
- `min: float | None`
- `max: float | None`

### Startup Daily Report

- Schedule a daily report generation job 1 minute after app startup.
- The job should use available seed data for the default demo home.
- Reports can be generated from metric history on demand; storing report rows is optional unless needed for implementation clarity.

### Validation Path

1. Confirm seed metrics exist.
2. Run `GET /homes/{home_id}/reports/daily?date=<seed-date>`.
3. Run `GET /homes/{home_id}/reports/custom?start_date=<start>&end_date=<end>`.
4. Confirm totals and per-appliance summaries match available metric readings.

## Feature 7: Minimal Demo UI

### Purpose

Provide a lightweight reviewer-friendly UI while keeping Swagger as the primary API testing surface.

### UI Scope

- Show default home context.
- Link to Swagger UI.
- Show appliance table.
- Register appliance form.
- Trigger home-level collection.
- Show historical metrics table.
- Show daily/custom report table.

### UI Rules

- UI consumes existing APIs only.
- UI must not create seed data.
- UI must not introduce behavior unavailable through APIs.
- UI should render standardized report JSON as tables, not raw JSON text.

### Validation Path

1. Start the backend.
2. Open the UI.
3. Confirm seeded appliances load.
4. Trigger collection.
5. Generate a report and confirm table output.

## Feature Build Rule

Do not start the next feature until the current feature can be validated through Swagger UI and the progress tracker has been updated.
