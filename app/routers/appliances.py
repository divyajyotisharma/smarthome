"""Home-scoped appliance registration and lifecycle routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_session
from app.schemas import ApplianceCreateRequest, ApplianceResponse
from app.services import appliances as appliance_service


router = APIRouter(prefix="/homes/{home_id}/appliances", tags=["appliances"])


@router.get("", response_model=list[ApplianceResponse])
def list_appliances(
    home_id: int,
    session: Session = Depends(get_session),
):
    """List appliances for one home context."""

    try:
        return appliance_service.list_appliances(session, home_id)
    except appliance_service.HomeNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "",
    response_model=ApplianceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register Appliance",
)
def create_appliance(
    home_id: int,
    request: ApplianceCreateRequest,
    session: Session = Depends(get_session),
):
    """Register a new appliance under the requested home."""

    try:
        return appliance_service.create_appliance(session, settings, home_id, request)
    except appliance_service.HomeNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except appliance_service.UnsupportedApplianceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{appliance_id}", response_model=ApplianceResponse)
def get_appliance(
    home_id: int,
    appliance_id: int,
    session: Session = Depends(get_session),
):
    """Fetch one appliance within the requested home."""

    try:
        return appliance_service.get_appliance(session, home_id, appliance_id)
    except (appliance_service.HomeNotFoundError, appliance_service.ApplianceNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete(
    "/{appliance_id}",
    response_model=ApplianceResponse,
    summary="Deactivate Appliance",
)
def delete_appliance(
    home_id: int,
    appliance_id: int,
    session: Session = Depends(get_session),
):
    """Soft deactivate an appliance while preserving its reading history."""

    try:
        return appliance_service.deactivate_appliance(session, home_id, appliance_id)
    except (appliance_service.HomeNotFoundError, appliance_service.ApplianceNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
