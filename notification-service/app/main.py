from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel

from shared.moneywise_common import NotificationChannel, NotificationRequest, Settings, Severity

settings = Settings(service_name="notification-service", service_port=8407)
app = FastAPI(title="MoneyWise Notification Service", version="1.0.0")

messages: list[dict[str, Any]] = []


class BudgetExceededRequest(BaseModel):
    user_id: str
    category: str
    month: str
    spent_amount: float
    limit_amount: float


BudgetExceededRequest.model_rebuild()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.post("/notify/send")
async def send_notification(request: NotificationRequest) -> dict[str, Any]:
    payload = {
        "notification_id": str(uuid4()),
        **request.model_dump(mode="json"),
        "status": "queued",
        "created_at": datetime.now(UTC).isoformat(),
    }
    messages.append(payload)
    return payload


@app.post("/notify/budget-exceeded")
async def notify_budget_exceeded(request: BudgetExceededRequest) -> dict[str, Any]:
    payload = {
        "notification_id": str(uuid4()),
        "user_id": request.user_id,
        "channel": NotificationChannel.PUSH.value,
        "subject": f"Budget exceeded: {request.category}",
        "body": (
            f"Category {request.category} for {request.month} exceeded by "
            f"{round(request.spent_amount - request.limit_amount, 2)}"
        ),
        "severity": Severity.WARNING.value,
        "status": "queued",
        "created_at": datetime.now(UTC).isoformat(),
    }
    messages.append(payload)
    return payload


@app.get("/notify/history")
async def history(user_id: str | None = None, limit: int = 50) -> dict[str, Any]:
    items = [item for item in messages if not user_id or item["user_id"] == user_id]
    return {"items": items[-limit:], "count": len(items)}
