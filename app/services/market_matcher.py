from dataclasses import dataclass
from typing import Any

from rapidfuzz import fuzz

from app.clients.polymarket_clob import PolymarketClobClient
from app.clients.polymarket_gamma import PolymarketGammaClient
from app.repositories.team_mapping_repository import TeamMappingRepository
from app.utils import normalize_probabilities


@dataclass
class MatchedMarket:
    event_id: str | None
    market_id: str
    event_title: str
    market_question: str
    home_win_probability: float
    away_win_probability: float
    draw_probability: float | None
    outcomes: list[dict[str, Any]]
    clob_token_ids: list[str]
    volume: float
    liquidity: float
    raw: dict[str, Any]


class MarketMatcherService:
    def __init__(
        self,
        gamma: PolymarketGammaClient,
        clob: PolymarketClobClient,
        mapping_repo: TeamMappingRepository,
    ) -> None:
        self.gamma = gamma
        self.clob = clob
        self.mapping_repo = mapping_repo

    def _names_in_text(self, text: str, names: list[str]) -> bool:
        text_lower = text.lower()
        return any(name.lower() in text_lower for name in names)

    def _score_event(self, event: dict[str, Any], home_names: list[str], away_names: list[str]) -> float:
        title = event.get("title") or ""
        if not self._names_in_text(title, home_names) or not self._names_in_text(title, away_names):
            return 0.0

        score = 50.0
        score += float(event.get("volume") or 0) / 10000
        score += float(event.get("liquidity") or 0) / 10000
        if event.get("active", True):
            score += 10
        return score

    def _map_outcomes(
        self,
        outcomes: list[str],
        prices: list[float],
        home_team: str,
        away_team: str,
    ) -> tuple[float, float, float | None, list[dict[str, Any]]]:
        home_names = self.mapping_repo.all_search_names(home_team)
        away_names = self.mapping_repo.all_search_names(away_team)

        home_prob = 0.0
        away_prob = 0.0
        draw_prob: float | None = None
        mapped: list[dict[str, Any]] = []

        for i, outcome in enumerate(outcomes):
            price = prices[i] if i < len(prices) else 0.0
            label = str(outcome)
            mapped.append({"label": label, "probability": price})

            label_lower = label.lower()
            if "draw" in label_lower or label_lower in {"tie", "x"}:
                draw_prob = price
                continue

            home_score = max(fuzz.partial_ratio(label_lower, n.lower()) for n in home_names)
            away_score = max(fuzz.partial_ratio(label_lower, n.lower()) for n in away_names)

            if home_score >= away_score and home_score >= 60:
                home_prob = price
            elif away_score > home_score and away_score >= 60:
                away_prob = price

        if home_prob == 0 and away_prob == 0 and len(prices) == 2:
            home_prob, away_prob = prices[0], prices[1]

        if draw_prob is not None:
            home_prob, away_prob = normalize_probabilities(home_prob, away_prob)
        else:
            home_prob, away_prob = normalize_probabilities(home_prob, away_prob)

        return home_prob, away_prob, draw_prob, mapped

    async def find_market(self, home_team: str, away_team: str) -> MatchedMarket | None:
        home_names = self.mapping_repo.all_search_names(home_team)
        away_names = self.mapping_repo.all_search_names(away_team)

        queries = [
            f"{home_team} vs {away_team}",
            f"{away_team} vs {home_team}",
            f"{home_names[0]} {away_names[0]}",
        ]

        best_event: dict[str, Any] | None = None
        best_score = 0.0

        for query in queries:
            search = await self.gamma.public_search(query)
            events = search.get("events") or []
            for event in events:
                score = self._score_event(event, home_names, away_names)
                if score > best_score:
                    best_score = score
                    best_event = event

        if not best_event or best_score <= 0:
            return None

        markets = best_event.get("markets") or []
        if not markets:
            return None

        best_market = max(
            markets,
            key=lambda m: float(m.get("volume") or m.get("volumeNum") or 0),
        )
        parsed = self.gamma.parse_market_fields(best_market)

        prices = list(parsed["outcome_prices"])
        if parsed["clob_token_ids"]:
            mids = await self.clob.get_midpoints([str(t) for t in parsed["clob_token_ids"]])
            if mids:
                prices = [mids.get(str(tid), prices[i] if i < len(prices) else 0.0)
                          for i, tid in enumerate(parsed["clob_token_ids"])]

        home_prob, away_prob, draw_prob, mapped_outcomes = self._map_outcomes(
            parsed["outcomes"], prices, home_team, away_team
        )

        return MatchedMarket(
            event_id=str(best_event.get("id", "")),
            market_id=parsed["market_id"],
            event_title=best_event.get("title") or "",
            market_question=parsed["question"],
            home_win_probability=home_prob,
            away_win_probability=away_prob,
            draw_probability=draw_prob,
            outcomes=mapped_outcomes,
            clob_token_ids=[str(t) for t in parsed["clob_token_ids"]],
            volume=parsed["volume"],
            liquidity=parsed["liquidity"],
            raw={"event": best_event, "market": parsed["raw"]},
        )
