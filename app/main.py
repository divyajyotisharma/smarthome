"""FastAPI application factory for the SmartHome assignment."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import Settings, settings
from app.db import create_engine_for_settings, create_session_factory, create_tables
from app.routers import appliances, collection, homes, metrics, reports, vendors
from app.scheduler import create_report_scheduler
from app.schemas import HealthResponse
from app.services.seed import seed_demo_data


def create_app(app_settings: Settings = settings) -> FastAPI:
    """Build the application, wire dependencies, and start background jobs."""

    app_engine = create_engine_for_settings(app_settings)
    session_factory = create_session_factory(app_engine)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        create_tables(app_engine)
        with session_factory() as session:
            seed_demo_data(session, app_settings)
        report_scheduler = create_report_scheduler(app_settings, session_factory)
        report_scheduler.start()
        yield
        report_scheduler.shutdown(wait=False)

    app = FastAPI(
        title="SmartHome API",
        version="0.1.0",
        description="Backend API for managing smart home appliances, metrics, and reports.",
        lifespan=lifespan,
    )

    def get_app_session():
        with session_factory() as session:
            yield session

    app.dependency_overrides[appliances.get_session] = get_app_session
    app.dependency_overrides[collection.get_session] = get_app_session
    app.dependency_overrides[homes.get_session] = get_app_session
    app.dependency_overrides[metrics.get_session] = get_app_session
    app.dependency_overrides[reports.get_session] = get_app_session
    app.include_router(appliances.router)
    app.include_router(collection.router)
    app.include_router(homes.router)
    app.include_router(metrics.router)
    app.include_router(reports.router)
    app.include_router(vendors.router)

    @app.get("/health", response_model=HealthResponse, tags=["foundation"])
    def health() -> HealthResponse:
        return HealthResponse(status="ok", service="smarthome")

    return app


app = create_app()
