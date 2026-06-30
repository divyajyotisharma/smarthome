"""Report aggregation over stored metric history for one home."""

from collections import Counter
from datetime import date, datetime, time, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Appliance, Home, MetricReading
from app.models.core import utc_now
from app.schemas import ApplianceReportSummary, MetricStats, ReportResponse


class ReportsServiceError(Exception):
    """Base exception for report generation failures."""

    pass


class HomeNotFoundError(ReportsServiceError):
    """Raised when a report is requested for a missing home."""

    pass


class InvalidDateRangeError(ReportsServiceError):
    """Raised when the report date range is reversed."""

    pass


def generate_daily_report(session: Session, home_id: int, report_date: date) -> ReportResponse:
    """Generate a one-day report for the requested home."""

    return generate_report(
        session=session,
        home_id=home_id,
        start_date=report_date,
        end_date=report_date,
        report_type="daily",
    )


def generate_report(
    session: Session,
    home_id: int,
    start_date: date,
    end_date: date,
    report_type: str = "custom",
) -> ReportResponse:
    """Aggregate appliance-level report rows for an inclusive date range."""

    home = session.get(Home, home_id)
    if home is None:
        raise HomeNotFoundError("Home not found")
    if start_date > end_date:
        raise InvalidDateRangeError("start_date must be earlier than or equal to end_date")

    appliances = list(
        session.scalars(
            select(Appliance)
            .where(Appliance.home_id == home_id)
            .order_by(Appliance.id)
        )
    )
    readings = list(
        session.scalars(
            select(MetricReading)
            .where(MetricReading.home_id == home_id)
            .where(MetricReading.recorded_at >= _start_of_day(start_date))
            .where(MetricReading.recorded_at <= _end_of_day(end_date))
            .order_by(MetricReading.appliance_id, MetricReading.recorded_at)
        )
    )

    readings_by_appliance: dict[int, list[MetricReading]] = {}
    for reading in readings:
        readings_by_appliance.setdefault(reading.appliance_id, []).append(reading)

    return ReportResponse(
        report_type=report_type,
        home_id=home_id,
        start_date=start_date,
        end_date=end_date,
        generated_at=utc_now(),
        total_appliances=len(appliances),
        total_metric_readings=len(readings),
        appliances=[
            _summarize_appliance(appliance, readings_by_appliance.get(appliance.id, []))
            for appliance in appliances
        ],
    )


def _summarize_appliance(appliance: Appliance, readings: list[MetricReading]) -> ApplianceReportSummary:
    """Build one report row for a single appliance."""

    states = Counter(
        reading.operational_state
        for reading in readings
        if reading.operational_state is not None
    )
    latest_reading_at = max((reading.recorded_at for reading in readings), default=None)

    return ApplianceReportSummary(
        appliance_id=appliance.id,
        display_name=appliance.display_name,
        vendor=appliance.vendor,
        appliance_type=appliance.appliance_type,
        readings_count=len(readings),
        power_watts=_metric_stats([reading.power_watts for reading in readings]),
        temperature_celsius=_metric_stats([reading.temperature_celsius for reading in readings]),
        state_counts=dict(sorted(states.items())),
        latest_reading_at=latest_reading_at,
    )


def _metric_stats(values: list[float | None]) -> MetricStats:
    """Calculate aggregate statistics while ignoring missing values."""

    numeric_values = [value for value in values if value is not None]
    if not numeric_values:
        return MetricStats(avg=None, min=None, max=None)
    return MetricStats(
        avg=round(sum(numeric_values) / len(numeric_values), 2),
        min=min(numeric_values),
        max=max(numeric_values),
    )


def _start_of_day(value: date) -> datetime:
    """Convert a date to the start of its UTC day."""

    return datetime.combine(value, time.min, tzinfo=timezone.utc)


def _end_of_day(value: date) -> datetime:
    """Convert a date to the end of its UTC day."""

    return datetime.combine(value, time.max, tzinfo=timezone.utc)
