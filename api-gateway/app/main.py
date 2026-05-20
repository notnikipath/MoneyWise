from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from shared.moneywise_common import (
    AddTransactionWorkflowResult,
    Role,
    Settings,
    TransactionType,
    sign_token,
    verify_token,
)


class GatewaySettings(BaseSettings):
    service_name: str = "api-gateway"
    service_port: int = 8400

    account_service_url: str = "http://account-service:8401"
    transaction_service_url: str = "http://transaction-service:8402"
    budget_service_url: str = "http://budget-service:8403"
    goal_service_url: str = "http://goal-service:8404"
    investment_service_url: str = "http://investment-service:8405"
    analytics_service_url: str = "http://analytics-service:8406"
    notification_service_url: str = "http://notification-service:8407"

    jwt_secret: str = Settings().jwt_secret
    token_exp_minutes: int = 240

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class AuthRequest(BaseModel):
    user_id: str
    role: Role = Role.USER


class AddTransactionRequest(BaseModel):
    user_id: str
    account_id: str
    amount: float = Field(gt=0)
    transaction_type: TransactionType = TransactionType.EXPENSE
    category: str | None = None
    description: str
    merchant: str | None = None


settings = GatewaySettings()
app = FastAPI(title="MoneyWise API Gateway", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


AuthRequest.model_rebuild()
AddTransactionRequest.model_rebuild()


async def _post_json(client: httpx.AsyncClient, url: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = await client.post(url, json=payload)
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


async def _get_json(client: httpx.AsyncClient, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    response = await client.get(url, params=params)
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


def _service_urls() -> dict[str, str]:
    return {
        "account": settings.account_service_url,
        "transaction": settings.transaction_service_url,
        "budget": settings.budget_service_url,
        "goal": settings.goal_service_url,
        "investment": settings.investment_service_url,
        "analytics": settings.analytics_service_url,
        "notification": settings.notification_service_url,
    }


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.post("/auth/token")
async def issue_token(request: AuthRequest) -> dict[str, str]:
    token = sign_token(
        {"sub": request.user_id, "role": request.role.value},
        settings.jwt_secret,
        exp_minutes=settings.token_exp_minutes,
    )
    return {"access_token": token, "token_type": "Bearer"}


@app.post("/auth/verify")
async def verify_auth(token: str) -> dict[str, Any]:
    payload = verify_token(token, settings.jwt_secret)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload


@app.get("/services/health")
async def service_health() -> dict[str, Any]:
    statuses: dict[str, Any] = {}
    async with httpx.AsyncClient(timeout=12.0) as client:
        for name, base_url in _service_urls().items():
            try:
                statuses[name] = await _get_json(client, f"{base_url}/health")
            except HTTPException as exc:
                statuses[name] = {"status": "error", "detail": exc.detail}
            except httpx.HTTPError as exc:
                statuses[name] = {"status": "error", "detail": str(exc)}
    return statuses


@app.post("/workflow/add-transaction")
async def add_transaction_workflow(request: AddTransactionRequest) -> dict[str, Any]:
    month = datetime.now(UTC).strftime("%Y-%m")
    notifications: list[dict[str, Any]] = []

    async with httpx.AsyncClient(timeout=20.0) as client:
        transaction = await _post_json(
            client,
            f"{settings.transaction_service_url}/transactions",
            {
                "user_id": request.user_id,
                "account_id": request.account_id,
                "amount": request.amount,
                "transaction_type": request.transaction_type.value,
                "category": request.category,
                "description": request.description,
                "merchant": request.merchant,
            },
        )

        delta = request.amount if request.transaction_type == TransactionType.INCOME else -request.amount
        account_update = await _post_json(
            client,
            f"{settings.account_service_url}/accounts/{request.account_id}/balance/apply",
            {"delta": delta, "reason": f"transaction:{transaction['transaction_id']}"},
        )

        budget_result: dict[str, Any] = {
            "matched": False,
            "alerts": [],
            "message": "Skipped for non-expense transaction",
        }
        if request.transaction_type == TransactionType.EXPENSE:
            budget_result = await _post_json(
                client,
                f"{settings.budget_service_url}/budgets/check",
                {
                    "user_id": request.user_id,
                    "category": transaction["category"],
                    "amount": request.amount,
                    "month": month,
                },
            )
            for alert in budget_result.get("alerts", []):
                notification = await _post_json(
                    client,
                    f"{settings.notification_service_url}/notify/budget-exceeded",
                    {
                        "user_id": request.user_id,
                        "category": alert["category"],
                        "month": alert["month"],
                        "spent_amount": alert["spent_amount"],
                        "limit_amount": alert["limit_amount"],
                    },
                )
                notifications.append(notification)

        tx_rows = await _get_json(
            client,
            f"{settings.transaction_service_url}/transactions",
            {"user_id": request.user_id},
        )
        transactions = tx_rows.get("items", [])
        income = sum(item["amount"] for item in transactions if item.get("transaction_type") == "income")
        expense = sum(item["amount"] for item in transactions if item.get("transaction_type") == "expense")
        monthly_free_cash = max(income - expense, 0) * 0.15

        goals = await _post_json(
            client,
            f"{settings.goal_service_url}/goals/{request.user_id}/update",
            {"monthly_free_cash": round(monthly_free_cash, 2)},
        )

        await _post_json(
            client,
            f"{settings.analytics_service_url}/analytics/ingest/transactions",
            {"user_id": request.user_id, "transactions": transactions},
        )

    result = AddTransactionWorkflowResult(
        transaction=transaction,
        account=account_update["account"],
        budget=budget_result,
        goals=goals,
        notifications=notifications,
    )
    return result.model_dump(mode="json")


@app.get("/dashboard/{user_id}")
async def dashboard(user_id: str) -> dict[str, Any]:
    month = datetime.now(UTC).strftime("%Y-%m")
    async with httpx.AsyncClient(timeout=20.0) as client:
        accounts = await _get_json(
            client,
            f"{settings.account_service_url}/accounts",
            {"user_id": user_id},
        )
        transactions = await _get_json(
            client,
            f"{settings.transaction_service_url}/transactions",
            {"user_id": user_id},
        )
        recurring = await _get_json(
            client,
            f"{settings.transaction_service_url}/transactions/recurring",
            {"user_id": user_id},
        )
        budgets = await _get_json(
            client,
            f"{settings.budget_service_url}/budgets",
            {"user_id": user_id, "month": month},
        )
        budget_alerts = await _get_json(
            client,
            f"{settings.budget_service_url}/budgets/alerts",
            {"user_id": user_id},
        )
        goals = await _get_json(client, f"{settings.goal_service_url}/goals/{user_id}")
        portfolio = await _get_json(client, f"{settings.investment_service_url}/investments/portfolio/{user_id}")
        risk = await _get_json(client, f"{settings.investment_service_url}/investments/portfolio/{user_id}/risk")
        reports = await _post_json(
            client,
            f"{settings.analytics_service_url}/analytics/reports/compute",
            {"user_id": user_id, "transactions": transactions.get("items", [])},
        )
        analytics_kpi = await _get_json(client, f"{settings.analytics_service_url}/analytics/kpi")
        notifications = await _get_json(
            client,
            f"{settings.notification_service_url}/notify/history",
            {"user_id": user_id},
        )
        categorization = await _get_json(client, f"{settings.transaction_service_url}/categorization/metrics")

    return {
        "accounts": accounts,
        "transactions": transactions,
        "recurring": recurring,
        "budgets": budgets,
        "budget_alerts": budget_alerts,
        "goals": goals,
        "portfolio": portfolio,
        "portfolio_risk": risk,
        "reports": reports,
        "analytics_kpi": analytics_kpi,
        "categorization": categorization,
        "notifications": notifications,
    }
