from typing import Any

from app.services.market_matcher import MatchedMarket
from app.utils.confidence import compute_confidence, goal_difference_from_ratio


class PredictionService:
    def build_prediction(
        self,
        home_team: str,
        away_team: str,
        market: MatchedMarket | None,
        home_form: dict[str, Any],
        away_form: dict[str, Any],
    ) -> dict[str, Any]:
        if market is None:
            return {
                "home_win_probability": None,
                "away_win_probability": None,
                "draw_probability": None,
                "goal_difference": None,
                "confidence": 15,
                "winner": None,
                "explanation": {
                    "summary": "No Polymarket market matched for this fixture.",
                    "factors": [],
                },
            }

        home_prob = market.home_win_probability
        away_prob = market.away_win_probability
        strength_ratio = home_prob / max(away_prob, 1e-6)
        base_gd = goal_difference_from_ratio(strength_ratio)

        form_diff = home_form.get("avg_goal_difference", 0) - away_form.get("avg_goal_difference", 0)
        if form_diff > 0.5 and base_gd < 3:
            base_gd = min(3, base_gd + 1)
        elif form_diff < -0.5 and base_gd > 0:
            base_gd = max(0, base_gd - 1)

        winner = home_team if home_prob >= away_prob else away_team
        combined_form = home_form.get("results", []) + away_form.get("results", [])
        confidence = compute_confidence(
            home_prob,
            away_prob,
            market.liquidity,
            market.volume,
            combined_form,
            has_market=True,
        )

        spread_pct = round(abs(home_prob - away_prob) * 100, 1)
        explanation = {
            "summary": (
                f"{winner} favored with {max(home_prob, away_prob) * 100:.1f}% implied win probability. "
                f"Expected margin: {base_gd} goal(s). Confidence {confidence}/100."
            ),
            "factors": [
                {"name": "Market probability spread", "value": f"{spread_pct}%", "impact": "high" if spread_pct > 30 else "low"},
                {"name": "Market volume", "value": f"${market.volume:,.0f}", "impact": "medium"},
                {"name": "Market liquidity", "value": f"${market.liquidity:,.0f}", "impact": "medium"},
                {"name": "Home recent form", "value": "-".join(home_form.get("results", [])) or "N/A", "impact": "medium"},
                {"name": "Away recent form", "value": "-".join(away_form.get("results", [])) or "N/A", "impact": "medium"},
            ],
        }

        return {
            "home_win_probability": round(home_prob, 4),
            "away_win_probability": round(away_prob, 4),
            "draw_probability": round(market.draw_probability, 4) if market.draw_probability else None,
            "goal_difference": base_gd,
            "confidence": confidence,
            "winner": winner,
            "explanation": explanation,
        }
