# MoneyWise

MoneyWise is a microservice personal finance assistant for transaction tracking, budgeting, financial goals, investments, and analytics.

## Implemented modules

- `api-gateway` - auth, health checks, orchestration workflows, dashboard aggregation
- `account-service` - accounts and cards, balance updates, XLSX or OFX statement import API
- `transaction-service` - manual transaction entry, automatic categorization, recurring payments
- `budget-service` - category limits, overspend alerts
- `goal-service` - goals with monthly saving plan and progress updates
- `investment-service` - portfolio positions, return and risk profile
- `analytics-service` - cashflow reports, category analytics, expense forecast, KPI and cache metrics
- `notification-service` - user notifications and budget overrun alerts
- `frontend` - React dashboard (desktop and mobile responsive)
- `mobile-app` - React Native blueprint notes

## Required stack

- Backend: Python + FastAPI
- Database: PostgreSQL, Redis
- Queues: Celery (Redis broker)
- Frontend: React
- Mobile: React Native (blueprint folder)

## Project structure

```text
Task_30_MoneyWise/
├── api-gateway/
├── account-service/
├── transaction-service/
├── budget-service/
├── goal-service/
├── investment-service/
├── analytics-service/
├── notification-service/
├── shared/
├── tests/
├── scripts/
├── docs/
├── frontend/
└── mobile-app/
```

## Key workflow (analogous to assignment)

`POST /workflow/add-transaction`

1. Create transaction in `transaction-service`
2. Update account balance in `account-service`
3. Check budget and create alerts in `budget-service`
4. Send notifications in `notification-service`
5. Update goals in `goal-service`
6. Refresh analytics dataset in `analytics-service`

## Optional improvements implemented

- Group A:
  - Automatic transaction categorization
  - Expense forecasting
  - Saving-rate recommendation
  - Investment risk analysis
- Group B:
  - Broker connect endpoint
  - Statement import endpoint (`xlsx`, `ofx`)
- Group C:
  - Report caching via TTL cache
  - Parallel processing plan via async-ready service decomposition
  - Asynchronous FX update task (Celery)

## Quality metrics coverage

- Categorization accuracy metric exposed by `GET /categorization/metrics`
- Report load target metric exposed by `GET /analytics/kpi`
- Throughput target tracking exposed by `GET /analytics/kpi`

## Local run

```bash
cd 'your/project/folder'
docker compose up --build -d
```

## Useful URLs

- Frontend: `http://localhost:5277`
- Gateway health: `http://localhost:8580/health`
- Gateway docs: `http://localhost:8580/docs`
- Service health matrix: `http://localhost:8580/services/health`

## Validation

```bash
python -m pip install -r requirements-dev.txt
python -m ruff check .
python -m pytest -q
docker compose config
```

## Demo workflow script

```bash
python scripts/demo_workflow.py
```
