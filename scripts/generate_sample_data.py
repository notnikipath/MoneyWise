from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from random import choice, randint, uniform

users = ["USR-DEMO", "USR-100", "USR-200"]
categories = ["groceries", "transport", "health", "entertainment", "housing", "salary"]
transaction_types = ["income", "expense"]


def make_event(index: int) -> dict:
    tx_type = choice(transaction_types)
    category = "salary" if tx_type == "income" else choice(categories[:-1])
    amount = round(uniform(900, 28_000), 2)
    return {
        "transaction_id": f"TX-{index:05d}",
        "user_id": choice(users),
        "account_id": "ACC-DEMO-1",
        "amount": amount,
        "transaction_type": tx_type,
        "category": category,
        "description": f"Sample {category} transaction",
        "booked_at": (datetime.now(UTC) - timedelta(days=randint(0, 120))).isoformat(),
    }


def main() -> None:
    events = [make_event(index) for index in range(1, 401)]
    out = Path("data/samples/moneywise_transactions.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(events, indent=2), encoding="utf-8")
    print(f"Generated {len(events)} events into {out}")


if __name__ == "__main__":
    main()
