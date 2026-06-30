from importlib import import_module

from app.main import app


def test_app_uses_logical_packages_for_core_layers():
    expected_modules = [
        "app.models.core",
        "app.schemas.core",
        "app.routers.appliances",
        "app.routers.collection",
        "app.routers.homes",
        "app.routers.metrics",
        "app.routers.reports",
        "app.routers.vendors",
        "app.scheduler",
        "app.services.appliances",
        "app.services.collection",
        "app.services.metrics",
        "app.services.reports",
        "app.services.seed",
        "app.vendors.adapters",
        "app.vendors.registry",
    ]

    for module_name in expected_modules:
        assert import_module(module_name)


def test_openapi_still_exposes_existing_feature_routes():
    paths = app.openapi()["paths"]

    assert "/health" in paths
    assert "/homes/{home_id}" in paths
    assert "/homes/{home_id}/appliances" in paths
    assert "/homes/{home_id}/appliances/{appliance_id}" in paths
    assert "/homes/{home_id}/collect" in paths
    assert "/homes/{home_id}/metrics" in paths
    assert "/homes/{home_id}/reports/daily" in paths
    assert "/homes/{home_id}/reports/custom" in paths
    assert "/vendors" in paths


def test_openapi_uses_client_friendly_operation_summaries():
    paths = app.openapi()["paths"]

    assert paths["/homes/{home_id}/appliances"]["post"]["summary"] == "Register Appliance"
    assert (
        paths["/homes/{home_id}/appliances/{appliance_id}"]["delete"]["summary"]
        == "Deactivate Appliance"
    )
    assert paths["/homes/{home_id}/collect"]["post"]["summary"] == "Manual Collect For Each Home"


def test_openapi_exposes_appliance_detail_read_route():
    paths = app.openapi()["paths"]

    assert "get" in paths["/homes/{home_id}/appliances/{appliance_id}"]


def test_register_appliance_schema_has_swagger_example():
    schemas = app.openapi()["components"]["schemas"]

    assert schemas["ApplianceCreateRequest"]["examples"] == [
        {
            "display_name": "Living Room AC",
            "vendor": "acme_home",
            "appliance_type": "air_conditioner",
            "vendor_device_id": "acme-ac-demo-1",
            "collection_interval_seconds": 60,
        }
    ]
