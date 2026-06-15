import json
import math
from typing import Any


def parse_json_field(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (list, dict)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def log_scale(value: float | None, threshold: float = 10000.0) -> float:
    if value is None or value <= 0:
        return 0.0
    return min(100.0, (math.log10(value + 1) / math.log10(threshold + 1)) * 100)


def normalize_probabilities(home: float, away: float) -> tuple[float, float]:
    total = home + away
    if total <= 0:
        return 0.5, 0.5
    return home / total, away / total
