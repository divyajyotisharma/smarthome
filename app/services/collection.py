"""Metric collection service for manual home runs and scheduled appliance polling."""

from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Appliance, Home, MetricReading
from app.vendors.adapters import NormalizedReading, adapter_for


class CollectionServiceError(Exception):
    """Base exception for collection failures."""

    pass


class HomeNotFoundError(CollectionServiceError):
    """Raised when collection is requested for a missing home."""

    pass


def collect_for_home(session: Session, home_id: int) -> tuple[list[MetricReading], int]:
    """Collect one normalized reading for each active appliance in a home."""

    home = session.get(Home, home_id)
    if home is None:
        raise HomeNotFoundError("Home not found")

    appliances = list(
        session.scalars(
            select(Appliance)
            .where(Appliance.home_id == home_id)
            .order_by(Appliance.id)
        )
    )
    active_appliances = [appliance for appliance in appliances if appliance.status == "active"]
    skipped_count = len(appliances) - len(active_appliances)

    readings = [
        _to_metric_reading(adapter_for(appliance.vendor).collect(appliance))
        for appliance in active_appliances
    ]
    session.add_all(readings)
    session.commit()
    for reading in readings:
        session.refresh(reading)
    return readings, skipped_count


def collect_due_appliances(
    session: Session,
    now: datetime | None = None,
) -> tuple[list[MetricReading], int]:
    """Collect readings for active appliances whose own interval has elapsed."""

    effective_now = now or datetime.now(timezone.utc)
    appliances = list(
        session.scalars(
            select(Appliance)
            .where(Appliance.status == "active")
            .order_by(Appliance.home_id, Appliance.id)
        )
    )

    due_appliances = [
        appliance
        for appliance in appliances
        if _is_appliance_due(session, appliance, effective_now)
    ]

    readings = [
        _to_metric_reading(
            adapter_for(appliance.vendor).collect(appliance),
            recorded_at=effective_now,
        )
        for appliance in due_appliances
    ]
    session.add_all(readings)
    session.commit()
    for reading in readings:
        session.refresh(reading)
    return readings, 0


def _is_appliance_due(session: Session, appliance: Appliance, now: datetime) -> bool:
    """Check whether the appliance has no reading or its interval has elapsed."""

    latest_recorded_at = session.scalar(
        select(func.max(MetricReading.recorded_at))
        .where(MetricReading.appliance_id == appliance.id)
    )
    if latest_recorded_at is None:
        return True

    return _as_utc(now).timestamp() - _as_utc(latest_recorded_at).timestamp() >= appliance.collection_interval_seconds


def _as_utc(value: datetime) -> datetime:
    """Normalize SQLite-returned naive timestamps as UTC for interval math."""

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _to_metric_reading(
    reading: NormalizedReading,
    recorded_at: datetime | None = None,
) -> MetricReading:
    """Convert a normalized vendor payload into a persisted metric row."""

    return MetricReading(
        home_id=reading.home_id,
        appliance_id=reading.appliance_id,
        vendor=reading.vendor,
        appliance_type=reading.appliance_type,
        power_watts=reading.power_watts,
        temperature_celsius=reading.temperature_celsius,
        operational_state=reading.operational_state,
        recorded_at=recorded_at or reading.recorded_at,
        raw_payload=reading.raw_payload,
    )
