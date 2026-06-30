"""Vendor capability route for the mock integration registry."""

from fastapi import APIRouter

from app.schemas import VendorCapabilityResponse
from app.vendors.registry import vendor_capabilities


router = APIRouter(prefix="/vendors", tags=["vendors"])


@router.get("", response_model=list[VendorCapabilityResponse])
def list_vendors() -> list[dict]:
    """Expose mocked vendor capabilities for Swagger and reviewers."""

    return vendor_capabilities()
