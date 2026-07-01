from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def _client(tmp_path) -> TestClient:
    db_path = tmp_path / "metrics-test.db"
    settings = Settings(database_url=f"sqlite:///{db_path}")
    return TestClient(create_app(settings))


def test_lists_seeded_metrics_for_home(tmp_path):
    with _client(tmp_path) as client:
        response = client.get("/homes/1/metrics")

    assert response.status_code == 200
    readings = response.json()
    assert len(readings) == 6
    assert "id" not in readings[0]
    assert "metric_reading_id" in readings[0]
    assert readings[0]["home_id"] == 1
    assert readings[0]["appliance_display_name"]
    assert "power_watts" in readings[0]
    assert "temperature_celsius" in readings[0]
    assert "operational_state" in readings[0]
    assert readings[0]["raw_payload"]


def test_collection_created_metrics_are_visible(tmp_path):
    with _client(tmp_path) as client:
        collect_response = client.post("/homes/1/collect")
        metrics_response = client.get("/homes/1/metrics")

    assert collect_response.status_code == 200
    assert metrics_response.status_code == 200
    collected_ids = {reading["metric_reading_id"] for reading in collect_response.json()["readings"]}
    metric_ids = {reading["metric_reading_id"] for reading in metrics_response.json()}
    assert collected_ids.issubset(metric_ids)
    assert all("raw_payload" in reading for reading in metrics_response.json())


def test_filters_metrics_by_appliance_id(tmp_path):
    with _client(tmp_path) as client:
        response = client.get("/homes/1/metrics", params={"appliance_id": 1})

    assert response.status_code == 200
    readings = response.json()
    assert len(readings) == 2
    assert all(reading["appliance_id"] == 1 for reading in readings)


def test_filters_metrics_by_inclusive_date_range(tmp_path):
    with _client(tmp_path) as client:
        included = client.get(
            "/homes/1/metrics",
            params={"start_date": "2026-06-30", "end_date": "2026-06-30"},
        )
        single_day = client.get(
            "/homes/1/metrics",
            params={"start_date": "2026-06-29", "end_date": "2026-06-29"},
        )
        excluded = client.get(
            "/homes/1/metrics",
            params={"start_date": "2026-07-01", "end_date": "2026-07-01"},
        )

    assert included.status_code == 200
    assert len(included.json()) == 3
    assert single_day.status_code == 200
    assert len(single_day.json()) == 3
    assert excluded.status_code == 200
    assert excluded.json() == []


def test_rejects_invalid_metric_date_range(tmp_path):
    with _client(tmp_path) as client:
        response = client.get(
            "/homes/1/metrics",
            params={"start_date": "2026-07-01", "end_date": "2026-06-30"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "start_date must be earlier than or equal to end_date"


def test_metrics_missing_home_returns_404(tmp_path):
    with _client(tmp_path) as client:
        response = client.get("/homes/999/metrics")

    assert response.status_code == 404
    assert response.json()["detail"] == "Home not found"
