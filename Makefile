lint:
	python -m ruff check .

test:
	python -m pytest -q

up:
	docker compose up --build -d
