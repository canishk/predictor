import pytest

from app.clients.polymarket_gamma import PolymarketGammaClient


def test_parse_market_fields_string_json():
    market = {
        "id": "1",
        "question": "Who wins?",
        "outcomes": '["Team A", "Team B"]',
        "outcomePrices": '["0.6", "0.4"]',
        "clobTokenIds": '["t1", "t2"]',
        "volume": "1000",
        "liquidity": "500",
    }
    parsed = PolymarketGammaClient.parse_market_fields(market)
    assert parsed["outcomes"] == ["Team A", "Team B"]
    assert parsed["outcome_prices"] == [0.6, 0.4]
    assert parsed["clob_token_ids"] == ["t1", "t2"]
