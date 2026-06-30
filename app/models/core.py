"""Core SmartHome persistence models."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp for persisted records."""

    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Declarative base shared by all SmartHome models."""

    pass


class Home(Base):
    """Home groups appliances and readings for one client/home context."""

    __tablename__ = "homes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    appliances: Mapped[list["Appliance"]] = relationship(back_populates="home")
    metric_readings: Mapped[list["MetricReading"]] = relationship(back_populates="home")


class Appliance(Base):
    """Registered device instance under a home; vendor behavior stays outside this model."""

    __tablename__ = "appliances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    home_id: Mapped[int] = mapped_column(ForeignKey("homes.id"), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    vendor: Mapped[str] = mapped_column(String(80), nullable=False)
    appliance_type: Mapped[str] = mapped_column(String(80), nullable=False)
    vendor_device_id: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False)
    collection_interval_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    deactivated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    home: Mapped[Home] = relationship(back_populates="appliances")
    metric_readings: Mapped[list["MetricReading"]] = relationship(back_populates="appliance")


class MetricReading(Base):
    """Normalized metric columns plus raw vendor payload for traceability."""

    __tablename__ = "metric_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    home_id: Mapped[int] = mapped_column(ForeignKey("homes.id"), nullable=False, index=True)
    appliance_id: Mapped[int] = mapped_column(ForeignKey("appliances.id"), nullable=False, index=True)
    vendor: Mapped[str] = mapped_column(String(80), nullable=False)
    appliance_type: Mapped[str] = mapped_column(String(80), nullable=False)
    power_watts: Mapped[float | None] = mapped_column(Float, nullable=True)
    temperature_celsius: Mapped[float | None] = mapped_column(Float, nullable=True)
    operational_state: Mapped[str | None] = mapped_column(String(40), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    raw_payload: Mapped[dict] = mapped_column(JSON, nullable=False)

    home: Mapped[Home] = relationship(back_populates="metric_readings")
    appliance: Mapped[Appliance] = relationship(back_populates="metric_readings")
