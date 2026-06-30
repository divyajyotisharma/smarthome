"""Report endpoints that summarize historical readings for a home."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_session
from app.schemas import ReportResponse
from app.services import reports as reports_service


router = APIRouter(prefix="/homes/{home_id}/reports", tags=["reports"])


@router.get("/daily", response_model=ReportResponse)
def get_daily_report(
    home_id: int,
    report_date: date = Query(alias="date"),
    session: Session = Depends(get_session),
) -> ReportResponse:
    """Generate a one-day report from the home's stored metrics."""

    try:
        return reports_service.generate_daily_report(session, home_id, report_date)
    except reports_service.HomeNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/custom", response_model=ReportResponse)
def get_custom_report(
    home_id: int,
    start_date: date,
    end_date: date,
    session: Session = Depends(get_session),
) -> ReportResponse:
    """Generate a report for an inclusive custom date range."""

    try:
        return reports_service.generate_report(session, home_id, start_date, end_date)
    except reports_service.HomeNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except reports_service.InvalidDateRangeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
