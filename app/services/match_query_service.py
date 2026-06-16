import json

import httpx
from sqlalchemy.orm import Session

from app.clients.football_data import FootballDataClient
from app.repositories.fixture_repository import FixtureRepository, PredictionRepository
from app.schemas.match import (
    FixtureSchema,
    MarketDataSchema,
    MatchDetailResponse,
    MatchSummary,
    PredictionDetailSchema,
    TeamFormSchema,
)
from app.services.form_service import compute_form, empty_form


class MatchQueryService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.fixture_repo = FixtureRepository(db)
        self.prediction_repo = PredictionRepository(db)
        self.football = FootballDataClient()

    def list_matches(self) -> list[MatchSummary]:
        fixtures = self.fixture_repo.list_today_tomorrow()
        results: list[MatchSummary] = []
        for fixture in fixtures:
            prediction = self.prediction_repo.latest_for_fixture(fixture.match_id)
            results.append(
                MatchSummary(
                    match_id=fixture.match_id,
                    home_team=fixture.home_team.name,
                    away_team=fixture.away_team.name,
                    kickoff=fixture.utc_date,
                    status=fixture.status,
                    day_bucket=fixture.day_bucket,
                    home_score=fixture.home_score,
                    away_score=fixture.away_score,
                    winner_prediction=prediction.winner if prediction else None,
                    home_win_probability=prediction.home_win_probability if prediction else None,
                    away_win_probability=prediction.away_win_probability if prediction else None,
                    goal_difference=prediction.goal_difference if prediction else None,
                    confidence=prediction.confidence if prediction else None,
                )
            )
        return results

    async def get_match_detail(self, match_id: int) -> MatchDetailResponse | None:
        fixture = self.fixture_repo.get_by_id(match_id)
        if not fixture:
            return None

        prediction = self.prediction_repo.latest_for_fixture(match_id)
        market = self.prediction_repo.latest_market_for_fixture(match_id)

        home_form = await self._fetch_team_form(fixture.home_team.football_data_id)
        away_form = await self._fetch_team_form(fixture.away_team.football_data_id)

        explanation = {}
        if prediction and prediction.explanation_json:
            explanation = json.loads(prediction.explanation_json)

        outcomes = []
        if market and market.outcomes_json:
            outcomes = json.loads(market.outcomes_json)

        return MatchDetailResponse(
            fixture=FixtureSchema(
                match_id=fixture.match_id,
                home_team=fixture.home_team.name,
                away_team=fixture.away_team.name,
                kickoff=fixture.utc_date,
                status=fixture.status,
                group=fixture.group_name,
                stage=fixture.stage,
                matchday=fixture.matchday,
                day_bucket=fixture.day_bucket,
                home_score=fixture.home_score,
                away_score=fixture.away_score,
            ),
            prediction=PredictionDetailSchema(
                winner=prediction.winner if prediction else None,
                home_win_probability=prediction.home_win_probability if prediction else None,
                away_win_probability=prediction.away_win_probability if prediction else None,
                draw_probability=prediction.draw_probability if prediction else None,
                goal_difference=prediction.goal_difference if prediction else None,
                confidence=prediction.confidence if prediction else None,
                explanation=explanation,
            ),
            recent_form={
                "home": TeamFormSchema(**home_form),
                "away": TeamFormSchema(**away_form),
            },
            market_data=MarketDataSchema(
                event_title=market.event_title if market else None,
                market_question=market.market_question if market else None,
                outcomes=outcomes,
                volume=market.volume if market else None,
                liquidity=market.liquidity if market else None,
                draw_probability=prediction.draw_probability if prediction else None,
            ),
        )

    async def _fetch_team_form(self, team_id: int) -> dict:
        try:
            matches = await self.football.get_team_matches(team_id)
            return compute_form(matches, team_id)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                return empty_form()
            raise
