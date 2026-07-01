from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def _client(tmp_path) -> TestClient:
    db_path = tmp_path / "reports-test.db"
    settings = Settings(database_url=f"sqlite:///{db_path}")
    return TestClient(create_app(settings))


def _summary_by_appliance(report: dict) -> dict[int, dict]:
    return {item["appliance_id"]: item for item in report["appliances"]}


def test_daily_report_summarizes_seeded_metrics(tmp_path):
    with _client(tmp_path) as client:
        response = client.get("/homes/1/reports/daily", params={"date": "2026-06-30"})

    assert response.status_code == 200
    report = response.json()
    summaries = _summary_by_appliance(report)

    assert report["report_type"] == "daily"
    assert report["home_id"] == 1
    assert report["start_date"] == "2026-06-30"
    assert report["end_date"] == "2026-06-30"
    assert report["total_appliances"] == 3
    assert report["total_metric_readings"] == 3
    assert summaries[1]["display_name"] == "Living Room AC"
    assert summaries[1]["readings_count"] == 1
    assert summaries[1]["power_watts"] == {"avg": 820.0, "min": 820.0, "max": 820.0}
    assert summaries[1]["temperature_celsius"] == {"avg": 23.5, "min": 23.5, "max": 23.5}
    assert summaries[1]["state_counts"] == {"running": 1}
    assert summaries[1]["latest_reading_at"] is not None


def test_custom_report_summarizes_inclusive_range(tmp_path):
    with _client(tmp_path) as client:
        response = client.get(
            "/homes/1/reports/custom",
            params={"start_date": "2026-06-29", "end_date": "2026-06-30"},
        )

    assert response.status_code == 200
    report = response.json()
    assert report["report_type"] == "custom"
    assert report["start_date"] == "2026-06-29"
    assert report["end_date"] == "2026-06-30"
    assert report["total_appliances"] == 3
    assert report["total_metric_readings"] == 6


def test_report_empty_range_keeps_appliance_context(tmp_path):
    with _client(tmp_path) as client:
        response = client.get("/homes/1/reports/daily", params={"date": "2026-07-01"})

    assert response.status_code == 200
    report = response.json()
    assert report["total_appliances"] == 3
    assert report["total_metric_readings"] == 0
    assert len(report["appliances"]) == 3
    assert all(item["readings_count"] == 0 for item in report["appliances"])
    assert all(item["power_watts"] == {"avg": None, "min": None, "max": None} for item in report["appliances"])
    assert all(item["latest_reading_at"] is None for item in report["appliances"])


def test_custom_report_rejects_invalid_range(tmp_path):
    with _client(tmp_path) as client:
        response = client.get(
            "/homes/1/reports/custom",
            params={"start_date": "2026-07-01", "end_date": "2026-06-30"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "start_date must be earlier than or equal to end_date"


@pytest.mark.parametrize(
    ("path", "params"),
    [
        ("/homes/999/reports/daily", {"date": "2026-06-30"}),
        ("/homes/999/reports/custom", {"start_date": "2026-06-30", "end_date": "2026-06-30"}),
    ],
)
def test_report_missing_home_returns_404(tmp_path, path, params):
    with _client(tmp_path) as client:
        response = client.get(path, params=params)

    assert response.status_code == 404
    assert response.json()["detail"] == "Home not found"


def test_scheduler_registers_startup_daily_report_job(tmp_path):
    from app.scheduler import create_report_scheduler

    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'scheduler-test.db'}",
        startup_report_delay_seconds=5,
    )
    scheduler = create_report_scheduler(settings, session_factory=lambda: None)

    jobs = scheduler.get_jobs()
    job = next(item for item in jobs if item.id == "startup-daily-report")

    assert job.name == "startup daily report"
    assert job.kwargs["home_id"] == settings.default_home_id
    assert job.trigger.run_date > datetime.now(timezone.utc)


def test_scheduler_registers_due_appliance_collection_interval_job(tmp_path):
    from app.scheduler import create_report_scheduler

    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'scheduler-test.db'}",
        default_collection_interval_seconds=7,
        scheduler_tick_interval_seconds=3,
    )
    scheduler = create_report_scheduler(settings, session_factory=lambda: None)

    jobs = scheduler.get_jobs()
    job = next(item for item in jobs if item.id == "due-appliance-collection")

    assert job.name == "due appliance metric collection"
    assert "home_id" not in job.kwargs
    assert job.trigger.interval.total_seconds() == settings.scheduler_tick_interval_seconds


def test_scheduler_default_tick_supports_short_demo_intervals(tmp_path):
    from app.scheduler import create_report_scheduler

    settings = Settings(database_url=f"sqlite:///{tmp_path / 'scheduler-test.db'}")
    scheduler = create_report_scheduler(settings, session_factory=lambda: None)

    job = next(item for item in scheduler.get_jobs() if item.id == "due-appliance-collection")

    assert settings.scheduler_tick_interval_seconds == 1
    assert job.trigger.interval.total_seconds() == 1
