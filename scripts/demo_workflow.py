from __future__ import annotations

import json

import httpx

GATEWAY = "http://localhost:8580"


async def run_demo() -> None:
    async with httpx.AsyncClient(timeout=20.0) as client:
        payload = {
            "user_id": "USR-DEMO",
            "account_id": "ACC-DEMO-1",
            "amount": 4200,
            "transaction_type": "expense",
            "description": "Taxi and fuel refill",
        }
        workflow = await client.post(f"{GATEWAY}/workflow/add-transaction", json=payload)
        workflow.raise_for_status()

        dashboard = await client.get(f"{GATEWAY}/dashboard/USR-DEMO")
        dashboard.raise_for_status()

    print("Workflow result:")
    print(json.dumps(workflow.json(), indent=2, ensure_ascii=False))
    print()
    print("Dashboard snapshot:")
    print(json.dumps(dashboard.json(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    import asyncio

    asyncio.run(run_demo())
