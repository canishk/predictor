from datetime import date, datetime, timezone
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import Base
from app.database.seed_mappings import seed_team_mappings
from app.models import Fixture, Team
from app.repositories.fixture_repository import FixtureRepository
from app.utils.dates import compute_day_bucket


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


def _team(session, fd_id: int, name: str) -> Team:
    team = Team(football_data_id=fd_id, name=name, short_name=name)
    session.add(team)
    session.flush()
    return team


def _match_payload(
    match_id: int,
    utc_date: str,
    status: str,
    home_id: int,
    home_name: str,
    away_id: int,
    away_name: str,
    home_score: int | None = None,
    away_score: int | None = None,
) -> dict:
    payload: dict = {
        "id": match_id,
        "utcDate": utc_date,
        "status": status,
        "matchday": 1,
        "stage": "GROUP_STAGE",
        "group": "GROUP_A",
        "homeTeam": {"id": home_id, "name": home_name, "shortName": home_name, "tla": "HOM"},
        "awayTeam": {"id": away_id, "name": away_name, "shortName": away_name, "tla": "AWY"},
    }
    if home_score is not None and away_score is not None:
        payload["score"] = {"fullTime": {"home": home_score, "away": away_score}}
    return payload


@patch("app.utils.dates.utc_today", return_value=FIXED_TODAY)
def test_compute_day_bucket_uses_utc(_mock_today):
    kickoff = datetime(2026, 6, 15, 22, 0, tzinfo=timezone.utc)
    assert compute_day_bucket(kickoff) == "yesterday"

    kickoff_today = datetime(2026, 6, 16, 19, 0, tzinfo=timezone.utc)
    assert compute_day_bucket(kickoff_today) == "today"

    kickoff_tomorrow = datetime(2026, 6, 17, 20, 0, tzinfo=timezone.utc)
    assert compute_day_bucket(kickoff_tomorrow) == "tomorrow"


@patch("app.utils.dates.utc_today", return_value=FIXED_TODAY)
def test_upsert_updates_status_and_scores(_mock_dates_today, db_session):
    repo = FixtureRepository(db_session)
    home = _team(db_session, 1, "Home FC")
    away = _team(db_session, 2, "Away FC")

    in_play = _match_payload(9001, "2026-06-16T19:00:00Z", "IN_PLAY", 1, "Home FC", 2, "Away FC")
    repo.upsert_fixture(in_play, home, away)
    db_session.commit()

    finished = _match_payload(
        9001, "2026-06-16T19:00:00Z", "FINISHED", 1, "Home FC", 2, "Away FC", 3, 1
    )
    repo.upsert_fixture(finished, home, away)
    db_session.commit()

    fixture = db_session.query(Fixture).filter(Fixture.match_id == 9001).one()
    assert fixture.status == "FINISHED"
    assert fixture.home_score == 3
    assert fixture.away_score == 1
    assert fixture.day_bucket == "today"


@patch("app.utils.dates.utc_today", return_value=FIXED_TODAY)
def test_yesterday_match_gets_yesterday_bucket(_mock_dates_today, db_session):
    repo = FixtureRepository(db_session)
    home = _team(db_session, 3, "France")
    away = _team(db_session, 4, "Germany")

    match = _match_payload(
        9002, "2026-06-15T22:00:00Z", "FINISHED", 3, "France", 4, "Germany", 2, 1
    )
    repo.upsert_fixture(match, home, away)
    db_session.commit()

    fixture = db_session.query(Fixture).filter(Fixture.match_id == 9002).one()
    assert fixture.day_bucket == "yesterday"


@patch("app.utils.dates.utc_today", return_value=FIXED_TODAY)
def test_list_includes_yesterday_kickoff(_mock_dates_today, db_session):
    repo = FixtureRepository(db_session)
    home = _team(db_session, 7, "Spain")
    away = _team(db_session, 8, "Italy")

    match = _match_payload(
        9005, "2026-06-15T22:00:00Z", "FINISHED", 7, "Spain", 8, "Italy", 2, 0
    )
    repo.upsert_fixture(match, home, away)
    db_session.commit()

    listed = repo.list_today_tomorrow()
    match_ids = {f.match_id for f in listed}

    assert 9005 in match_ids


@patch("app.utils.dates.utc_today", return_value=FIXED_TODAY)
def test_list_excludes_stale_day_bucket_with_old_kickoff(_mock_dates_today, db_session):
    repo = FixtureRepository(db_session)
    home = _team(db_session, 5, "Old Home")
    away = _team(db_session, 6, "Old Away")

    stale = Fixture(
        match_id=9003,
        home_team_id=home.id,
        away_team_id=away.id,
        utc_date=datetime(2026, 6, 13, 19, 0, tzinfo=timezone.utc),
        status="FINISHED",
        day_bucket="today",
        home_score=1,
        away_score=0,
    )
    db_session.add(stale)

    current = _match_payload(9004, "2026-06-16T19:00:00Z", "TIMED", 5, "Old Home", 6, "Old Away")
    repo.upsert_fixture(current, home, away)
    db_session.commit()

    listed = repo.list_today_tomorrow()
    match_ids = {f.match_id for f in listed}

    assert 9003 not in match_ids
    assert 9004 in match_ids
