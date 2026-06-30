"""Home-level metric collection service for manual and scheduled runs."""

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


def _to_metric_reading(reading: NormalizedReading) -> MetricReading:
    """Convert a normalized vendor payload into a persisted metric row."""

    return MetricReading(
        home_id=reading.home_id,
        appliance_id=reading.appliance_id,
        vendor=reading.vendor,
        appliance_type=reading.appliance_type,
        power_watts=reading.power_watts,
        temperature_celsius=reading.temperature_celsius,
        operational_state=reading.operational_state,
        recorded_at=reading.recorded_at,
        raw_payload=reading.raw_payload,
    )
