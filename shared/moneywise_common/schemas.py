from __future__ import annotations

from datetime import UTC, date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Role(str, Enum):
    USER = "user"
    ADVISOR = "advisor"
    ADMIN = "admin"


class AccountType(str, Enum):
    CASH = "cash"
    DEBIT_CARD = "debit_card"
    CREDIT_CARD = "credit_card"
    SAVINGS = "savings"


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"


class AssetType(str, Enum):
    STOCK = "stock"
    BOND = "bond"
    ETF = "etf"
    CASH = "cash"


class NotificationChannel(str, Enum):
    EMAIL = "email"
    PUSH = "push"
    TELEGRAM = "telegram"
    SMS = "sms"


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AccountCreateRequest(BaseModel):
    user_id: str
    name: str
    account_type: AccountType
    currency: str = "RUB"
    balance: float = Field(default=0.0)
    credit_limit: float = Field(default=0.0, ge=0)


class Account(BaseModel):
    account_id: str
    user_id: str
    name: str
    account_type: AccountType
    currency: str = "RUB"
    balance: float = 0.0
    credit_limit: float = Field(default=0.0, ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class BalanceAdjustmentRequest(BaseModel):
    delta: float
    reason: str


class StatementImportRow(BaseModel):
    booked_at: date
    amount: float
    description: str
    merchant: str | None = None


class StatementImportRequest(BaseModel):
    user_id: str
    account_id: str
    statement_format: str = Field(pattern="^(xlsx|ofx)$")
    rows: list[StatementImportRow] = Field(default_factory=list)


class TransactionCreateRequest(BaseModel):
    user_id: str
    account_id: str
    amount: float = Field(gt=0)
    transaction_type: TransactionType
    category: str | None = None
    description: str
    merchant: str | None = None
    booked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Transaction(BaseModel):
    transaction_id: str
    user_id: str
    account_id: str
    amount: float
    transaction_type: TransactionType
    category: str
    description: str
    merchant: str | None = None
    booked_at: datetime
    is_auto_categorized: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RecurringPaymentCreateRequest(BaseModel):
    user_id: str
    account_id: str
    amount: float = Field(gt=0)
    transaction_type: TransactionType = TransactionType.EXPENSE
    category: str
    description: str
    day_of_month: int = Field(ge=1, le=28)


class RecurringPayment(BaseModel):
    recurring_id: str
    user_id: str
    account_id: str
    amount: float
    transaction_type: TransactionType
    category: str
    description: str
    day_of_month: int
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class BudgetCreateRequest(BaseModel):
    user_id: str
    category: str
    limit_amount: float = Field(gt=0)
    month: str = Field(pattern="^\\d{4}-\\d{2}$")


class Budget(BaseModel):
    budget_id: str
    user_id: str
    category: str
    limit_amount: float
    spent_amount: float = 0.0
    month: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class BudgetCheckRequest(BaseModel):
    user_id: str
    category: str
    amount: float = Field(gt=0)
    month: str = Field(pattern="^\\d{4}-\\d{2}$")


class BudgetAlert(BaseModel):
    alert_id: str
    user_id: str
    category: str
    month: str
    limit_amount: float
    spent_amount: float
    over_by: float
    severity: Severity = Severity.WARNING
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class GoalCreateRequest(BaseModel):
    user_id: str
    name: str
    target_amount: float = Field(gt=0)
    deadline: date
    start_amount: float = Field(default=0.0, ge=0)


class Goal(BaseModel):
    goal_id: str
    user_id: str
    name: str
    target_amount: float
    current_amount: float
    deadline: date
    monthly_required: float
    progress_pct: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class GoalUpdateRequest(BaseModel):
    monthly_free_cash: float = Field(default=0.0)


class InvestmentPositionCreateRequest(BaseModel):
    user_id: str
    asset_type: AssetType
    ticker: str
    quantity: float = Field(gt=0)
    average_price: float = Field(gt=0)
    current_price: float = Field(gt=0)
    currency: str = "RUB"


class InvestmentPosition(BaseModel):
    position_id: str
    user_id: str
    asset_type: AssetType
    ticker: str
    quantity: float
    average_price: float
    current_price: float
    currency: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class QuoteUpdateRequest(BaseModel):
    ticker: str
    current_price: float = Field(gt=0)


class NotificationRequest(BaseModel):
    user_id: str
    channel: NotificationChannel
    subject: str
    body: str
    severity: Severity = Severity.INFO


class AuditEvent(BaseModel):
    event_id: str
    actor_id: str
    actor_role: Role | str
    action: str
    object_type: str
    object_id: str
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AddTransactionWorkflowRequest(BaseModel):
    user_id: str
    account_id: str
    amount: float = Field(gt=0)
    transaction_type: TransactionType = TransactionType.EXPENSE
    category: str | None = None
    description: str
    merchant: str | None = None


class AddTransactionWorkflowResult(BaseModel):
    transaction: dict[str, Any]
    account: dict[str, Any]
    budget: dict[str, Any]
    goals: dict[str, Any]
    notifications: list[dict[str, Any]] = Field(default_factory=list)
    processed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
