from __future__ import annotations

from collections import Counter
import math
from statistics import fmean, pstdev
from typing import Hashable, Iterable, Sequence

from sql_tools import normalize_sql


def exact_match(predicted_sql: str, gold_sql: str) -> bool:
    return normalize_sql(predicted_sql) == normalize_sql(gold_sql)


def execution_match(
    predicted_rows: Sequence[Hashable],
    gold_rows: Sequence[Hashable],
    *,
    order_sensitive: bool = False,
    duplicate_sensitive: bool = False,
) -> bool:
    if order_sensitive:
        return list(predicted_rows) == list(gold_rows)
    if duplicate_sensitive:
        return Counter(predicted_rows) == Counter(gold_rows)
    return set(predicted_rows) == set(gold_rows)


def clean_abnormal_ratios(ratios: Iterable[float]) -> list[float]:
    values = [float(value) for value in ratios if value > 0 and math.isfinite(value)]
    if len(values) < 2:
        return values
    mean = fmean(values)
    deviation = pstdev(values)
    if deviation == 0:
        return values
    cleaned = [value for value in values if mean - 3 * deviation < value < mean + 3 * deviation]
    return cleaned or values


def rves_reward(time_ratio: float) -> float:
    if time_ratio <= 0:
        return 0.0
    if time_ratio >= 2:
        return 1.25
    if time_ratio >= 1:
        return 1.0
    if time_ratio >= 0.5:
        return 0.75
    if time_ratio >= 0.25:
        return 0.5
    return 0.25


def rves_score(reward: float) -> float:
    return math.sqrt(reward) * 100 if reward > 0 else 0.0

