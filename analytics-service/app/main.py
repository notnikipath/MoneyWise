from __future__ import annotations

from statistics import mean
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from shared.moneywise_common import (
    Settings,
    TTLCache,
    cashflow_by_month,
    category_breakdown,
    expense_forecast,
    projected_savings_rate,
    report_load_seconds,
    transactions_per_second,
)

settings = Settings(service_name="analytics-service", service_port=8406)
app = FastAPI(title="MoneyWise Analytics Service", version="1.0.0")

reports_cache = TTLCache(ttl_seconds=90)
report_hits = 0
report_misses = 0
user_transactions: dict[str, list[dict[str, Any]]] = {}


class TransactionsIngestRequest(BaseModel):
    user_id: str
    transactions: list[dict[str, Any]] = Field(default_factory=list)


class ComputeReportRequest(BaseModel):
    user_id: str
    transactions: list[dict[str, Any]] = Field(default_factory=list)


TransactionsIngestRequest.model_rebuild()
ComputeReportRequest.model_rebuild()


def _build_reports(user_id: str, transactions: list[dict[str, Any]]) -> dict[str, Any]:
    cashflow = cashflow_by_month(transactions)
    categories = category_breakdown(transactions)

    monthly_income = [item["income"] for item in cashflow.values()]
    monthly_expense = [item["expense"] for item in cashflow.values()]
    avg_income = round(mean(monthly_income), 2) if monthly_income else 0.0
    avg_expense = round(mean(monthly_expense), 2) if monthly_expense else 0.0

    forecast = {
        "next_month_expense": expense_forecast(monthly_expense),
        "avg_income": avg_income,
        "avg_expense": avg_expense,
        "savings_rate_pct": projected_savings_rate(avg_income, avg_expense),
    }

    return {
        "user_id": user_id,
        "cashflow": cashflow,
        "categories": categories,
        "forecast": forecast,
        "transactions_count": len(transactions),
    }


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.post("/analytics/ingest/transactions")
async def ingest_transactions(request: TransactionsIngestRequest) -> dict[str, Any]:
    user_transactions[request.user_id] = request.transactions
    reports_cache.clear()
    return {"status": "accepted", "user_id": request.user_id, "count": len(request.transactions)}


@app.post("/analytics/reports/compute")
async def compute_reports(request: ComputeReportRequest) -> dict[str, Any]:
    global report_hits, report_misses
    cache_key = f"report:{request.user_id}:{len(request.transactions)}"
    cached = reports_cache.get(cache_key)
    if cached is not None:
        report_hits += 1
        return {**cached, "cache": "hit"}

    report_misses += 1
    data = _build_reports(request.user_id, request.transactions)
    reports_cache.set(cache_key, data)
    return {**data, "cache": "miss"}


@app.get("/analytics/reports/{user_id}")
async def report_for_user(user_id: str) -> dict[str, Any]:
    transactions = user_transactions.get(user_id, [])
    return _build_reports(user_id, transactions)


@app.get("/analytics/kpi")
async def kpi() -> dict[str, Any]:
    cache_total = report_hits + report_misses
    hit_ratio = report_hits / cache_total if cache_total else 0.0
    row_count = sum(len(items) for items in user_transactions.values())
    current_tx_day = max(row_count * 320, 1)

    return {
        "categorization_accuracy_target_pct": settings.categorization_accuracy_target,
        "report_latency_estimate_seconds": report_load_seconds(hit_ratio, row_count),
        "report_latency_target_seconds": settings.report_latency_target_seconds,
        "throughput_estimate_tx_per_day": current_tx_day,
        "throughput_target_tx_per_day": settings.throughput_target_tx_per_day,
        "throughput_estimate_tps": transactions_per_second(current_tx_day),
        "cache_hit_ratio": round(hit_ratio * 100, 2),
    }


@app.get("/analytics/cache/stats")
async def cache_stats() -> dict[str, Any]:
    total = report_hits + report_misses
    ratio = round((report_hits / total) * 100, 2) if total else 0.0
    return {
        "hits": report_hits,
        "misses": report_misses,
        "hit_ratio_pct": ratio,
    }
