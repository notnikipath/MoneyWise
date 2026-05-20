from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import FastAPI

from shared.moneywise_common import Budget, BudgetAlert, BudgetCheckRequest, BudgetCreateRequest, Settings

settings = Settings(service_name="budget-service", service_port=8403)
app = FastAPI(title="MoneyWise Budget Service", version="1.0.0")

budgets: dict[str, Budget] = {}
alerts: list[BudgetAlert] = []


def _seed_demo() -> None:
    demo = Budget(
        budget_id="BUD-DEMO-1",
        user_id="USR-DEMO",
        category="groceries",
        limit_amount=25_000,
        spent_amount=16_500,
        month=datetime.now(UTC).strftime("%Y-%m"),
    )
    budgets[demo.budget_id] = demo


_seed_demo()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.post("/budgets")
async def create_budget(request: BudgetCreateRequest) -> dict[str, Any]:
    budget = Budget(
        budget_id=str(uuid4()),
        user_id=request.user_id,
        category=request.category.lower(),
        limit_amount=request.limit_amount,
        month=request.month,
    )
    budgets[budget.budget_id] = budget
    return budget.model_dump(mode="json")


@app.get("/budgets")
async def list_budgets(user_id: str | None = None, month: str | None = None) -> dict[str, Any]:
    items = []
    for budget in budgets.values():
        if user_id and budget.user_id != user_id:
            continue
        if month and budget.month != month:
            continue
        items.append(budget.model_dump(mode="json"))
    return {"items": items, "count": len(items)}


@app.post("/budgets/check")
async def check_budget(request: BudgetCheckRequest) -> dict[str, Any]:
    matched = [
        budget
        for budget in budgets.values()
        if (
            budget.user_id == request.user_id
            and budget.category == request.category.lower()
            and budget.month == request.month
        )
    ]
    if not matched:
        return {
            "matched": False,
            "alerts": [],
            "spent_amount": 0,
            "remaining": None,
            "message": "No configured budget for category/month",
        }

    budget = matched[0]
    budget.spent_amount = round(budget.spent_amount + request.amount, 2)
    remaining = round(budget.limit_amount - budget.spent_amount, 2)
    triggered: list[dict[str, Any]] = []

    if budget.spent_amount > budget.limit_amount:
        alert = BudgetAlert(
            alert_id=str(uuid4()),
            user_id=budget.user_id,
            category=budget.category,
            month=budget.month,
            limit_amount=budget.limit_amount,
            spent_amount=budget.spent_amount,
            over_by=round(budget.spent_amount - budget.limit_amount, 2),
        )
        alerts.append(alert)
        triggered.append(alert.model_dump(mode="json"))

    return {
        "matched": True,
        "budget": budget.model_dump(mode="json"),
        "alerts": triggered,
        "spent_amount": budget.spent_amount,
        "remaining": remaining,
    }


@app.get("/budgets/alerts")
async def list_alerts(user_id: str | None = None, limit: int = 30) -> dict[str, Any]:
    items = [alert.model_dump(mode="json") for alert in alerts if not user_id or alert.user_id == user_id]
    return {"items": items[-limit:], "count": len(items)}
