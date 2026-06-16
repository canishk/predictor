import json
from datetime import date
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
import respx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import Base
from app.database.seed_mappings import seed_team_mappings
from app.models import Fixture
from app.services.refresh_service import RefreshService

FIXTURES = Path(__file__).parent.parent / "fixtures"
FIXED_TODAY = date(2026, 6, 16)


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    seed_team_mappings(session)
    yield session
    session.close()


@respx.mock
@pytest.mark.asyncio
async def test_football_data_client_matches():
    from app.clients.football_data import FootballDataClient

    payload = json.loads((FIXTURES / "football_matches.json").read_text())
    respx.get(url__regex=r".*/competitions/2000/matches.*").mock(
        return_value=httpx.Response(200, json=payload)
    )

    client = FootballDataClient()
    matches = await client.get_competition_matches(
        __import__("datetime").date(2026, 6, 15),
        __import__("datetime").date(2026, 6, 17),
    )
    assert len(matches) == 4
    assert matches[0]["homeTeam"]["name"] == "Argentina"


@respx.mock
@pytest.mark.asyncio
async def test_get_team_matches_uses_finished_status():
    from app.clients.football_data import FootballDataClient

    route = respx.get(url__regex=r".*/teams/773/matches.*").mock(
        return_value=httpx.Response(200, json={"matches": []})
    )

    client = FootballDataClient()
    await client.get_team_matches(773)

    assert route.calls.last.request.url.params["status"] == "FINISHED"


@respx.mock
@pytest.mark.asyncio
async def test_football_data_client_retries_on_rate_limit():
    from app.clients.football_data import FootballDataClient
    from app.utils.cache import cache

    cache.clear()

    respx.get(url__regex=r".*/teams/.*/matches.*").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "0"}),
            httpx.Response(200, json={"matches": [{"id": 1}]}),
        ]
    )

    client = FootballDataClient()
    matches = await client.get_team_matches(773)
    assert len(matches) == 1
    assert matches[0]["id"] == 1


@respx.mock
@pytest.mark.asyncio
@patch("app.clients.football_data.utc_today", return_value=FIXED_TODAY)
@patch("app.utils.dates.utc_today", return_value=FIXED_TODAY)
async def test_refresh_service_pipeline(_mock_dates, _mock_client, db_session):
    football_payload = json.loads((FIXTURES / "football_matches.json").read_text())
    search_payload = json.loads((FIXTURES / "polymarket_search.json").read_text())

    competition_route = respx.get(url__regex=r".*/competitions/2000/matches.*").mock(
        return_value=httpx.Response(200, json=football_payload)
    )
    respx.get(url__regex=r".*/public-search.*").mock(
        return_value=httpx.Response(200, json=search_payload)
    )
    respx.get(url__regex=r".*/midpoint.*").mock(
        return_value=httpx.Response(200, json={"mid": "0.64"})
    )

    service = RefreshService(db_session)
    result = await service.run()
    assert result["processed"] >= 1
    assert len(competition_route.calls) == 1

    finished = db_session.query(Fixture).filter(Fixture.match_id == 500002).one()
    assert finished.status == "FINISHED"
    assert finished.home_score == 2
    assert finished.away_score == 1
    assert finished.day_bucket == "yesterday"
