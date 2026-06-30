"""Static supported-device registry used to validate appliance registration."""

SUPPORTED_VENDOR_APPLIANCES: dict[str, set[str]] = {
    "acme_home": {"air_conditioner", "refrigerator"},
    "zenith_iot": {"air_conditioner", "washer"},
}

NORMALIZED_METRICS = ["power_watts", "temperature_celsius", "operational_state"]


def is_supported_vendor_appliance(vendor: str, appliance_type: str) -> bool:
    """Check whether a vendor and appliance type are supported together."""

    return appliance_type in SUPPORTED_VENDOR_APPLIANCES.get(vendor, set())


def vendor_capabilities() -> list[dict]:
    """Return API-friendly capability summaries for the mock vendors."""

    return [
        {
            "vendor": vendor,
            "supported_appliance_types": sorted(appliance_types),
            "normalized_metrics": NORMALIZED_METRICS,
        }
        for vendor, appliance_types in sorted(SUPPORTED_VENDOR_APPLIANCES.items())
    ]
