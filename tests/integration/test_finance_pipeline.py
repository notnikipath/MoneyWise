from pathlib import Path

from fastapi.testclient import TestClient

from tests.integration.helpers import load_module

ROOT = Path(__file__).resolve().parents[2]

account_module = load_module("account_module", ROOT / "account-service" / "app" / "main.py")
transaction_module = load_module("transaction_module", ROOT / "transaction-service" / "app" / "main.py")
budget_module = load_module("budget_module", ROOT / "budget-service" / "app" / "main.py")
goal_module = load_module("goal_module", ROOT / "goal-service" / "app" / "main.py")
invest_module = load_module("invest_module", ROOT / "investment-service" / "app" / "main.py")
analytics_module = load_module("analytics_module", ROOT / "analytics-service" / "app" / "main.py")
notification_module = load_module("notification_module", ROOT / "notification-service" / "app" / "main.py")

account_client = TestClient(account_module.app)
transaction_client = TestClient(transaction_module.app)
budget_client = TestClient(budget_module.app)
goal_client = TestClient(goal_module.app)
invest_client = TestClient(invest_module.app)
analytics_client = TestClient(analytics_module.app)
notification_client = TestClient(notification_module.app)


def test_core_finance_flow() -> None:
    tx = transaction_client.post(
        "/transactions",
        json={
            "user_id": "USR-DEMO",
            "account_id": "ACC-DEMO-1",
            "amount": 3900,
            "transaction_type": "expense",
            "description": "Supermarket groceries",
        },
    )
    assert tx.status_code == 200
    transaction = tx.json()
    assert transaction["category"] == "groceries"

    account_update = account_client.post(
        "/accounts/ACC-DEMO-1/balance/apply",
        json={"delta": -3900, "reason": f"transaction:{transaction['transaction_id']}"},
    )
    assert account_update.status_code == 200

    budget_check = budget_client.post(
        "/budgets/check",
        json={
            "user_id": "USR-DEMO",
            "category": "groceries",
            "amount": 3900,
            "month": account_module.datetime.now(account_module.UTC).strftime("%Y-%m"),
        },
    )
    assert budget_check.status_code == 200

    goals_update = goal_client.post("/goals/USR-DEMO/update", json={"monthly_free_cash": 12000})
    assert goals_update.status_code == 200
    assert goals_update.json()["items"]



def test_analytics_and_investment_flow() -> None:
    tx_list = transaction_client.get("/transactions", params={"user_id": "USR-DEMO"})
    assert tx_list.status_code == 200

    report = analytics_client.post(
        "/analytics/reports/compute",
        json={"user_id": "USR-DEMO", "transactions": tx_list.json()["items"]},
    )
    assert report.status_code == 200
    assert "cashflow" in report.json()

    portfolio = invest_client.get("/investments/portfolio/USR-DEMO")
    assert portfolio.status_code == 200
    assert portfolio.json()["total_market_value"] > 0

    risk = invest_client.get("/investments/portfolio/USR-DEMO/risk")
    assert risk.status_code == 200
    assert risk.json()["risk_level"] in {"low", "medium", "high"}



def test_statement_import_and_notification() -> None:
    imported = account_client.post(
        "/accounts/import/statement",
        json={
            "user_id": "USR-DEMO",
            "account_id": "ACC-DEMO-1",
            "statement_format": "ofx",
            "rows": [
                {
                    "booked_at": "2026-05-01",
                    "amount": -2200,
                    "description": "Taxi",
                    "merchant": "CityTaxi",
                }
            ],
        },
    )
    assert imported.status_code == 200
    assert imported.json()["batch"]["rows_count"] == 1

    note = notification_client.post(
        "/notify/send",
        json={
            "user_id": "USR-DEMO",
            "channel": "push",
            "subject": "Budget reminder",
            "body": "You are close to transport budget limit",
            "severity": "info",
        },
    )
    assert note.status_code == 200
