"""Pydantic request and response models for the SmartHome API."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    """Minimal health check payload used by the foundation endpoint."""

    status: str
    service: str


class HomeResponse(BaseModel):
    """Response shape for the seeded home/client context."""

    model_config = ConfigDict(from_attributes=True)

    home_id: int
    name: str
    created_at: datetime


class ApplianceCreateRequest(BaseModel):
    """Request body for registering an appliance under a home."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "display_name": "Living Room AC",
                    "vendor": "acme_home",
                    "appliance_type": "air_conditioner",
                    "vendor_device_id": "acme-ac-demo-1",
                    "collection_interval_seconds": 60,
                }
            ]
        }
    )

    display_name: str
    vendor: str
    appliance_type: str
    vendor_device_id: str
    collection_interval_seconds: int | None = None


class ApplianceResponse(BaseModel):
    """Response body for appliance list, detail, create, and delete calls."""

    model_config = ConfigDict(from_attributes=True)

    appliance_id: int
    home_id: int
    display_name: str
    vendor: str
    appliance_type: str
    vendor_device_id: str
    status: str
    collection_interval_seconds: int
    created_at: datetime
    deactivated_at: datetime | None


class VendorCapabilityResponse(BaseModel):
    """Public summary of a mock vendor's supported appliance types."""

    vendor: str
    supported_appliance_types: list[str]
    normalized_metrics: list[str]


class MetricReadingResponse(BaseModel):
    """Normalized metric reading exposed to clients and reports."""

    model_config = ConfigDict(from_attributes=True)

    metric_reading_id: int
    home_id: int
    appliance_id: int
    appliance_display_name: str
    vendor: str
    appliance_type: str
    power_watts: float | None
    temperature_celsius: float | None
    operational_state: str | None
    recorded_at: datetime
    raw_payload: dict


class CollectionRunResponse(BaseModel):
    """Summary returned by the manual home-level collection helper."""

    home_id: int
    collected_count: int
    skipped_count: int
    readings: list[MetricReadingResponse]


class MetricStats(BaseModel):
    """Aggregate values for a numeric metric within a report range."""

    avg: float | None
    min: float | None
    max: float | None


class ApplianceReportSummary(BaseModel):
    """Per-appliance report row with summary metrics and state counts."""

    appliance_id: int
    display_name: str
    vendor: str
    appliance_type: str
    readings_count: int
    power_watts: MetricStats
    temperature_celsius: MetricStats
    state_counts: dict[str, int]
    latest_reading_at: datetime | None


class ReportResponse(BaseModel):
    """Top-level report payload for daily and custom report endpoints."""

    report_type: str
    home_id: int
    start_date: date
    end_date: date
    generated_at: datetime
    total_appliances: int
    total_metric_readings: int
    appliances: list[ApplianceReportSummary]
