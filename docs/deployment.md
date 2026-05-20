# Deployment Notes

## Prerequisites

- Docker and Docker Compose
- Python 3.11+ for local tests

## Steps

1. Copy `.env.example` to `.env` if you need custom values.
2. Build and start services:
   - `docker compose up --build -d`
3. Check cluster health:
   - `curl http://localhost:8580/services/health`

## Stop

- `docker compose down`

## With volumes cleanup

- `docker compose down -v`
