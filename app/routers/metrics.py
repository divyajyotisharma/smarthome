"""Read-only historical metric routes scoped to one home."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_session
from app.schemas import MetricReadingResponse
from app.services import metrics as metrics_service


router = APIRouter(prefix="/homes/{home_id}", tags=["metrics"])


@router.get("/metrics", response_model=list[MetricReadingResponse])
def list_metrics(
    home_id: int,
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    appliance_id: int | None = Query(default=None),
    session: Session = Depends(get_session),
) -> list[MetricReadingResponse]:
    """List historical readings for one home with optional filters."""

    try:
        return metrics_service.list_metrics(
            session=session,
            home_id=home_id,
            start_date=start_date,
            end_date=end_date,
            appliance_id=appliance_id,
        )
    except metrics_service.HomeNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except metrics_service.InvalidDateRangeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
