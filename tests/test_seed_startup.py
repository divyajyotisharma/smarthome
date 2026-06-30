from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.config import Settings
from app.db import create_tables
from app.main import create_app
from app.models import Appliance, Home, MetricReading
from app.services.seed import seed_demo_data


def test_seed_demo_data_is_idempotent(tmp_path):
    db_path = tmp_path / "smarthome-test.db"
    settings = Settings(database_url=f"sqlite:///{db_path}")
    engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
    session_factory = sessionmaker(bind=engine)

    create_tables(engine)

    with session_factory() as session:
        seed_demo_data(session, settings)
        seed_demo_data(session, settings)

        homes = session.scalars(select(Home)).all()
        appliances = session.scalars(select(Appliance)).all()
        readings = session.scalars(select(MetricReading)).all()

    assert len(homes) == 1
    assert homes[0].id == settings.default_home_id
    assert homes[0].name == "Demo Home"
    assert len(appliances) == 3
    assert len(readings) == 6


def test_startup_seeds_default_home_and_exposes_it(tmp_path):
    db_path = tmp_path / "api-smarthome-test.db"
    settings = Settings(database_url=f"sqlite:///{db_path}")
    app = create_app(settings)

    with TestClient(app) as client:
        response = client.get(f"/homes/{settings.default_home_id}")

    assert response.status_code == 200
    assert response.json()["id"] == settings.default_home_id
    assert response.json()["name"] == "Demo Home"
    assert "created_at" in response.json()
