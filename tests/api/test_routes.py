import json
from pathlib import Path

import httpx
import pytest
import respx
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.session import Base, get_db
from app.database.seed_mappings import seed_team_mappings
from app.config import get_settings
from app.main import app as fastapi_app

FIXTURES = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("DISABLE_SCHEDULER", "true")
    get_settings.cache_clear()

    import app.models  # noqa: F401

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)

    setup_db = TestingSession()
    seed_team_mappings(setup_db)
    setup_db.close()

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    fastapi_app.dependency_overrides[get_db] = override_get_db

    football_payload = json.loads((FIXTURES / "football_matches.json").read_text())
    search_payload = json.loads((FIXTURES / "polymarket_search.json").read_text())

    with respx.mock:
        respx.get(url__regex=r".*/competitions/2000/matches.*").mock(
            return_value=httpx.Response(200, json=football_payload)
        )
        respx.get(url__regex=r".*/teams/.*/matches.*").mock(
            return_value=httpx.Response(200, json={"matches": []})
        )
        respx.get(url__regex=r".*/public-search.*").mock(
            return_value=httpx.Response(200, json=search_payload)
        )
        respx.get(url__regex=r".*/midpoint.*").mock(
            return_value=httpx.Response(200, json={"mid": "0.64"})
        )

        with TestClient(fastapi_app) as test_client:
            yield test_client

    fastapi_app.dependency_overrides.clear()
    get_settings.cache_clear()


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_list_matches(client):
    client.post("/api/admin/refresh")
    response = client.get("/api/matches")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_match_detail_not_found(client):
    response = client.get("/api/matches/999999")
    assert response.status_code == 404
