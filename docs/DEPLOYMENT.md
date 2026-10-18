# Travel System — Deployment Guide

This project deploys across **Neon** (Postgres), **Render** (API + worker + cron + Redis), and **Vercel** (frontend). Follow the hosting sequence below exactly.

## Environments

| Env | Neon branch | Render | Vercel |
|-----|-------------|--------|--------|
| development | local Docker Compose | local | local |
| staging | `staging` | staging services | preview deploys |
| production | `main` | production services | prod domain |

## 1. Neon (database first)

1. Create a Neon project. Add branches: `main`, `staging`, `dev`.
2. In each branch create the schemas (migrations do this too):
   ```sql
   CREATE SCHEMA IF NOT EXISTS crm;
   CREATE SCHEMA IF NOT EXISTS admin;
   ```
3. Copy **two** connection strings per environment:
   - **Pooled** (`...pooler.neon.tech`) → `DATABASE_URL`, `ADMIN_DATABASE_URL` for the app/workers.
   - **Direct** (`...neon.tech`) → `DATABASE_URL_DIRECT` for Alembic migrations.
4. The app uses `pool_pre_ping=True` and `pool_recycle=300`, with retry/backoff on cold starts (Neon scales to zero).

## 2. Object storage & email

- Storage: Cloudflare R2 (or AWS S3) private bucket. Local dev uses MinIO. Set `STORAGE_*` env vars.
- Email: Resend in staging/prod (`EMAIL_PROVIDER=resend`, `RESEND_API_KEY`), Mailpit locally.

## 3. Render Key Value (Redis)

- Provision a Render Key Value instance. It provides `REDIS_URL` used as the Celery broker/backend and for caching/rate-limiting.

## 4. Render API (FastAPI, Docker)

- Blueprint in `render.yaml` (`travel-system-api`), built from `backend/Dockerfile.api`.
- Health check: `GET /api/v1/health`.
- Pre-deploy: `alembic upgrade head` (uses `DATABASE_URL_DIRECT`).

## 5. Render worker + cron

- `travel-system-worker` runs the Celery worker.
- Crons (in `render.yaml`): outbox sync (`*/5`), daily reminders (`0 9 * * *`), nightly reconciliation (`0 2 * * *`).

## 6. Vercel (frontend)

- Root `frontend/`, build `npm run build`, output `dist/`.
- Set `VITE_API_BASE_URL` to the Render API URL.
- `vercel.json` provides SPA rewrites + security headers.

## 7. Wiring

- `CORS_ORIGINS` / `FRONTEND_URL` = Vercel domain(s).
- Register payment webhooks at `POST /api/v1/payments/webhooks/{provider}`.
- Custom domains + HTTPS on Render and Vercel.
- UI shows a "server waking up" paper-plane state while Render free tier boots.

## 8. Smoke test

```bash
python scripts/smoke_test.py https://<api>.onrender.com
```

## Key considerations

- Free tiers sleep (Render) and scale to zero (Neon) → cold-start retries everywhere.
- Render has no persistent disk → all files go to object storage; PDFs stored in the bucket.
- Secrets live only in Render/Vercel/Neon dashboards — never in the repo.
- Encryption key rotation via `ENCRYPTION_KEY` + optional `ENCRYPTION_KEY_PREVIOUS`.
