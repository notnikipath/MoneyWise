from __future__ import annotations

from statistics import mean


def categorization_accuracy(predicted: list[str], actual: list[str]) -> float:
    if not predicted or not actual or len(predicted) != len(actual):
        return 0.0
    correct = 0
    for pred, real in zip(predicted, actual, strict=True):
        if pred == real:
            correct += 1
    return round(correct / len(actual) * 100, 2)


def report_load_seconds(cache_hit_ratio: float, row_count: int) -> float:
    safe_hit_ratio = min(max(cache_hit_ratio, 0.0), 1.0)
    cpu_penalty = min(row_count / 400_000, 1.8)
    estimate = 3.9 - safe_hit_ratio * 1.4 + cpu_penalty
    return round(max(0.45, estimate), 2)


def transactions_per_second(tx_per_day: int) -> float:
    if tx_per_day <= 0:
        return 0.0
    return round(tx_per_day / 86_400, 2)


def mean_return(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(mean(values), 2)


def projected_savings_rate(income: float, expenses: float) -> float:
    if income <= 0:
        return 0.0
    return round(max((income - expenses) / income, -1.0) * 100, 2)
