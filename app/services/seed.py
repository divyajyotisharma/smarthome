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
    """Create demo homes, appliances, and sample readings when missing."""

    for home_id, home_name, appliance_specs in _demo_home_specs(settings):
        _seed_home(session, home_id, home_name, appliance_specs, settings.default_collection_interval_seconds)

    session.commit()


def _seed_home(
    session: Session,
    home_id: int,
    home_name: str,
    appliance_specs: list[dict],
    collection_interval_seconds: int,
) -> None:
    """Seed one home context without duplicating existing records."""

    home = session.get(Home, home_id)
    if home is None:
        home = Home(id=home_id, name=home_name)
        session.add(home)
        session.flush()

    if not session.scalars(select(Appliance).where(Appliance.home_id == home.id)).first():
        session.add_all(_demo_appliances(home.id, appliance_specs, collection_interval_seconds))
        session.flush()

    if not session.scalars(select(MetricReading).where(MetricReading.home_id == home.id)).first():
        appliances = session.scalars(select(Appliance).where(Appliance.home_id == home.id)).all()
        session.add_all(
            reading
            for appliance in appliances
            for reading in _demo_readings_for_appliance(home.id, appliance)
        )


def _demo_home_specs(settings: Settings) -> list[tuple[int, str, list[dict]]]:
    """Return the fixed home contexts used for local review."""

    return [
        (
            settings.default_home_id,
            settings.default_home_name,
            [
                {
                    "id": 1,
                    "display_name": "Living Room AC",
                    "vendor": "acme_home",
                    "appliance_type": "air_conditioner",
                    "vendor_device_id": "acme-ac-101",
                },
                {
                    "id": 2,
                    "display_name": "Kitchen Refrigerator",
                    "vendor": "acme_home",
                    "appliance_type": "refrigerator",
                    "vendor_device_id": "acme-fridge-202",
                },
                {
                    "id": 3,
                    "display_name": "Laundry Washer",
                    "vendor": "zenith_iot",
                    "appliance_type": "washer",
                    "vendor_device_id": "zenith-washer-303",
                },
            ],
        ),
        (
            2,
            "Weekend Home",
            [
                {
                    "id": 4,
                    "display_name": "Guest Suite AC",
                    "vendor": "zenith_iot",
                    "appliance_type": "air_conditioner",
                    "vendor_device_id": "zenith-ac-204",
                },
                {
                    "id": 5,
                    "display_name": "Garage Refrigerator",
                    "vendor": "acme_home",
                    "appliance_type": "refrigerator",
                    "vendor_device_id": "acme-fridge-205",
                },
            ],
        ),
    ]


def _demo_appliances(
    home_id: int,
    appliance_specs: list[dict],
    collection_interval_seconds: int,
) -> list[Appliance]:
    """Return appliance rows for one seeded home."""

    return [
        Appliance(
            id=spec["id"],
            home_id=home_id,
            display_name=spec["display_name"],
            vendor=spec["vendor"],
            appliance_type=spec["appliance_type"],
            vendor_device_id=spec["vendor_device_id"],
            collection_interval_seconds=collection_interval_seconds,
        )
        for spec in appliance_specs
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
