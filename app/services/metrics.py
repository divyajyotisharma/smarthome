"""Historical metric queries and filter rules for one home."""

from datetime import date, datetime, time, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Home, MetricReading


class MetricsServiceError(Exception):
    """Base exception for historical metric lookups."""

    pass


class HomeNotFoundError(MetricsServiceError):
    """Raised when the requested home does not exist."""

    pass


class InvalidDateRangeError(MetricsServiceError):
    """Raised when a report or filter range is inverted."""

    pass


def list_metrics(
    session: Session,
    home_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
    appliance_id: int | None = None,
) -> list[MetricReading]:
    """Return a home's metric history with optional appliance and date filters."""

    home = session.get(Home, home_id)
    if home is None:
        raise HomeNotFoundError("Home not found")

    if start_date is not None and end_date is not None and start_date > end_date:
        raise InvalidDateRangeError("start_date must be earlier than or equal to end_date")

    query = select(MetricReading).where(MetricReading.home_id == home_id)

    if appliance_id is not None:
        query = query.where(MetricReading.appliance_id == appliance_id)
    if start_date is not None:
        query = query.where(MetricReading.recorded_at >= _start_of_day(start_date))
    if end_date is not None:
        query = query.where(MetricReading.recorded_at <= _end_of_day(end_date))

    query = query.order_by(MetricReading.recorded_at.desc(), MetricReading.id.desc())
    return list(session.scalars(query))


def _start_of_day(value: date) -> datetime:
    """Convert a date filter to the start of that UTC day."""

    return datetime.combine(value, time.min, tzinfo=timezone.utc)


def _end_of_day(value: date) -> datetime:
    """Convert a date filter to the end of that UTC day."""

    return datetime.combine(value, time.max, tzinfo=timezone.utc)
