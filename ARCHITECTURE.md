# Travel System - Architecture

## Repository layout

```
travel-system/
|-- backend/
|   |-- app/
|   |   |-- api/v1/          # REST endpoints (routers, deps)
|   |   |-- core/            # config, security (jwt, passwords, encryption), logging
|   |   |-- db/              # async engine + session
|   |   |-- middleware/      # error envelope, audit, rate limiting
|   |   |-- models/          # SQLAlchemy 2.0 models (crm + admin schemas)
|   |   |-- repositories/    # data access / query building
|   |   |-- schemas/         # Pydantic v2 schemas
|   |   |-- services/        # business logic (payments, ledger, analytics,
|   |   |                    #   export, pdf, reminders, reconciliation, ...)
|   |   |-- tasks/           # Celery task definitions (local compose only)
|   |   |-- utils/           # helpers (dates, masking, validators)
|   |   |-- workers/         # Celery app + beat schedule (local compose only)
|   |   |-- cli.py           # cron entrypoint: outbox | reminders | reconcile
|   |   `-- main.py          # FastAPI app factory
|   |-- alembic/             # migrations (crm + admin schemas)
|   |-- tests/               # pytest, SQLite harness
|   |-- Dockerfile.api       # image for the API and the Render cron jobs
|   |-- Dockerfile.worker    # image for the local Celery worker
|   |-- pyproject.toml       # ruff + strict mypy configuration
|   `-- requirements.txt
|-- frontend/
|   |-- src/
|   |   |-- components/      # shared UI
|   |   |-- config/          # api client, theme config
|   |   |-- features/        # feature modules (clients, trips, payments, analytics, ...)
|   |   |-- styles/          # theme tokens (orange, dark mode)
|   |   |-- App.tsx
|   |   `-- main.tsx
|   |-- tailwind.config.ts
|   |-- vite.config.ts
|   |-- vercel.json          # SPA rewrite + security headers
|   `-- .env.example
|-- scripts/                 # seed.py, smoke_test.py, create_admin.py
|-- docs/                    # DEPLOYMENT.md, ERD.md, HOSTING_PHASE2.md (historical)
|-- .github/workflows/ci.yml # ruff, mypy, pytest, tsc, build, post-deploy smoke
|-- render.yaml              # Render blueprint: API + 3 cron jobs
|-- docker-compose.yml       # local stack: postgres, redis, minio, mailpit,
|                            #   api, worker+beat, frontend
|-- Makefile                 # up, down, api, migrate, seed, test, lint, typecheck, smoke
|-- PHASES.md                # phase breakdown (1-6, all delivered)
|-- DEPLOYMENT_PLAN.md       # hosting sequence this deployment follows
|-- DB_SCHEMA.md  ERD.md  PLAN.md  ARCHITECTURE.md  README.md
```

## Runtime shape

- **Production**: Vercel frontend -> Render FastAPI -> Neon (`crm` + `admin` schemas).
  Background work runs as Render cron jobs invoking `python -m app.cli`, so there is
  no Celery worker and no Redis in production.
- **Local**: the same app plus Celery worker + beat and Redis, MinIO and Mailpit,
  all from `docker-compose.yml`. The beat schedule mirrors the Render crons.

## Design Principles

- Modular (routers/services/repos/schemas)
- Type-safe end-to-end (TS strict + mypy strict)
- Security-first (AES-256-GCM field encryption, masking, audit log)
- Cloud-native for Render/Vercel/Neon
- Transactions first: side effects (email, ledger sync) go through the
  transactional outbox, never inline in a request
