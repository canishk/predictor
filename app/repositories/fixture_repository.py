import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session, joinedload

from app.models import Fixture, Prediction, PredictionMarket, Team


class FixtureRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def upsert_fixture(
        self,
        match_data: dict,
        home_team: Team,
        away_team: Team,
        day_bucket: str,
    ) -> Fixture:
        match_id = match_data["id"]
        fixture = self.db.query(Fixture).filter(Fixture.match_id == match_id).first()
        if not fixture:
            fixture = Fixture(match_id=match_id)
            self.db.add(fixture)

        fixture.home_team_id = home_team.id
        fixture.away_team_id = away_team.id
        fixture.utc_date = datetime.fromisoformat(match_data["utcDate"].replace("Z", "+00:00"))
        fixture.status = match_data.get("status", "SCHEDULED")
        fixture.group_name = match_data.get("group")
        fixture.stage = match_data.get("stage")
        fixture.matchday = match_data.get("matchday")
        fixture.day_bucket = day_bucket
        self.db.flush()
        return fixture

    def list_today_tomorrow(self) -> list[Fixture]:
        return (
            self.db.query(Fixture)
            .options(joinedload(Fixture.home_team), joinedload(Fixture.away_team))
            .filter(Fixture.day_bucket.in_(["today", "tomorrow"]))
            .order_by(Fixture.utc_date)
            .all()
        )

    def get_by_id(self, match_id: int) -> Fixture | None:
        return (
            self.db.query(Fixture)
            .options(joinedload(Fixture.home_team), joinedload(Fixture.away_team))
            .filter(Fixture.match_id == match_id)
            .first()
        )


class PredictionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def save_market(self, fixture_id: int, market_payload: dict) -> PredictionMarket:
        existing = (
            self.db.query(PredictionMarket)
            .filter(PredictionMarket.fixture_id == fixture_id)
            .order_by(PredictionMarket.matched_at.desc())
            .first()
        )
        if existing:
            market = existing
        else:
            market = PredictionMarket(fixture_id=fixture_id)
            self.db.add(market)

        market.polymarket_event_id = market_payload.get("event_id")
        market.polymarket_market_id = market_payload.get("market_id")
        market.event_title = market_payload.get("event_title")
        market.market_question = market_payload.get("market_question")
        market.outcomes_json = json.dumps(market_payload.get("outcomes", []))
        market.clob_token_ids_json = json.dumps(market_payload.get("clob_token_ids", []))
        market.volume = market_payload.get("volume")
        market.liquidity = market_payload.get("liquidity")
        market.raw_json = json.dumps(market_payload.get("raw", {}))
        market.matched_at = datetime.now(timezone.utc)
        self.db.flush()
        return market

    def save_prediction(self, fixture_id: int, prediction_payload: dict) -> Prediction:
        prediction = Prediction(fixture_id=fixture_id)
        self.db.add(prediction)
        prediction.home_win_probability = prediction_payload.get("home_win_probability")
        prediction.away_win_probability = prediction_payload.get("away_win_probability")
        prediction.draw_probability = prediction_payload.get("draw_probability")
        prediction.goal_difference = prediction_payload.get("goal_difference")
        prediction.confidence = prediction_payload.get("confidence")
        prediction.winner = prediction_payload.get("winner")
        prediction.explanation_json = json.dumps(prediction_payload.get("explanation", {}))
        prediction.snapshot_at = datetime.now(timezone.utc)
        self.db.flush()
        return prediction

    def latest_for_fixture(self, fixture_id: int) -> Prediction | None:
        return (
            self.db.query(Prediction)
            .filter(Prediction.fixture_id == fixture_id)
            .order_by(Prediction.snapshot_at.desc())
            .first()
        )

    def latest_market_for_fixture(self, fixture_id: int) -> PredictionMarket | None:
        return (
            self.db.query(PredictionMarket)
            .filter(PredictionMarket.fixture_id == fixture_id)
            .order_by(PredictionMarket.matched_at.desc())
            .first()
        )
