from fastapi.testclient import TestClient
from sqlalchemy import select

from app.config import Settings
from app.db import create_engine_for_settings, create_session_factory
from app.main import create_app
from app.models import MetricReading


def _client_and_settings(tmp_path):
    db_path = tmp_path / "collection-test.db"
    settings = Settings(database_url=f"sqlite:///{db_path}")
    return TestClient(create_app(settings)), settings


def _reading_count(settings: Settings) -> int:
    engine = create_engine_for_settings(settings)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        return len(session.scalars(select(MetricReading)).all())


def test_lists_vendor_capabilities_with_overlapping_appliance_type(tmp_path):
    client, _ = _client_and_settings(tmp_path)

    with client:
        response = client.get("/vendors")

    assert response.status_code == 200
    capabilities = response.json()
    vendors = {item["vendor"]: item for item in capabilities}

    assert {"acme_home", "zenith_iot"}.issubset(vendors)
    assert "air_conditioner" in vendors["acme_home"]["supported_appliance_types"]
    assert "air_conditioner" in vendors["zenith_iot"]["supported_appliance_types"]
    assert "power_watts" in vendors["acme_home"]["normalized_metrics"]


def test_collects_metrics_for_active_home_appliances(tmp_path):
    client, _ = _client_and_settings(tmp_path)

    with client:
        response = client.post("/homes/1/collect")

    assert response.status_code == 200
    payload = response.json()
    assert payload["home_id"] == 1
    assert payload["collected_count"] == 3
    assert payload["skipped_count"] == 0
    assert len(payload["readings"]) == 3
    assert all(reading["raw_payload"] for reading in payload["readings"])
    assert all("operational_state" in reading for reading in payload["readings"])


def test_collection_persists_metric_readings(tmp_path):
    client, settings = _client_and_settings(tmp_path)

    with client:
        before_count = _reading_count(settings)
        response = client.post("/homes/1/collect")
        after_count = _reading_count(settings)

    assert response.status_code == 200
    assert after_count - before_count == response.json()["collected_count"]


def test_collection_skips_inactive_appliances(tmp_path):
    client, _ = _client_and_settings(tmp_path)

    with client:
        client.delete("/homes/1/appliances/1")
        response = client.post("/homes/1/collect")

    assert response.status_code == 200
    payload = response.json()
    assert payload["collected_count"] == 2
    assert payload["skipped_count"] == 1
    assert all(reading["appliance_id"] != 1 for reading in payload["readings"])


def test_collect_missing_home_returns_404(tmp_path):
    client, _ = _client_and_settings(tmp_path)

    with client:
        response = client.post("/homes/999/collect")

    assert response.status_code == 404
    assert response.json()["detail"] == "Home not found"
