.PHONY: up down logs migrate seed test lint typecheck smoke api

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

api:
	cd backend && uvicorn app.main:app --reload

migrate:
	cd backend && alembic upgrade head

seed:
	cd backend && python ../scripts/seed.py

test:
	cd backend && pytest -v

lint:
	cd backend && ruff check app tests

typecheck:
	cd backend && mypy app

smoke:
	SMOKE_ADMIN_PASSWORD=Admin123! python scripts/smoke_test.py http://localhost:8000
