# Travel System — Deployment Guide

Production runs on **Neon** (Postgres 16), **Render** (API + scheduled cron jobs) and **Vercel** (frontend). Development runs entirely from Docker Compose. Follow this sequence when re-provisioning or moving environments.

| Env | Database | API | Frontend | Jobs |
|-----|----------|-----|----------|------|
| development | local Postgres 16 (Compose) | Compose `api` on `:8000` | Compose `frontend` on `:5173` | Celery worker + beat in Compose |
| production | Neon branch `main` | Render `travel-system-api` | Vercel production deploy | Render cron jobs (no worker, no Redis) |

Live endpoints: API `https://travel-1-3sq0.onrender.com`, frontend `https://travel-wine-chi.vercel.app`.

## 1. Neon (database first)

1. Create a Neon project and a branch for each environment.
2. Copy **two** connection strings:
   - **Pooled** (`...pooler...`) → `DATABASE_URL`, `ADMIN_DATABASE_URL`.
   - **Direct** (`...neon.tech`) → `DATABASE_URL_DIRECT` (what Alembic uses).
3. Use `?ssl=require` as the query parameter. `?sslmode=require` is **not** understood by SQLAlchemy's asyncpg URL and will fail to connect.
4. Schemas are created by migrations (`crm`, `admin`) — no manual DDL required.
5. The engine uses `pool_pre_ping` and `pool_recycle`; Neon scales to zero, so cold starts are retried by the app and by the smoke test.

Both `DATABASE_URL` and `ADMIN_DATABASE_URL` point at the same database: `crm` and `admin` are schemas within it. `ADMIN_DATABASE_URL` is a required setting reserved for splitting the ledger onto its own connection later.

## 2. Object storage & email

- **Storage**: `STORAGE_BACKEND=local` in production. Files are written to the container filesystem, which Render wipes on every deploy; invoice PDFs are regenerated automatically when missing, so nothing breaks. Switching to Cloudflare R2/S3 means setting `STORAGE_BACKEND=s3` plus `STORAGE_ENDPOINT` / `STORAGE_BUCKET` / `STORAGE_ACCESS_KEY` / `STORAGE_SECRET_KEY` / `STORAGE_USE_SSL`.
- **Email**: Resend in production (`EMAIL_PROVIDER=resend`, `RESEND_API_KEY`, `EMAIL_FROM` on a verified domain), Mailpit locally (`EMAIL_PROVIDER=mailpit`). Sending goes through the transactional outbox, so provider failures never fail a user request.

## 3. Background jobs (Render cron, no Redis)

Production has **no Celery worker and no Redis**. Every scheduled job is a Render cron job that runs a command from `backend/app/cli.py` in the API's image and exits:

| Service | Schedule (UTC) | Command |
|---------|----------------|---------|
| `travel-system-outbox-sync` | `*/5 * * * *` | `python -m app.cli outbox 200` |
| `travel-system-reminders` | `0 9 * * *` (12:00 EAT) | `python -m app.cli reminders` |
| `travel-system-reconciliation` | `0 2 * * *` | `python -m app.cli reconcile` |

Notes on the blueprint ([`render.yaml`](../render.yaml)):

- Crons use `runtime: docker` and override the image command with `dockerCommand` (also mirrored in `startCommand`); `buildCommand`/`runCommand` are not valid for Docker-based crons.
- Cron jobs inherit secrets from the API service via `fromService.envVarKey`, so nothing sensitive is duplicated in the file.
- Validate before syncing: the file is checked against Render's published schema (`https://render.com/schema/render.yaml.json`).
- Syncing the blueprint **removes** any blueprint-managed worker or Redis service, which is intended.

Local Compose runs Celery instead: `docker compose up` starts a worker with `--beat`, and `backend/app/workers/celery_app.py` mirrors the same three schedules (beat only, no `--beat` process runs in production).

## 4. Render API (FastAPI, Docker)

- Blueprint service `travel-system-api`, image built from `backend/Dockerfile.api`.
- Health check: `GET /api/v1/health` (also drives zero-downtime deploys).
- Pre-deploy: `alembic upgrade head` against `DATABASE_URL_DIRECT`.
- Deploys automatically on every push to `main`.
- Environment variables (set in the dashboard or via the blueprint):

| Key | Value / source |
|-----|----------------|
| `ENVIRONMENT`, `LOG_LEVEL`, `BASE_CURRENCY` | `production`, `INFO`, `UGX` |
| `PAYMENT_PROVIDER`, `STORAGE_BACKEND` | `mock`, `local` |
| `DATABASE_URL`, `DATABASE_URL_DIRECT`, `ADMIN_DATABASE_URL` | Neon (`sync: false`) |
| `SECRET_KEY`, `JWT_SECRET`, `JWT_REFRESH_SECRET`, `ENCRYPTION_KEY` | secrets — never in the repo |
| `CORS_ORIGINS`, `FRONTEND_URL` | Vercel domain |
| `STORAGE_*`, `EMAIL_PROVIDER`, `EMAIL_FROM`, `RESEND_API_KEY` | storage + Resend |

`ENCRYPTION_KEY` must never change once real data exists — re-keying would orphan every encrypted passport number.

## 5. Vercel (frontend)

- Root `frontend/`, build `npm run build`, output `dist/`, preset Vite.
- `VITE_API_BASE_URL` is inlined at **build** time: changing the API URL requires a redeploy of the frontend.
- `vercel.json` provides SPA rewrites plus security headers.
- `vercel.json` also redirects unmatched `*.vercel.app` hosts to the primary domain, so PR preview deployments land on production rather than a preview API. Point previews at a staging API if you need them.

## 6. Wiring

- `CORS_ORIGINS` and `FRONTEND_URL` must list the exact frontend origin (scheme + host, no trailing slash).
- Payments use the mock provider; there is no external payment webhook yet, so nothing to register with a provider.
- Custom domains + HTTPS are configured per service in Render and Vercel.
- The frontend shows a paper-plane "waking up" state while the free-tier API cold starts.

## 7. CI/CD (GitHub Actions)

`.github/workflows/ci.yml` runs on pushes and PRs:

| Job | Steps |
|-----|-------|
| `backend` | `ruff check app tests`, `mypy app` (both blocking), `pytest -q` on SQLite |
| `frontend` | `npm ci`, `npm run typecheck`, `npm run build` |
| `smoke` | runs on `main` only, waits ~75s for the Render deploy, then runs `scripts/smoke_test.py` |

Deploys themselves are not CI-driven: Render and Vercel both auto-deploy on push to `main`.

The smoke job needs repository secrets `SMOKE_API_URL` (plus optional `SMOKE_ADMIN_EMAIL`, `SMOKE_ADMIN_PASSWORD`). If `SMOKE_API_URL` is absent the job skips instead of failing.

## 8. Smoke test

```bash
# production
python scripts/smoke_test.py https://travel-1-3sq0.onrender.com

# local (seeded admin password differs)
SMOKE_ADMIN_PASSWORD='Admin123!' python scripts/smoke_test.py http://localhost:8000
```

Configuration: `SMOKE_API_URL`, `SMOKE_ADMIN_EMAIL` (default `admin@example.com`), `SMOKE_ADMIN_PASSWORD`, `SMOKE_TIMEOUT`, `SMOKE_HEALTH_ATTEMPTS`/`SMOKE_HEALTH_DELAY` (cold-start polling), `SMOKE_SKIP_CLEANUP`.

It checks, in order: health (with cold-start retry), login, client list, client create, mock payment create, invoice PDF bytes, refund, outbox read, admin-ledger reconciliation, analytics summary, CSV export, and cleans up the client it created. Exit code `0` means every check passed; failures are listed by name.

## Key considerations

- Free tiers sleep (Render) and scale to zero (Neon) → cold-start retries everywhere; never treat the first timeout as a failure.
- Render has no persistent disk → local storage is ephemeral, and anything durable belongs in object storage.
- Secrets live only in the Render/Vercel/Neon dashboards — never in this repository.
- Redis is a local-development dependency only; production must not be given a `REDIS_URL` it does not need.
