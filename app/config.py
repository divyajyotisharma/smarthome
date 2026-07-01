"""Central configuration for the SmartHome backend."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Runtime settings used by API, seed, and scheduler code."""

    database_url: str = "sqlite:///data/smarthome.db"
    default_home_id: int = 1
    default_home_name: str = "Demo Home"
    default_collection_interval_seconds: int = 60
    scheduler_tick_interval_seconds: int = 1
    startup_report_delay_seconds: int = 60


settings = Settings()
