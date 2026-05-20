# API Overview

## Gateway

- `POST /auth/token`
- `POST /auth/verify`
- `GET /services/health`
- `POST /workflow/add-transaction`
- `GET /dashboard/{user_id}`

## Account service

- `GET /accounts`
- `GET /accounts/{account_id}`
- `POST /accounts`
- `POST /accounts/{account_id}/balance/apply`
- `POST /accounts/import/statement`
- `GET /accounts/import/history`

## Transaction service

- `GET /transactions`
- `POST /transactions`
- `POST /transactions/recurring`
- `GET /transactions/recurring`
- `POST /transactions/recurring/{recurring_id}/execute`
- `GET /categorization/metrics`

## Budget service

- `POST /budgets`
- `GET /budgets`
- `POST /budgets/check`
- `GET /budgets/alerts`

## Goal service

- `POST /goals`
- `GET /goals/{user_id}`
- `POST /goals/{user_id}/update`
- `GET /goals/{user_id}/summary`

## Investment service

- `POST /investments/positions`
- `GET /investments/positions`
- `POST /investments/quotes`
- `GET /investments/portfolio/{user_id}`
- `GET /investments/portfolio/{user_id}/risk`
- `POST /investments/broker/connect`

## Analytics service

- `POST /analytics/ingest/transactions`
- `POST /analytics/reports/compute`
- `GET /analytics/reports/{user_id}`
- `GET /analytics/kpi`
- `GET /analytics/cache/stats`

## Notification service

- `POST /notify/send`
- `POST /notify/budget-exceeded`
- `GET /notify/history`
