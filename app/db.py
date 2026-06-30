"""SQLAlchemy engine, session, and table setup for the SmartHome app."""

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings, settings
from app.models import Base


def create_engine_for_settings(app_settings: Settings) -> Engine:
    """Build an engine and ensure SQLite paths exist for local runs."""

    if app_settings.database_url.startswith("sqlite:///"):
        db_path = Path(app_settings.database_url.removeprefix("sqlite:///"))
        if db_path.parent != Path("."):
            db_path.parent.mkdir(parents=True, exist_ok=True)
        return create_engine(app_settings.database_url, connect_args={"check_same_thread": False})

    return create_engine(app_settings.database_url)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create the session factory used by request handlers and jobs."""

    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def create_tables(engine: Engine) -> None:
    """Create all declared tables if they are missing."""

    Base.metadata.create_all(bind=engine)


engine = create_engine_for_settings(settings)
SessionLocal = create_session_factory(engine)


def get_session() -> Generator[Session]:
    """Yield a request-scoped database session."""

    with SessionLocal() as session:
        yield session
