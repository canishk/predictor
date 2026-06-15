from app.utils import log_scale, normalize_probabilities

__all__ = ["compute_confidence", "goal_difference_from_ratio", "form_consistency_score"]


def goal_difference_from_ratio(strength_ratio: float) -> int:
    if strength_ratio < 0.2:
        return 0
    if strength_ratio < 0.4:
        return 1
    if strength_ratio < 0.7:
        return 2
    return 3


def form_consistency_score(recent_results: list[str]) -> float:
    if not recent_results:
        return 50.0
    points_map = {"W": 3, "D": 1, "L": 0}
    points = [points_map.get(r.upper(), 1) for r in recent_results]
    if len(points) == 1:
        return 80.0
    mean = sum(points) / len(points)
    variance = sum((p - mean) ** 2 for p in points) / len(points)
    return max(0.0, min(100.0, 100.0 - variance * 20))


def compute_confidence(
    home_prob: float,
    away_prob: float,
    liquidity: float | None,
    volume: float | None,
    form_results: list[str],
    has_market: bool = True,
) -> int:
    if not has_market:
        return 15

    spread = abs(home_prob - away_prob) * 100
    liquidity_score = log_scale(liquidity)
    volume_score = log_scale(volume)
    form_score = form_consistency_score(form_results)

    raw = 0.4 * spread + 0.2 * liquidity_score + 0.2 * volume_score + 0.2 * form_score
    return int(max(0, min(100, round(raw))))
