from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.config import Settings
from app.db import create_engine_for_settings, create_session_factory
from app.main import create_app
from app.models import Appliance, MetricReading
from app.models.core import utc_now
from app.services import collection


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
    assert all("id" not in reading for reading in payload["readings"])
    assert all("metric_reading_id" in reading for reading in payload["readings"])
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


def test_collection_includes_newly_registered_weekend_home_appliance(tmp_path):
    client, _ = _client_and_settings(tmp_path)

    with client:
        create_response = client.post(
            "/homes/2/appliances",
            json={
                "display_name": "Weekend Bedroom AC",
                "vendor": "zenith_iot",
                "appliance_type": "air_conditioner",
                "vendor_device_id": "zenith-weekend-ac-901",
            },
        )
        collect_response = client.post("/homes/2/collect")

    assert create_response.status_code == 201
    created_appliance_id = create_response.json()["appliance_id"]
    assert collect_response.status_code == 200
    assert any(
        reading["appliance_id"] == created_appliance_id
        for reading in collect_response.json()["readings"]
    )


def test_scheduled_collection_uses_each_appliance_interval(tmp_path):
    client, settings = _client_and_settings(tmp_path)

    with client:
        pass

    engine = create_engine_for_settings(settings)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        home_one_appliances = list(
            session.scalars(
                select(Appliance)
                .where(Appliance.home_id == 1)
                .order_by(Appliance.id)
            )
        )
        all_appliances = list(session.scalars(select(Appliance).order_by(Appliance.id)))
        due_appliance = home_one_appliances[0]
        for appliance in all_appliances:
            appliance.collection_interval_seconds = 3600
        due_appliance.collection_interval_seconds = 60
        due_appliance_id = due_appliance.id

        now = utc_now()
        session.add_all(
            MetricReading(
                home_id=appliance.home_id,
                appliance_id=appliance.id,
                vendor=appliance.vendor,
                appliance_type=appliance.appliance_type,
                power_watts=1.0,
                temperature_celsius=None,
                operational_state="test",
                recorded_at=now - timedelta(seconds=61),
                raw_payload={"source": "test"},
            )
            for appliance in all_appliances
        )
        session.commit()

        readings, skipped_count = collection.collect_due_appliances(session, now=now)

    assert skipped_count == 0
    assert {reading.appliance_id for reading in readings} == {due_appliance_id}
    assert readings[0].recorded_at.replace(tzinfo=now.tzinfo) == now


def test_scheduled_collection_picks_up_new_due_appliance_without_restart(tmp_path):
    client, settings = _client_and_settings(tmp_path)

    with client:
        response = client.post(
            "/homes/2/appliances",
            json={
                "display_name": "Weekend Bedroom AC",
                "vendor": "zenith_iot",
                "appliance_type": "air_conditioner",
                "vendor_device_id": "zenith-weekend-ac-902",
                "collection_interval_seconds": 60,
            },
        )

    assert response.status_code == 201
    appliance_id = response.json()["appliance_id"]

    engine = create_engine_for_settings(settings)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        readings, skipped_count = collection.collect_due_appliances(session, now=utc_now())

    assert skipped_count == 0
    assert any(reading.appliance_id == appliance_id for reading in readings)


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
