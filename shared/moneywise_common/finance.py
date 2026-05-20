from __future__ import annotations

from collections import defaultdict
from datetime import UTC, date, datetime
from math import sqrt

CATEGORY_KEYWORDS: dict[str, set[str]] = {
    "groceries": {"market", "grocery", "supermarket", "food", "pyaterochka", "magnit"},
    "transport": {"taxi", "metro", "fuel", "gas", "bus"},
    "housing": {"rent", "mortgage", "utilities", "electricity", "water"},
    "health": {"pharmacy", "doctor", "clinic", "medicine"},
    "entertainment": {"cinema", "streaming", "concert", "game"},
    "salary": {"salary", "payroll", "bonus"},
    "investment": {"broker", "dividend", "coupon", "bond"},
}


def normalize_category(category: str | None) -> str:
    if not category:
        return "other"
    return category.strip().lower().replace(" ", "_")


def auto_categorize(description: str, merchant: str | None = None) -> tuple[str, bool]:
    bag = f"{description} {merchant or ''}".lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in bag for keyword in keywords):
            return category, True
    return "other", False


def monthly_required_saving(
    target_amount: float,
    current_amount: float,
    deadline: date,
    today: date | None = None,
) -> float:
    reference = today or datetime.now(UTC).date()
    if deadline <= reference:
        return round(max(target_amount - current_amount, 0), 2)
    months = max((deadline.year - reference.year) * 12 + (deadline.month - reference.month), 1)
    remaining = max(target_amount - current_amount, 0)
    return round(remaining / months, 2)


def progress_pct(current_amount: float, target_amount: float) -> float:
    if target_amount <= 0:
        return 0.0
    return round(min(max(current_amount / target_amount, 0.0), 1.0) * 100, 2)


def position_market_value(quantity: float, current_price: float) -> float:
    return round(quantity * current_price, 2)


def position_cost_basis(quantity: float, average_price: float) -> float:
    return round(quantity * average_price, 2)


def position_return_pct(quantity: float, average_price: float, current_price: float) -> float:
    cost = position_cost_basis(quantity, average_price)
    if cost <= 0:
        return 0.0
    pnl = position_market_value(quantity, current_price) - cost
    return round((pnl / cost) * 100, 2)


def portfolio_volatility(returns: list[float]) -> float:
    if not returns:
        return 0.0
    avg = sum(returns) / len(returns)
    variance = sum((item - avg) ** 2 for item in returns) / len(returns)
    return round(sqrt(variance), 4)


def expense_forecast(monthly_expenses: list[float], seasonality_factor: float = 1.03) -> float:
    if not monthly_expenses:
        return 0.0
    recent = monthly_expenses[-6:]
    baseline = sum(recent) / len(recent)
    trend = 1.0
    if len(recent) >= 3 and recent[-1] > recent[0]:
        trend += 0.015
    return round(baseline * trend * seasonality_factor, 2)


def cashflow_by_month(transactions: list[dict]) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = defaultdict(lambda: {"income": 0.0, "expense": 0.0, "net": 0.0})
    for transaction in transactions:
        booked_at = transaction.get("booked_at")
        if isinstance(booked_at, str):
            month = booked_at[:7]
        else:
            month = str(booked_at)[:7]
        amount = float(transaction.get("amount", 0.0))
        tx_type = transaction.get("transaction_type")
        if tx_type == "income":
            result[month]["income"] += amount
        elif tx_type == "expense":
            result[month]["expense"] += amount
    for month in result:
        result[month]["income"] = round(result[month]["income"], 2)
        result[month]["expense"] = round(result[month]["expense"], 2)
        result[month]["net"] = round(result[month]["income"] - result[month]["expense"], 2)
    return dict(sorted(result.items(), key=lambda item: item[0]))


def category_breakdown(transactions: list[dict]) -> dict[str, float]:
    result: dict[str, float] = defaultdict(float)
    for transaction in transactions:
        if transaction.get("transaction_type") != "expense":
            continue
        result[str(transaction.get("category", "other"))] += float(transaction.get("amount", 0.0))
    return {
        category: round(amount, 2)
        for category, amount in sorted(result.items(), key=lambda item: item[1], reverse=True)
    }
