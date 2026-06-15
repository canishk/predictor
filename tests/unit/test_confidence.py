import pytest

from app.utils import normalize_probabilities
from app.utils.confidence import compute_confidence, form_consistency_score, goal_difference_from_ratio


@pytest.mark.parametrize(
    "ratio,expected",
    [
        (0.1, 0),
        (0.3, 1),
        (0.5, 2),
        (0.8, 3),
    ],
)
def test_goal_difference_from_ratio(ratio, expected):
    assert goal_difference_from_ratio(ratio) == expected


def test_normalize_probabilities():
    home, away = normalize_probabilities(0.6, 0.4)
    assert home == pytest.approx(0.6)
    assert away == pytest.approx(0.4)


def test_normalize_probabilities_zero_sum():
    home, away = normalize_probabilities(0.0, 0.0)
    assert home == 0.5
    assert away == 0.5


def test_form_consistency_uniform():
    assert form_consistency_score(["W", "W", "W", "W", "W"]) > form_consistency_score(["W", "L", "W", "L", "W"])


def test_confidence_high_spread():
    score = compute_confidence(0.85, 0.15, 50000, 50000, ["W", "W", "D"], has_market=True)
    assert score >= 60


def test_confidence_no_market():
    assert compute_confidence(0.5, 0.5, None, None, [], has_market=False) == 15
