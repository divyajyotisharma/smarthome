"""Appliance business rules for home-scoped registration and lifecycle changes."""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Appliance, Home, MetricReading
from app.models.core import utc_now
from app.schemas import ApplianceCreateRequest
from app.vendors.registry import is_supported_vendor_appliance


class ApplianceServiceError(Exception):
    """Base exception for appliance service failures."""

    pass


class HomeNotFoundError(ApplianceServiceError):
    """Raised when a requested home does not exist."""

    pass


class ApplianceNotFoundError(ApplianceServiceError):
    """Raised when an appliance is missing or belongs to a different home."""

    pass


class UnsupportedApplianceError(ApplianceServiceError):
    """Raised when a vendor and appliance type are not in the registry."""

    pass


@dataclass(frozen=True)
class ApplianceRegistrationResult:
    """Result of registering a vendor device under a home."""

    appliance: Appliance
    created: bool


def list_appliances(session: Session, home_id: int) -> list[Appliance]:
    """Return all appliances registered under a home."""

    _get_home(session, home_id)
    return list(
        session.scalars(
            select(Appliance).where(Appliance.home_id == home_id).order_by(Appliance.id)
        )
    )


def create_appliance(
    session: Session,
    settings: Settings,
    home_id: int,
    request: ApplianceCreateRequest,
) -> ApplianceRegistrationResult:
    """Create a new appliance record using the default interval when needed."""

    _get_home(session, home_id)
    _validate_supported(request.vendor, request.appliance_type)

    existing_appliance = _find_existing_appliance(
        session=session,
        home_id=home_id,
        vendor=request.vendor,
        vendor_device_id=request.vendor_device_id,
    )
    if existing_appliance is not None:
        return ApplianceRegistrationResult(appliance=existing_appliance, created=False)

    appliance = Appliance(
        home_id=home_id,
        display_name=request.display_name,
        vendor=request.vendor,
        appliance_type=request.appliance_type,
        vendor_device_id=request.vendor_device_id,
        collection_interval_seconds=(
            request.collection_interval_seconds
            if request.collection_interval_seconds is not None
            else settings.default_collection_interval_seconds
        ),
    )
    session.add(appliance)
    session.commit()
    session.refresh(appliance)
    return ApplianceRegistrationResult(appliance=appliance, created=True)


def get_appliance(session: Session, home_id: int, appliance_id: int) -> Appliance:
    """Load one appliance while enforcing the requested home scope."""

    _get_home(session, home_id)
    appliance = session.get(Appliance, appliance_id)
    if appliance is None or appliance.home_id != home_id:
        raise ApplianceNotFoundError("Appliance not found")
    return appliance


def deactivate_appliance(session: Session, home_id: int, appliance_id: int) -> Appliance:
    """Mark an appliance inactive without deleting its historical readings."""

    appliance = get_appliance(session, home_id, appliance_id)
    if appliance.status != "inactive":
        deactivated_at = utc_now()
        appliance.status = "inactive"
        appliance.deactivated_at = deactivated_at
        session.add(_build_deactivation_metric(session, appliance, deactivated_at))
        session.commit()
        session.refresh(appliance)
    return appliance


def _find_existing_appliance(
    session: Session,
    home_id: int,
    vendor: str,
    vendor_device_id: str,
) -> Appliance | None:
    """Return the appliance already representing a vendor device in a home."""

    return session.scalar(
        select(Appliance)
        .where(
            Appliance.home_id == home_id,
            Appliance.vendor == vendor,
            Appliance.vendor_device_id == vendor_device_id,
        )
        .order_by(Appliance.id)
    )


def _build_deactivation_metric(
    session: Session,
    appliance: Appliance,
    recorded_at,
) -> MetricReading:
    """Create a lifecycle metric row that records appliance deactivation."""

    latest_reading = session.scalar(
        select(MetricReading)
        .where(MetricReading.appliance_id == appliance.id)
        .order_by(MetricReading.recorded_at.desc(), MetricReading.id.desc())
    )
    return MetricReading(
        home_id=appliance.home_id,
        appliance_id=appliance.id,
        vendor=appliance.vendor,
        appliance_type=appliance.appliance_type,
        power_watts=latest_reading.power_watts if latest_reading is not None else None,
        temperature_celsius=(
            latest_reading.temperature_celsius if latest_reading is not None else None
        ),
        operational_state="deactivated",
        recorded_at=recorded_at,
        raw_payload={
            "event": "appliance_deactivated",
            "source": "lifecycle",
            "vendor_device_id": appliance.vendor_device_id,
        },
    )


def _get_home(session: Session, home_id: int) -> Home:
    """Shared home existence check used by appliance operations."""

    home = session.get(Home, home_id)
    if home is None:
        raise HomeNotFoundError("Home not found")
    return home


def _validate_supported(vendor: str, appliance_type: str) -> None:
    """Reject appliance registrations that are not in the static registry."""

    if not is_supported_vendor_appliance(vendor, appliance_type):
        raise UnsupportedApplianceError(
            f"Vendor {vendor} does not support appliance type {appliance_type}"
        )
