# Architecture

## Context

MoneyWise helps users control spending, enforce category budgets, grow savings goals, and track investment performance from one platform.

## Service map

- `api-gateway`: unified entrypoint and workflow orchestrator
- `account-service`: account registry, card balances, statement import
- `transaction-service`: transactions, categorization, recurring operations
- `budget-service`: monthly limits and overspend detection
- `goal-service`: savings goals and monthly contribution logic
- `investment-service`: portfolio positions, return, risk scoring
- `analytics-service`: cashflow analytics, forecast, KPI tracking, caching
- `notification-service`: push or email style notifications

## Infrastructure

- PostgreSQL as persistent OLTP storage target
- Redis for cache and Celery broker
- Celery worker for asynchronous jobs (FX rates and report warmup)
- Docker Compose for local deployment

## Core orchestration flow

1. User sends a new transaction via gateway
2. Gateway stores transaction
3. Gateway updates account balance
4. Gateway validates budget and emits alert when limit exceeded
5. Gateway updates goals with current free-cash estimate
6. Gateway refreshes analytics dataset and dashboard view

## Scalability notes

- Analytics report responses are cache-backed (`TTLCache`) to keep report latency low
- Service decomposition supports independent horizontal scaling for write-heavy transaction traffic
- Celery worker offloads non-blocking jobs such as rates refresh
- Throughput KPI endpoint tracks proximity to 1M transactions/day target
