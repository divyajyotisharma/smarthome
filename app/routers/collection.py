"""Manual home-level metric collection routes used for demos and tests."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_session
from app.schemas import CollectionRunResponse
from app.services import collection as collection_service


router = APIRouter(prefix="/homes/{home_id}", tags=["collection"])


@router.post(
    "/collect",
    response_model=CollectionRunResponse,
    summary="Manual Collect For Each Home",
)
def collect_for_home(home_id: int, session: Session = Depends(get_session)) -> CollectionRunResponse:
    """Trigger one collection pass for all active appliances in a home."""

    try:
        readings, skipped_count = collection_service.collect_for_home(session, home_id)
    except collection_service.HomeNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return CollectionRunResponse(
        home_id=home_id,
        collected_count=len(readings),
        skipped_count=skipped_count,
        readings=readings,
    )
