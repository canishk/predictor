import json
from typing import Any

import httpx

from app.config import get_settings
from app.utils import parse_json_field
from app.utils.cache import cache


class PolymarketGammaClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        cache_key_params = params or {}
        cached = cache.get("polymarket_gamma", path, cache_key_params)
        if cached is not None:
            return cached

        url = f"{self.settings.polymarket_gamma_base_url}{path}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        cache.set("polymarket_gamma", data, path, cache_key_params)
        return data

    async def get_sports(self) -> list[dict[str, Any]]:
        data = await self._get("/sports")
        return data if isinstance(data, list) else []

    async def public_search(self, query: str, limit_per_type: int = 10) -> dict[str, Any]:
        return await self._get(
            "/public-search",
            {"q": query, "limit_per_type": limit_per_type, "search_profiles": False},
        )

    async def get_event(self, event_id: str) -> dict[str, Any]:
        return await self._get(f"/events/{event_id}")

    async def get_market(self, market_id: str) -> dict[str, Any]:
        return await self._get(f"/markets/{market_id}")

    async def get_tags(self) -> list[dict[str, Any]]:
        data = await self._get("/tags")
        return data if isinstance(data, list) else []

    @staticmethod
    def parse_market_fields(market: dict[str, Any]) -> dict[str, Any]:
        outcomes = parse_json_field(market.get("outcomes")) or []
        outcome_prices = parse_json_field(market.get("outcomePrices")) or []
        clob_token_ids = parse_json_field(market.get("clobTokenIds")) or []

        prices: list[float] = []
        for price in outcome_prices:
            try:
                prices.append(float(price))
            except (TypeError, ValueError):
                prices.append(0.0)

        return {
            "outcomes": outcomes if isinstance(outcomes, list) else [],
            "outcome_prices": prices,
            "clob_token_ids": clob_token_ids if isinstance(clob_token_ids, list) else [],
            "volume": float(market.get("volume") or market.get("volumeNum") or 0),
            "liquidity": float(market.get("liquidity") or market.get("liquidityNum") or 0),
            "question": market.get("question") or market.get("title") or "",
            "market_id": str(market.get("id", "")),
            "closed": bool(market.get("closed")),
            "active": bool(market.get("active", True)),
            "raw": market,
        }
