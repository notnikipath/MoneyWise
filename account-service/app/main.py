from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException

from shared.moneywise_common import (
    Account,
    AccountCreateRequest,
    AccountType,
    BalanceAdjustmentRequest,
    Settings,
    StatementImportRequest,
)

settings = Settings(service_name="account-service", service_port=8401)
app = FastAPI(title="MoneyWise Account Service", version="1.0.0")

accounts: dict[str, Account] = {
    "ACC-DEMO-1": Account(
        account_id="ACC-DEMO-1",
        user_id="USR-DEMO",
        name="Main Debit",
        account_type=AccountType.DEBIT_CARD,
        currency="RUB",
        balance=178_450.0,
    ),
    "ACC-DEMO-2": Account(
        account_id="ACC-DEMO-2",
        user_id="USR-DEMO",
        name="Credit Card",
        account_type=AccountType.CREDIT_CARD,
        currency="RUB",
        balance=-12_300.0,
        credit_limit=150_000,
    ),
}
statement_import_history: list[dict[str, Any]] = []


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.get("/accounts")
async def list_accounts(user_id: str | None = None) -> dict[str, Any]:
    items = []
    for account in accounts.values():
        if user_id and account.user_id != user_id:
            continue
        items.append(account.model_dump(mode="json"))
    return {"items": items, "count": len(items)}


@app.get("/accounts/{account_id}")
async def get_account(account_id: str) -> dict[str, Any]:
    account = accounts.get(account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return account.model_dump(mode="json")


@app.post("/accounts")
async def create_account(request: AccountCreateRequest) -> dict[str, Any]:
    account = Account(
        account_id=str(uuid4()),
        user_id=request.user_id,
        name=request.name,
        account_type=request.account_type,
        currency=request.currency,
        balance=request.balance,
        credit_limit=request.credit_limit,
    )
    accounts[account.account_id] = account
    return account.model_dump(mode="json")


@app.post("/accounts/{account_id}/balance/apply")
async def apply_balance_change(account_id: str, request: BalanceAdjustmentRequest) -> dict[str, Any]:
    account = accounts.get(account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    account.balance = round(account.balance + request.delta, 2)
    return {
        "account": account.model_dump(mode="json"),
        "delta": request.delta,
        "reason": request.reason,
    }


@app.post("/accounts/import/statement")
async def import_statement(request: StatementImportRequest) -> dict[str, Any]:
    account = accounts.get(request.account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    if account.user_id != request.user_id:
        raise HTTPException(status_code=403, detail="Account does not belong to user")

    imported = []
    total_income = 0.0
    total_expense = 0.0

    for row in request.rows:
        tx_type = "income" if row.amount >= 0 else "expense"
        amount = abs(row.amount)
        if tx_type == "income":
            total_income += amount
            account.balance = round(account.balance + amount, 2)
        else:
            total_expense += amount
            account.balance = round(account.balance - amount, 2)
        imported.append(
            {
                "booked_at": row.booked_at.isoformat(),
                "amount": amount,
                "transaction_type": tx_type,
                "description": row.description,
                "merchant": row.merchant,
            }
        )

    batch = {
        "import_id": str(uuid4()),
        "user_id": request.user_id,
        "account_id": request.account_id,
        "statement_format": request.statement_format,
        "rows": imported,
        "rows_count": len(imported),
        "total_income": round(total_income, 2),
        "total_expense": round(total_expense, 2),
        "created_at": datetime.now(UTC).isoformat(),
    }
    statement_import_history.append(batch)
    return {
        "status": "imported",
        "batch": batch,
        "account": account.model_dump(mode="json"),
    }


@app.get("/accounts/import/history")
async def import_history(user_id: str | None = None, limit: int = 20) -> dict[str, Any]:
    items = statement_import_history
    if user_id:
        items = [item for item in statement_import_history if item["user_id"] == user_id]
    return {"items": items[-limit:], "count": len(items)}
