from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any
from uuid import uuid4

from fastapi import FastAPI

from shared.moneywise_common import (
    Goal,
    GoalCreateRequest,
    GoalUpdateRequest,
    Settings,
    monthly_required_saving,
    progress_pct,
)

settings = Settings(service_name="goal-service", service_port=8404)
app = FastAPI(title="MoneyWise Goal Service", version="1.0.0")

goals: dict[str, Goal] = {}


def _build_goal(request: GoalCreateRequest) -> Goal:
    monthly_required = monthly_required_saving(request.target_amount, request.start_amount, request.deadline)
    return Goal(
        goal_id=str(uuid4()),
        user_id=request.user_id,
        name=request.name,
        target_amount=request.target_amount,
        current_amount=request.start_amount,
        deadline=request.deadline,
        monthly_required=monthly_required,
        progress_pct=progress_pct(request.start_amount, request.target_amount),
    )


def _seed_demo() -> None:
    demo = GoalCreateRequest(
        user_id="USR-DEMO",
        name="Emergency fund",
        target_amount=300_000,
        deadline=date(datetime.now(UTC).year + 1, 12, 1),
        start_amount=92_000,
    )
    goal = _build_goal(demo)
    goal.goal_id = "GOAL-DEMO-1"
    goals[goal.goal_id] = goal


_seed_demo()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.post("/goals")
async def create_goal(request: GoalCreateRequest) -> dict[str, Any]:
    goal = _build_goal(request)
    goals[goal.goal_id] = goal
    return goal.model_dump(mode="json")


@app.get("/goals/{user_id}")
async def list_goals(user_id: str) -> dict[str, Any]:
    items = [goal.model_dump(mode="json") for goal in goals.values() if goal.user_id == user_id]
    return {"items": items, "count": len(items)}


@app.post("/goals/{user_id}/update")
async def update_goals(user_id: str, request: GoalUpdateRequest) -> dict[str, Any]:
    user_goals = [goal for goal in goals.values() if goal.user_id == user_id]
    if not user_goals:
        return {"items": [], "allocated": 0.0, "message": "No goals configured"}

    total_gap = sum(max(goal.target_amount - goal.current_amount, 0) for goal in user_goals)
    allocated = 0.0
    if request.monthly_free_cash > 0 and total_gap > 0:
        for goal in user_goals:
            gap = max(goal.target_amount - goal.current_amount, 0)
            if gap <= 0:
                continue
            share = request.monthly_free_cash * (gap / total_gap)
            deposit = min(share, gap)
            goal.current_amount = round(goal.current_amount + deposit, 2)
            allocated += deposit

    for goal in user_goals:
        goal.monthly_required = monthly_required_saving(goal.target_amount, goal.current_amount, goal.deadline)
        goal.progress_pct = progress_pct(goal.current_amount, goal.target_amount)

    return {
        "items": [goal.model_dump(mode="json") for goal in user_goals],
        "allocated": round(allocated, 2),
        "message": "Goals updated",
    }


@app.get("/goals/{user_id}/summary")
async def goal_summary(user_id: str) -> dict[str, Any]:
    user_goals = [goal for goal in goals.values() if goal.user_id == user_id]
    total_target = round(sum(goal.target_amount for goal in user_goals), 2)
    total_current = round(sum(goal.current_amount for goal in user_goals), 2)
    return {
        "user_id": user_id,
        "goals_count": len(user_goals),
        "total_target": total_target,
        "total_current": total_current,
        "total_progress_pct": progress_pct(total_current, total_target) if total_target else 0,
    }
