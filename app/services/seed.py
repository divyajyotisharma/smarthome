"""Idempotent demo seeding used to boot the SmartHome assignment quickly."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Appliance, Home, MetricReading


SEED_RECORDED_AT = (
    datetime(2026, 6, 30, 9, 0, tzinfo=timezone.utc),
    datetime(2026, 6, 30, 9, 15, tzinfo=timezone.utc),
)


def seed_demo_data(session: Session, settings: Settings) -> None:
    """Create the default home, appliances, and sample readings when missing."""

    home = session.get(Home, settings.default_home_id)
    if home is None:
        home = Home(id=settings.default_home_id, name=settings.default_home_name)
        session.add(home)
        session.flush()

    if not session.scalars(select(Appliance).where(Appliance.home_id == home.id)).first():
        session.add_all(_demo_appliances(home.id, settings.default_collection_interval_seconds))
        session.flush()

    if not session.scalars(select(MetricReading).where(MetricReading.home_id == home.id)).first():
        appliances = session.scalars(select(Appliance).where(Appliance.home_id == home.id)).all()
        session.add_all(
            reading
            for appliance in appliances
            for reading in _demo_readings_for_appliance(home.id, appliance)
        )

    session.commit()


def _demo_appliances(home_id: int, collection_interval_seconds: int) -> list[Appliance]:
    """Return the fixed appliance set used for the seeded demo home."""

    return [
        Appliance(
            id=1,
            home_id=home_id,
            display_name="Living Room AC",
            vendor="acme_home",
            appliance_type="air_conditioner",
            vendor_device_id="acme-ac-101",
            collection_interval_seconds=collection_interval_seconds,
        ),
        Appliance(
            id=2,
            home_id=home_id,
            display_name="Kitchen Refrigerator",
            vendor="acme_home",
            appliance_type="refrigerator",
            vendor_device_id="acme-fridge-202",
            collection_interval_seconds=collection_interval_seconds,
        ),
        Appliance(
            id=3,
            home_id=home_id,
            display_name="Laundry Washer",
            vendor="zenith_iot",
            appliance_type="washer",
            vendor_device_id="zenith-washer-303",
            collection_interval_seconds=collection_interval_seconds,
        ),
    ]


def _demo_readings_for_appliance(home_id: int, appliance: Appliance) -> list[MetricReading]:
    """Return the fixed sample readings used to make reports usable on startup."""

    values_by_type = {
        "air_conditioner": ((820.0, 23.5, "running"), (790.0, 23.1, "idle")),
        "refrigerator": ((145.0, 4.1, "running"), (151.0, 4.3, "running")),
        "washer": ((500.0, None, "running"), (80.0, None, "idle")),
    }
    values = values_by_type[appliance.appliance_type]

    return [
        MetricReading(
            home_id=home_id,
            appliance_id=appliance.id,
            vendor=appliance.vendor,
            appliance_type=appliance.appliance_type,
            power_watts=power_watts,
            temperature_celsius=temperature_celsius,
            operational_state=state,
            recorded_at=SEED_RECORDED_AT[index],
            raw_payload={
                "vendor": appliance.vendor,
                "device_id": appliance.vendor_device_id,
                "sample_index": index,
                "state": state,
            },
        )
        for index, (power_watts, temperature_celsius, state) in enumerate(values)
    ]
