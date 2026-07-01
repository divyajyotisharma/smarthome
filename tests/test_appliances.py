from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def _client(tmp_path) -> TestClient:
    db_path = tmp_path / "appliance-test.db"
    settings = Settings(database_url=f"sqlite:///{db_path}")
    return TestClient(create_app(settings))


def test_lists_seeded_appliances_for_home(tmp_path):
    with _client(tmp_path) as client:
        response = client.get("/homes/1/appliances")

    assert response.status_code == 200
    appliances = response.json()
    assert len(appliances) == 3
    assert "id" not in appliances[0]
    assert appliances[0]["appliance_id"] == 1
    assert appliances[0]["home_id"] == 1
    assert appliances[0]["display_name"]
    assert appliances[0]["status"] == "active"


def test_gets_one_appliance_by_id(tmp_path):
    with _client(tmp_path) as client:
        response = client.get("/homes/1/appliances/1")

    assert response.status_code == 200
    appliance = response.json()
    assert "id" not in appliance
    assert appliance["appliance_id"] == 1
    assert appliance["home_id"] == 1


def test_registers_supported_appliance_with_default_interval(tmp_path):
    with _client(tmp_path) as client:
        response = client.post(
            "/homes/1/appliances",
            json={
                "display_name": "Bedroom AC",
                "vendor": "zenith_iot",
                "appliance_type": "air_conditioner",
                "vendor_device_id": "zenith-ac-404",
            },
        )
        list_response = client.get("/homes/1/appliances")

    assert response.status_code == 201
    created = response.json()
    assert created["display_name"] == "Bedroom AC"
    assert created["collection_interval_seconds"] == 60
    assert created["status"] == "active"
    assert "id" not in created
    assert any(item["appliance_id"] == created["appliance_id"] for item in list_response.json())


def test_register_appliance_is_idempotent_for_same_home_vendor_device(tmp_path):
    request = {
        "display_name": "Bedroom AC",
        "vendor": "zenith_iot",
        "appliance_type": "air_conditioner",
        "vendor_device_id": "zenith-ac-idempotent",
    }

    with _client(tmp_path) as client:
        first_response = client.post("/homes/1/appliances", json=request)
        second_response = client.post(
            "/homes/1/appliances",
            json={**request, "display_name": "Bedroom AC Duplicate"},
        )
        list_response = client.get("/homes/1/appliances")

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert second_response.json()["appliance_id"] == first_response.json()["appliance_id"]
    assert second_response.json()["display_name"] == "Bedroom AC"
    matching = [
        appliance
        for appliance in list_response.json()
        if appliance["vendor_device_id"] == "zenith-ac-idempotent"
    ]
    assert len(matching) == 1


def test_rejects_unsupported_vendor_type_combination(tmp_path):
    with _client(tmp_path) as client:
        response = client.post(
            "/homes/1/appliances",
            json={
                "display_name": "Unsupported Oven",
                "vendor": "acme_home",
                "appliance_type": "oven",
                "vendor_device_id": "acme-oven-999",
            },
        )

    assert response.status_code == 400
    assert "does not support appliance type" in response.json()["detail"]


def test_get_missing_appliance_returns_404(tmp_path):
    with _client(tmp_path) as client:
        response = client.get("/homes/1/appliances/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Appliance not found"


def test_delete_soft_deactivates_appliance(tmp_path):
    with _client(tmp_path) as client:
        delete_response = client.delete("/homes/1/appliances/1")
        fetch_response = client.get("/homes/1/appliances/1")

    assert delete_response.status_code == 200
    assert delete_response.json()["status"] == "inactive"
    assert delete_response.json()["deactivated_at"] is not None
    assert fetch_response.status_code == 200
    assert fetch_response.json()["status"] == "inactive"


def test_delete_registers_deactivation_metric_with_latest_known_values(tmp_path):
    with _client(tmp_path) as client:
        before_metrics = client.get("/homes/1/metrics", params={"appliance_id": 1}).json()
        delete_response = client.delete("/homes/1/appliances/1")
        after_metrics = client.get("/homes/1/metrics", params={"appliance_id": 1}).json()
        second_delete_response = client.delete("/homes/1/appliances/1")
        final_metrics = client.get("/homes/1/metrics", params={"appliance_id": 1}).json()

    assert delete_response.status_code == 200
    assert second_delete_response.status_code == 200
    assert len(after_metrics) == len(before_metrics) + 1
    assert len(final_metrics) == len(after_metrics)

    deactivation_metric = after_metrics[0]
    previous_latest_metric = before_metrics[0]
    assert deactivation_metric["operational_state"] == "deactivated"
    assert deactivation_metric["power_watts"] == previous_latest_metric["power_watts"]
    assert deactivation_metric["temperature_celsius"] == previous_latest_metric["temperature_celsius"]
    assert deactivation_metric["raw_payload"]["event"] == "appliance_deactivated"
