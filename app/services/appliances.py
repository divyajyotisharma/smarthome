"""Appliance business rules for home-scoped registration and lifecycle changes."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Appliance, Home
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
) -> Appliance:
    """Create a new appliance record using the default interval when needed."""

    _get_home(session, home_id)
    _validate_supported(request.vendor, request.appliance_type)

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
    return appliance


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
        appliance.status = "inactive"
        appliance.deactivated_at = utc_now()
        session.commit()
        session.refresh(appliance)
    return appliance


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
