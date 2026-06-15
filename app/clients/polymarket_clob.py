from typing import Any

import httpx

from app.config import get_settings
from app.utils.cache import cache


class PolymarketClobClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        cache_key_params = params or {}
        cached = cache.get("polymarket_clob", path, cache_key_params)
        if cached is not None:
            return cached

        url = f"{self.settings.polymarket_clob_base_url}{path}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        cache.set("polymarket_clob", data, path, cache_key_params)
        return data

    async def get_midpoint(self, token_id: str) -> float | None:
        try:
            data = await self._get("/midpoint", {"token_id": token_id})
            if isinstance(data, dict):
                mid = data.get("mid")
                return float(mid) if mid is not None else None
            return float(data)
        except (httpx.HTTPError, TypeError, ValueError):
            return None

    async def get_midpoints(self, token_ids: list[str]) -> dict[str, float]:
        results: dict[str, float] = {}
        for token_id in token_ids:
            mid = await self.get_midpoint(token_id)
            if mid is not None:
                results[token_id] = mid
        return results

    async def get_orderbook(self, token_id: str) -> dict[str, Any]:
        try:
            return await self._get("/book", {"token_id": token_id})
        except httpx.HTTPError:
            return {}

    async def get_price_history(self, token_id: str, interval: str = "1d") -> list[dict[str, Any]]:
        try:
            data = await self._get("/prices-history", {"market": token_id, "interval": interval})
            if isinstance(data, dict):
                return data.get("history", [])
            return data if isinstance(data, list) else []
        except httpx.HTTPError:
            return []
