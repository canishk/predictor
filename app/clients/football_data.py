from datetime import timedelta
import asyncio
from typing import Any

import httpx

from app.config import get_settings
from app.utils.cache import cache
from app.utils.dates import utc_today


class FootballDataClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Accept": "application/json"}
        if self.settings.football_data_api_key:
            headers["X-Auth-Token"] = self.settings.football_data_api_key
        return headers

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        cached = cache.get("football_data", path, params or {})
        if cached is not None:
            return cached

        url = f"{self.settings.football_data_base_url}{path}"
        retries = 5
        delay = 60.0

        async with httpx.AsyncClient(timeout=30.0) as client:
            for attempt in range(retries + 1):
                response = await client.get(url, headers=self._headers(), params=params)
                if response.status_code == 429:
                    if attempt == retries:
                        response.raise_for_status()

                    retry_after = response.headers.get("Retry-After")
                    if retry_after is not None:
                        try:
                            delay = float(retry_after)
                        except ValueError:
                            delay = 60.0

                    await asyncio.sleep(delay)
                    delay = min(delay * 2, 120.0)
                    continue

                response.raise_for_status()
                data = response.json()
                break

        cache.set("football_data", data, path, params or {})
        return data

    async def get_competition_matches(
        self,
        date_from,
        date_to,
    ) -> list[dict[str, Any]]:
        competition_id = self.settings.football_data_competition_id
        data = await self._get(
            f"/competitions/{competition_id}/matches",
            {
                "dateFrom": date_from.isoformat(),
                "dateTo": date_to.isoformat(),
            },
        )
        return data.get("matches", [])

    async def get_recent_window_matches(
        self,
    ) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
        today = utc_today()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)
        day_after = today + timedelta(days=2)
        lookback_start = today - timedelta(days=self.settings.football_data_form_lookback_days)

        all_matches = await self.get_competition_matches(lookback_start, day_after)
        buckets: dict[str, list[dict[str, Any]]] = {
            "yesterday": [],
            "today": [],
            "tomorrow": [],
        }

        for match in all_matches:
            utc_date = match.get("utcDate", "")[:10]
            if utc_date == yesterday.isoformat():
                buckets["yesterday"].append(match)
            elif utc_date == today.isoformat():
                buckets["today"].append(match)
            elif utc_date == tomorrow.isoformat():
                buckets["tomorrow"].append(match)

        return buckets, all_matches

    async def get_today_and_tomorrow_matches(
        self,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        buckets, all_matches = await self.get_recent_window_matches()
        return buckets["today"], buckets["tomorrow"], all_matches

    async def get_match(self, match_id: int) -> dict[str, Any]:
        return await self._get(f"/matches/{match_id}")

    async def get_team_matches(self, team_id: int, limit: int = 5) -> list[dict[str, Any]]:
        data = await self._get(
            f"/teams/{team_id}/matches",
            {"status": "FINISHED", "limit": limit},
        )
        return data.get("matches", [])
