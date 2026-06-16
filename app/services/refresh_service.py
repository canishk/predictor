from sqlalchemy.orm import Session

from app.clients.football_data import FootballDataClient
from app.clients.polymarket_clob import PolymarketClobClient
from app.clients.polymarket_gamma import PolymarketGammaClient
from app.repositories.fixture_repository import FixtureRepository, PredictionRepository
from app.repositories.team_mapping_repository import TeamMappingRepository, TeamRepository
from app.services.form_service import build_team_form_map, empty_form
from app.services.market_matcher import MarketMatcherService
from app.services.prediction_service import PredictionService
from app.utils.cache import cache


class RefreshService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.football = FootballDataClient()
        self.gamma = PolymarketGammaClient()
        self.clob = PolymarketClobClient()
        self.fixture_repo = FixtureRepository(db)
        self.prediction_repo = PredictionRepository(db)
        self.team_repo = TeamRepository(db)
        self.mapping_repo = TeamMappingRepository(db)
        self.market_matcher = MarketMatcherService(self.gamma, self.clob, self.mapping_repo)
        self.prediction_service = PredictionService()

    async def run(self) -> dict:
        cache.clear()
        buckets, all_matches = await self.football.get_recent_window_matches()
        form_map = build_team_form_map(all_matches)
        processed = 0

        for matches in buckets.values():
            for match_data in matches:
                await self._process_match(match_data, form_map)
                processed += 1

        self.db.commit()
        return {
            "processed": processed,
            "today": len(buckets["today"]),
            "tomorrow": len(buckets["tomorrow"]),
        }

    async def _process_match(
        self,
        match_data: dict,
        form_map: dict[int, dict],
    ) -> None:
        home_data = match_data["homeTeam"]
        away_data = match_data["awayTeam"]
        home_team = self.team_repo.upsert_team(home_data)
        away_team = self.team_repo.upsert_team(away_data)
        fixture = self.fixture_repo.upsert_fixture(match_data, home_team, away_team)

        market = await self.market_matcher.find_market(home_team.name, away_team.name)
        if market:
            self.prediction_repo.save_market(
                fixture.match_id,
                {
                    "event_id": market.event_id,
                    "market_id": market.market_id,
                    "event_title": market.event_title,
                    "market_question": market.market_question,
                    "outcomes": market.outcomes,
                    "clob_token_ids": market.clob_token_ids,
                    "volume": market.volume,
                    "liquidity": market.liquidity,
                    "raw": market.raw,
                },
            )

        home_form = form_map.get(home_data["id"], empty_form())
        away_form = form_map.get(away_data["id"], empty_form())

        prediction = self.prediction_service.build_prediction(
            home_team.name, away_team.name, market, home_form, away_form
        )
        self.prediction_repo.save_prediction(fixture.match_id, prediction)
