"""APScheduler wiring for demo collection and startup report jobs."""

from collections.abc import Callable
from datetime import timedelta
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.config import Settings
from app.models.core import utc_now
from app.services import collection
from app.services import reports
from app.services.seed import SEED_RECORDED_AT


logger = logging.getLogger(__name__)


def create_report_scheduler(
    settings: Settings,
    session_factory: Callable[[], Session],
) -> BackgroundScheduler:
    """Create the in-process scheduler used by the FastAPI lifespan."""

    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        generate_startup_daily_report,
        trigger="date",
        run_date=utc_now() + timedelta(seconds=settings.startup_report_delay_seconds),
        id="startup-daily-report",
        name="startup daily report",
        kwargs={
            "session_factory": session_factory,
            "home_id": settings.default_home_id,
        },
        replace_existing=True,
    )
    scheduler.add_job(
        collect_due_appliance_metrics,
        trigger="interval",
        seconds=settings.scheduler_tick_interval_seconds,
        id="due-appliance-collection",
        name="due appliance metric collection",
        kwargs={"session_factory": session_factory},
        replace_existing=True,
    )
    return scheduler


def generate_startup_daily_report(
    session_factory: Callable[[], Session],
    home_id: int,
) -> None:
    """Generate the demo daily report after the app has started."""

    with session_factory() as session:
        report = reports.generate_daily_report(session, home_id, SEED_RECORDED_AT[0].date())
    logger.info(
        "Generated startup daily report for home_id=%s readings=%s",
        home_id,
        report.total_metric_readings,
    )


def collect_default_home_metrics(
    session_factory: Callable[[], Session],
    home_id: int,
) -> None:
    """Run a home-level collection pass for demo compatibility."""

    with session_factory() as session:
        readings, skipped_count = collection.collect_for_home(session, home_id)
    logger.info(
        "Collected scheduled metrics for home_id=%s readings=%s skipped=%s",
        home_id,
        len(readings),
        skipped_count,
    )


def collect_due_appliance_metrics(
    session_factory: Callable[[], Session],
) -> None:
    """Run scheduled collection for appliances whose own interval is due."""

    with session_factory() as session:
        readings, skipped_count = collection.collect_due_appliances(session)
    logger.info(
        "Collected scheduled due appliance metrics readings=%s skipped=%s",
        len(readings),
        skipped_count,
    )
