from __future__ import annotations

from random import uniform

from .celery_app import celery_app


@celery_app.task(name="moneywise.refresh_exchange_rates")
def refresh_exchange_rates() -> dict[str, float]:
    # Simulated asynchronous FX refresh.
    return {
        "USD_RUB": round(uniform(83, 97), 4),
        "EUR_RUB": round(uniform(91, 108), 4),
        "CNY_RUB": round(uniform(11.2, 13.5), 4),
    }


@celery_app.task(name="moneywise.warmup_reports")
def warmup_reports(user_id: str) -> dict[str, str]:
    return {"status": "scheduled", "user_id": user_id}
