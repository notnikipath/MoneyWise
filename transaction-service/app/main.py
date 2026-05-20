from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import FastAPI

from shared.moneywise_common import (
    RecurringPayment,
    RecurringPaymentCreateRequest,
    Settings,
    Transaction,
    TransactionCreateRequest,
    TransactionType,
    auto_categorize,
    categorization_accuracy,
    normalize_category,
)

settings = Settings(service_name="transaction-service", service_port=8402)
app = FastAPI(title="MoneyWise Transaction Service", version="1.0.0")

transactions: dict[str, Transaction] = {}
recurring_payments: dict[str, RecurringPayment] = {}
validation_pairs: list[tuple[str, str]] = [
    ("groceries", "groceries"),
    ("transport", "transport"),
    ("housing", "housing"),
    ("entertainment", "entertainment"),
    ("health", "health"),
    ("other", "other"),
    ("investment", "investment"),
    ("other", "groceries"),
    ("salary", "salary"),
    ("transport", "transport"),
]


def _seed_demo() -> None:
    demo_items = [
        TransactionCreateRequest(
            user_id="USR-DEMO",
            account_id="ACC-DEMO-1",
            amount=185_000,
            transaction_type=TransactionType.INCOME,
            category="salary",
            description="Monthly payroll",
        ),
        TransactionCreateRequest(
            user_id="USR-DEMO",
            account_id="ACC-DEMO-1",
            amount=16_500,
            transaction_type=TransactionType.EXPENSE,
            category="groceries",
            description="Supermarket expenses",
        ),
        TransactionCreateRequest(
            user_id="USR-DEMO",
            account_id="ACC-DEMO-1",
            amount=5_600,
            transaction_type=TransactionType.EXPENSE,
            category="transport",
            description="Taxi and fuel",
        ),
    ]
    for item in demo_items:
        _create_transaction(item)



def _create_transaction(request: TransactionCreateRequest) -> Transaction:
    manual_category = normalize_category(request.category) if request.category else None
    if manual_category:
        category = manual_category
        is_auto = False
    else:
        category, is_auto = auto_categorize(request.description, request.merchant)
    transaction = Transaction(
        transaction_id=str(uuid4()),
        user_id=request.user_id,
        account_id=request.account_id,
        amount=request.amount,
        transaction_type=request.transaction_type,
        category=category,
        description=request.description,
        merchant=request.merchant,
        booked_at=request.booked_at,
        is_auto_categorized=is_auto,
    )
    transactions[transaction.transaction_id] = transaction
    return transaction


_seed_demo()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.get("/transactions")
async def list_transactions(
    user_id: str | None = None,
    account_id: str | None = None,
    transaction_type: TransactionType | None = None,
) -> dict[str, Any]:
    items = []
    for transaction in transactions.values():
        if user_id and transaction.user_id != user_id:
            continue
        if account_id and transaction.account_id != account_id:
            continue
        if transaction_type and transaction.transaction_type != transaction_type:
            continue
        items.append(transaction.model_dump(mode="json"))
    items.sort(key=lambda item: item["booked_at"], reverse=True)
    return {"items": items, "count": len(items)}


@app.post("/transactions")
async def create_transaction(request: TransactionCreateRequest) -> dict[str, Any]:
    transaction = _create_transaction(request)
    return transaction.model_dump(mode="json")


@app.post("/transactions/recurring")
async def create_recurring_payment(request: RecurringPaymentCreateRequest) -> dict[str, Any]:
    recurring = RecurringPayment(
        recurring_id=str(uuid4()),
        user_id=request.user_id,
        account_id=request.account_id,
        amount=request.amount,
        transaction_type=request.transaction_type,
        category=normalize_category(request.category),
        description=request.description,
        day_of_month=request.day_of_month,
    )
    recurring_payments[recurring.recurring_id] = recurring
    return recurring.model_dump(mode="json")


@app.get("/transactions/recurring")
async def list_recurring(user_id: str | None = None) -> dict[str, Any]:
    items = []
    for recurring in recurring_payments.values():
        if user_id and recurring.user_id != user_id:
            continue
        items.append(recurring.model_dump(mode="json"))
    return {"items": items, "count": len(items)}


@app.post("/transactions/recurring/{recurring_id}/execute")
async def execute_recurring(recurring_id: str) -> dict[str, Any]:
    recurring = recurring_payments.get(recurring_id)
    if recurring is None:
        return {"status": "not_found"}
    if not recurring.active:
        return {"status": "inactive"}

    request = TransactionCreateRequest(
        user_id=recurring.user_id,
        account_id=recurring.account_id,
        amount=recurring.amount,
        transaction_type=recurring.transaction_type,
        category=recurring.category,
        description=recurring.description,
        booked_at=datetime.now(UTC),
    )
    transaction = _create_transaction(request)
    return {"status": "executed", "transaction": transaction.model_dump(mode="json")}


@app.get("/categorization/metrics")
async def categorization_metrics() -> dict[str, Any]:
    predicted = [item[0] for item in validation_pairs]
    actual = [item[1] for item in validation_pairs]
    accuracy = categorization_accuracy(predicted, actual)
    auto_share = 0.0
    if transactions:
        auto_count = len([transaction for transaction in transactions.values() if transaction.is_auto_categorized])
        auto_share = round(auto_count / len(transactions) * 100, 2)
    return {
        "accuracy_pct": accuracy,
        "target_pct": settings.categorization_accuracy_target,
        "meets_target": accuracy >= settings.categorization_accuracy_target,
        "auto_categorized_share_pct": auto_share,
    }
