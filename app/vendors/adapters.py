"""Mock vendor adapters that normalize different payload styles into one shape."""

from dataclasses import dataclass
from datetime import datetime

from app.models import Appliance
from app.models.core import utc_now


@dataclass(frozen=True)
class NormalizedReading:
    """Canonical metric payload returned by vendor adapters."""

    appliance_id: int
    home_id: int
    vendor: str
    appliance_type: str
    power_watts: float | None
    temperature_celsius: float | None
    operational_state: str | None
    recorded_at: datetime
    raw_payload: dict


class VendorAdapter:
    """Base contract for vendor-specific collectors."""

    vendor: str

    def collect(self, appliance: Appliance) -> NormalizedReading:
        """Collect and normalize one reading for the given appliance."""

        raise NotImplementedError


class AcmeHomeAdapter(VendorAdapter):
    """Mock adapter for the acme_home vendor payload shape."""

    vendor = "acme_home"

    def collect(self, appliance: Appliance) -> NormalizedReading:
        raw_payload = {
            "device_id": appliance.vendor_device_id,
            "power_watts": _power_for(appliance),
            "temp_celsius": _temperature_for(appliance),
            "status": "cooling" if appliance.appliance_type == "air_conditioner" else "running",
        }
        return NormalizedReading(
            appliance_id=appliance.id,
            home_id=appliance.home_id,
            vendor=appliance.vendor,
            appliance_type=appliance.appliance_type,
            power_watts=raw_payload["power_watts"],
            temperature_celsius=raw_payload["temp_celsius"],
            operational_state=_normalize_state(raw_payload["status"]),
            recorded_at=utc_now(),
            raw_payload=raw_payload,
        )


class ZenithIotAdapter(VendorAdapter):
    """Mock adapter for the zenith_iot vendor payload shape."""

    vendor = "zenith_iot"

    def collect(self, appliance: Appliance) -> NormalizedReading:
        raw_payload = {
            "id": appliance.vendor_device_id,
            "energyUsageW": _power_for(appliance),
            "temperatureF": 74.3 if appliance.appliance_type == "air_conditioner" else None,
            "state": "RUNNING",
        }
        return NormalizedReading(
            appliance_id=appliance.id,
            home_id=appliance.home_id,
            vendor=appliance.vendor,
            appliance_type=appliance.appliance_type,
            power_watts=raw_payload["energyUsageW"],
            temperature_celsius=_fahrenheit_to_celsius(raw_payload["temperatureF"]),
            operational_state=_normalize_state(raw_payload["state"]),
            recorded_at=utc_now(),
            raw_payload=raw_payload,
        )


ADAPTERS: dict[str, VendorAdapter] = {
    "acme_home": AcmeHomeAdapter(),
    "zenith_iot": ZenithIotAdapter(),
}


def adapter_for(vendor: str) -> VendorAdapter:
    """Return the configured adapter for a supported vendor."""

    return ADAPTERS[vendor]


def _power_for(appliance: Appliance) -> float:
    """Return deterministic sample power values for the mocked adapters."""

    if appliance.appliance_type == "air_conditioner":
        return 820.0
    if appliance.appliance_type == "refrigerator":
        return 145.0
    return 500.0


def _temperature_for(appliance: Appliance) -> float | None:
    """Return deterministic sample temperature values for the mocked adapters."""

    if appliance.appliance_type == "air_conditioner":
        return 23.5
    if appliance.appliance_type == "refrigerator":
        return 4.1
    return None


def _fahrenheit_to_celsius(value: float | None) -> float | None:
    """Normalize Fahrenheit readings into Celsius for the canonical model."""

    if value is None:
        return None
    return round((value - 32) * 5 / 9, 1)


def _normalize_state(value: str) -> str:
    """Map vendor-specific state strings into the shared report vocabulary."""

    normalized = value.lower()
    if normalized in {"cooling", "running"}:
        return "running"
    if normalized in {"idle", "standby"}:
        return "idle"
    return normalized
