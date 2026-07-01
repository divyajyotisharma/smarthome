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
    assert second_response.status_code == 200
    assert second_response.json()["appliance_id"] == first_response.json()["appliance_id"]
    assert second_response.json()["display_name"] == "Bedroom AC"
    matching = [
        appliance
        for appliance in list_response.json()
        if appliance["vendor_device_id"] == "zenith-ac-idempotent"
    ]
    assert len(matching) == 1


def test_idempotent_duplicate_registration_returns_200_ok(tmp_path):
    request = {
        "display_name": "Bedroom AC",
        "vendor": "zenith_iot",
        "appliance_type": "air_conditioner",
        "vendor_device_id": "zenith-ac-status-code",
    }

    with _client(tmp_path) as client:
        first_response = client.post("/homes/1/appliances", json=request)
        duplicate_response = client.post("/homes/1/appliances", json=request)

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 200
    assert duplicate_response.json()["appliance_id"] == first_response.json()["appliance_id"]


def test_register_idempotency_is_scoped_to_home(tmp_path):
    request = {
        "display_name": "Shared Device ID",
        "vendor": "zenith_iot",
        "appliance_type": "air_conditioner",
        "vendor_device_id": "shared-device-001",
    }

    with _client(tmp_path) as client:
        home_one_response = client.post("/homes/1/appliances", json=request)
        home_two_response = client.post("/homes/2/appliances", json=request)

    assert home_one_response.status_code == 201
    assert home_two_response.status_code == 201
    assert home_one_response.json()["appliance_id"] != home_two_response.json()["appliance_id"]
    assert home_one_response.json()["home_id"] == 1
    assert home_two_response.json()["home_id"] == 2


def test_register_idempotency_is_scoped_to_vendor(tmp_path):
    with _client(tmp_path) as client:
        acme_response = client.post(
            "/homes/1/appliances",
            json={
                "display_name": "Acme AC",
                "vendor": "acme_home",
                "appliance_type": "air_conditioner",
                "vendor_device_id": "same-vendor-device-id",
            },
        )
        zenith_response = client.post(
            "/homes/1/appliances",
            json={
                "display_name": "Zenith AC",
                "vendor": "zenith_iot",
                "appliance_type": "air_conditioner",
                "vendor_device_id": "same-vendor-device-id",
            },
        )

    assert acme_response.status_code == 201
    assert zenith_response.status_code == 201
    assert acme_response.json()["appliance_id"] != zenith_response.json()["appliance_id"]


def test_register_existing_inactive_vendor_device_returns_existing_inactive_appliance(tmp_path):
    request = {
        "display_name": "Temporary AC",
        "vendor": "zenith_iot",
        "appliance_type": "air_conditioner",
        "vendor_device_id": "inactive-device-001",
    }

    with _client(tmp_path) as client:
        create_response = client.post("/homes/1/appliances", json=request)
        appliance_id = create_response.json()["appliance_id"]
        client.delete(f"/homes/1/appliances/{appliance_id}")
        duplicate_response = client.post(
            "/homes/1/appliances",
            json={**request, "display_name": "Temporary AC Again"},
        )

    assert duplicate_response.status_code == 200
    assert duplicate_response.json()["appliance_id"] == appliance_id
    assert duplicate_response.json()["status"] == "inactive"


def test_register_missing_home_returns_404(tmp_path):
    with _client(tmp_path) as client:
        response = client.post(
            "/homes/999/appliances",
            json={
                "display_name": "Missing Home AC",
                "vendor": "zenith_iot",
                "appliance_type": "air_conditioner",
                "vendor_device_id": "missing-home-device",
            },
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Home not found"


def test_register_missing_required_field_returns_422(tmp_path):
    with _client(tmp_path) as client:
        response = client.post(
            "/homes/1/appliances",
            json={
                "display_name": "Incomplete Device",
                "vendor": "zenith_iot",
                "appliance_type": "washer",
            },
        )

    assert response.status_code == 422


def test_register_rejects_non_positive_collection_interval(tmp_path):
    with _client(tmp_path) as client:
        response = client.post(
            "/homes/1/appliances",
            json={
                "display_name": "Invalid Interval Washer",
                "vendor": "zenith_iot",
                "appliance_type": "washer",
                "vendor_device_id": "invalid-interval-washer",
                "collection_interval_seconds": 0,
            },
        )

    assert response.status_code == 422


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


def test_list_missing_home_returns_404(tmp_path):
    with _client(tmp_path) as client:
        response = client.get("/homes/999/appliances")

    assert response.status_code == 404
    assert response.json()["detail"] == "Home not found"


def test_get_appliance_from_wrong_home_returns_404(tmp_path):
    with _client(tmp_path) as client:
        response = client.get("/homes/2/appliances/1")

    assert response.status_code == 404
    assert response.json()["detail"] == "Appliance not found"


def test_delete_appliance_from_wrong_home_returns_404(tmp_path):
    with _client(tmp_path) as client:
        response = client.delete("/homes/2/appliances/1")

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


def test_delete_registers_deactivation_metric_without_prior_reading(tmp_path):
    with _client(tmp_path) as client:
        create_response = client.post(
            "/homes/1/appliances",
            json={
                "display_name": "No Reading Washer",
                "vendor": "zenith_iot",
                "appliance_type": "washer",
                "vendor_device_id": "no-reading-washer-001",
            },
        )
        appliance_id = create_response.json()["appliance_id"]
        delete_response = client.delete(f"/homes/1/appliances/{appliance_id}")
        metrics_response = client.get(
            "/homes/1/metrics",
            params={"appliance_id": appliance_id},
        )

    assert delete_response.status_code == 200
    assert metrics_response.status_code == 200
    assert metrics_response.json()[0]["operational_state"] == "deactivated"
    assert metrics_response.json()[0]["power_watts"] is None
    assert metrics_response.json()[0]["temperature_celsius"] is None
