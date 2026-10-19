# Phase 2: Hosting Setup — Step-by-Step (Neon, Render, Vercel)

This is the **exact hosting sequence** to follow with all required environment variables. Do **not** store secrets in code. Enter all values in each provider dashboard.

> **Status (Phase 6):** historical planning document, kept for the original
> environment-variable walkthrough. The authoritative guide is
> [DEPLOYMENT.md](DEPLOYMENT.md). In particular, production no longer runs a
> Celery worker or Redis: scheduled work runs as Render cron jobs invoking
> `python -m app.cli`, so the worker/Redis service tables below do not reflect
> production.

## 0. Prerequisites

- Git repo: https://github.com/NakawombeEmmily/Travel- (main)
- CLI access (optional): `gh`, `vercel`, `render` CLI (not required)
- Domains (optional): custom domains for API/frontend

---

## 1. Neon (Postgres 16) — Database first

Create project + branches + schemas + get pooled/direct URLs.

1. Go to [Neon Console](https://neon.tech/) → **Create project**
   - Project name: `travel-system`
   - Postgres version: 16
   - Region: closest to East Africa (or your primary region)

2. Create branches (Data → Branches)
   - `dev`
   - `staging`
   - `main` (production)

3. For **each branch**, create schemas `crm` and `admin`
   - SQL Editor → run:
     ```sql
     CREATE SCHEMA IF NOT EXISTS crm;
     CREATE SCHEMA IF NOT EXISTS admin;
     ```
   (Migrations run via Alembic on deploy, but creating schemas early is fine)

4. Get connection strings per branch (Connection Details → Connection string)
   - **Pooled** (PgBouncer) — use for app/workers (cold-start tolerant): 
     `postgresql+asyncpg://<user>:<pass>@<pooler>...neon.tech/<db>?ssl=require`
   - **Direct** (non-pooled) — use for Alembic migrations only:
     `postgresql+asyncpg://<user>:<pass>@<host>...neon.tech/<db>?ssl=require`

   > ⚠️ **Gotcha:** SQLAlchemy's `asyncpg` driver rejects `?sslmode=require`
   > (`TypeError: connect() got an unexpected keyword argument 'sslmode'`).
   > Always convert Neon's `sslmode=require` → **`ssl=require`** in every URL.
   > Also add `-pooler` to the host (`ep-xxx-pooler.<region>`) for the pooled URL.

   Save these for staging and production:
   | Branch | DATABASE_URL (pooled, asyncpg) | DATABASE_URL_DIRECT (direct, asyncpg) | ADMIN_DATABASE_URL (pooled) |
   |---|---|---|---|
   | dev | (local only) | (local only) | (local only) |
   | staging | `NEON_STAGING_POOLED` | `NEON_STAGING_DIRECT` | usually same DB, same pooled (schema `admin`) |
   | main | `NEON_PROD_POOLED` | `NEON_PROD_DIRECT` | `NEON_PROD_POOLED` (or separate if desired) |

> Note: For single-DB setup, `ADMIN_DATABASE_URL` can equal `DATABASE_URL` (different schemas `crm`/`admin`). This project expects both.

---

## 2. Cloudflare R2 (S3-compatible storage) — recommended

Render has no persistent disk; uploads/PDFs go here.

1. [Cloudflare R2](https://dash.cloudflare.com/) → R2 → Create bucket
   - Bucket name: `travel-system-prod` (or `travel-system-staging`)
   - Location: auto

2. Create API token (R2 → Manage R2 API Tokens → Create API token)
   - Permissions: Object Read & Write (and List if needed)
   - Save: `Account ID`, `Access Key ID`, `Secret Access Key`

3. Public access: keep **private**. No public bucket policy needed.

| Env var | Staging | Production |
|---|---|---|
| `STORAGE_ENDPOINT` | `s3.eu-west-1.cloudflarer2.com` (or your R2 endpoint) | same |
| `STORAGE_REGION` | `auto` | `auto` |
| `STORAGE_BUCKET` | `travel-system-staging` | `travel-system-prod` |
| `STORAGE_ACCESS_KEY` | R2 token access key | R2 token access key |
| `STORAGE_SECRET_KEY` | R2 token secret | R2 token secret |
| `STORAGE_USE_SSL` | `true` | `true` |

(Local dev: MinIO `localhost:9000`, `STORAGE_USE_SSL=false`.)

---

## 3. Email provider (Resend) — staging/prod

1. [Resend](https://resend.com/) → API Keys → Create API Key
   - Name: `travel-system-prod`
   - Scope: Full Access (or Sending)
   - Save `RESEND_API_KEY`

2. Verify sender domain (recommended) or use test sender for staging: `onboarding@resend.dev` is fine for testing.

| Env var | Staging | Production |
|---|---|---|
| `EMAIL_PROVIDER` | `resend` | `resend` |
| `EMAIL_FROM` | `"Travel System" <noreply@yourdomain.com>` | `"Travel System" <noreply@yourdomain.com>` |
| `RESEND_API_KEY` | Resend API key (staging) | Resend API key (prod) |

(Local: `EMAIL_PROVIDER=mailpit`, `EMAIL_FROM="Travel System <noreply@localhost>"`.)

---

## 4. Render Key Value (Redis) — broker/cache

1. [Render Dashboard](https://dashboard.render.com/) → **New + → Key Value**
   - Name: `travel-system-redis`
   - Instance type: Starter (sufficient for Phase 1–4)
   - Region: same region as API
   - Create

2. After creation, Render exposes `REDIS_URL` internally. In `render.yaml` it’s wired via `fromService` (you don’t need to paste manually for services). For cron jobs in the blueprint we reference sync fields; in practice Render injects Redis URL if you also attach or just set `REDIS_URL` from the Redis instance in the dashboard if needed. The provided `render.yaml` uses `fromService` for API/worker (recommended).

> Note: Cron jobs in Render Docker can reuse env; ensure `REDIS_URL` is set for worker/crons that may enqueue tasks (reminders). If using the blueprint, Render will provision Redis first.

---

## 5. Render — Deploy API, Worker, Cron Jobs (using render.yaml)

Render Blueprint deploys all three (API, worker, crons) + Redis reference.

### Option A: Blueprint deploy (recommended, one-click)

1. Push to GitHub (done: `a384a73` on `main`)
2. Render → **New + → Blueprint**
3. Connect repo: `NakawombeEmmily/Travel-`
4. Branch: `main`
5. Render will detect `render.yaml` in root. Review services:
   - `travel-system-api` (web, Docker)
   - `travel-system-worker` (background worker, Docker)
   - `travel-system-redis` (Key Value) — created or referenced
   - Crons: `travel-system-outbox-sync`, `travel-system-reminders`, `travel-system-reconciliation`

6. Click **Apply**. It will create resources and fail pre-deploy until env vars set (expected). Proceed to Step 6 to fill env vars.

### Option B: Manual (if blueprint edits needed) — not necessary

Blueprint is included.

---

## 6. Render — Environment variables (staging + production)

Set per environment (use separate Render services for staging/prod: create second blueprint or duplicate services, pointing to `staging` branch + Neon staging).

### 6.1 `travel-system-api` (Web Service)

| Key | Value | Notes |
|---|---|---|
| `ENVIRONMENT` | `production` (or `staging`) | staging → `staging` |
| `DATABASE_URL` | Neon **pooled** URL (asyncpg) | e.g. `postgresql+asyncpg://...pooler.neon.tech/<db>?ssl=require` |
| `DATABASE_URL_DIRECT` | Neon **direct** URL (asyncpg) | used by `alembic upgrade head` pre-deploy |
| `ADMIN_DATABASE_URL` | Neon pooled URL | same DB or separate; schemas `admin` |
| `REDIS_URL` | (auto if fromService) or Redis internal URL | blueprint uses fromService |
| `SECRET_KEY` | random 32+ chars | generate (Render can auto-generate) |
| `JWT_SECRET` | random 32+ chars | generate |
| `JWT_REFRESH_SECRET` | random 48+ chars | generate (separate) |
| `ENCRYPTION_KEY` | base64url of **32-byte** key | `python -c "import os,base64;print(base64.urlsafe_b64encode(os.urandom(32)).decode())"` |
| `ENCRYPTION_KEY_PREVIOUS` | (optional) | for rotation later |
| `CORS_ORIGINS` | Vercel prod origins (comma-separated) | e.g. `https://travel-system.vercel.app,https://yourdomain.com` (staging preview: include preview URLs) |
| `FRONTEND_URL` | `https://travel-system.vercel.app` | prod frontend URL |
| `ALLOWED_HOSTS` | `*` (or Render URL + custom API) | can keep `*` behind HTTPS + CORS |
| `STORAGE_ENDPOINT` | R2 endpoint | see Step 2 |
| `STORAGE_REGION` | `auto` | R2 |
| `STORAGE_BUCKET` | bucket name | staging/prod bucket |
| `STORAGE_ACCESS_KEY` | R2 access key | |
| `STORAGE_SECRET_KEY` | R2 secret key | |
| `STORAGE_USE_SSL` | `true` | |
| `EMAIL_PROVIDER` | `resend` | |
| `EMAIL_FROM` | sender address | `"Travel System" <noreply@yourdomain.com>` |
| `RESEND_API_KEY` | Resend key | |
| `BASE_CURRENCY` | `UGX` | company base currency |
| `LOG_LEVEL` | `INFO` | `DEBUG` for staging if needed |

> Generate `ENCRYPTION_KEY` (32-byte base64url): 
```bash
python3 -c "import os,base64; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"
```

### 6.2 `travel-system-worker` (Background Worker)

Same secrets as API (DB/Redis/storage/email/keys). Do **not** duplicate unnecessarily; Render lets you inherit or set same values.

| Key | Value |
|---|---|
| `ENVIRONMENT` | `production`/`staging` |
| `DATABASE_URL` | Neon pooled |
| `ADMIN_DATABASE_URL` | Neon pooled |
| `REDIS_URL` | fromService (blueprint) |
| `ENCRYPTION_KEY` | same as API |
| `STORAGE_ENDPOINT`, `STORAGE_REGION`, `STORAGE_BUCKET`, `STORAGE_ACCESS_KEY`, `STORAGE_SECRET_KEY`, `STORAGE_USE_SSL` | same |
| `EMAIL_PROVIDER`, `EMAIL_FROM`, `RESEND_API_KEY` | same |
| `SECRET_KEY`, `JWT_SECRET`, `JWT_REFRESH_SECRET` | same (worker may need if tasks decode tokens) |
| `BASE_CURRENCY` | `UGX` |

### 6.3 Cron Jobs

Crons run Docker worker image with specific commands. Set required env per cron (at minimum DB/Redis). Blueprint includes placeholders; in Render UI → Cron Jobs → Environment, add:

| Cron | Required | Notes |
|---|---|---|
| `travel-system-outbox-sync` | `DATABASE_URL`, `ADMIN_DATABASE_URL`, `REDIS_URL`, `ENCRYPTION_KEY`, `BASE_CURRENCY` | syncs CRM payments → admin ledger |
| `travel-system-reminders` | `DATABASE_URL`, `REDIS_URL`, `EMAIL_PROVIDER`, `EMAIL_FROM`, `RESEND_API_KEY` | visa/passport reminders |
| `travel-system-reconciliation` | `DATABASE_URL`, `ADMIN_DATABASE_URL`, `BASE_CURRENCY` | nightly reconciliation |

(You can also set shared env vars at service level.)

---

## 7. Vercel — Frontend deploy

1. Go to [Vercel](https://vercel.com/) → **Add New… → Project**
2. Import Git repo: `NakawombeEmmily/Travel-`
3. Framework Preset: **Vite**
4. Root Directory: `frontend`
5. Build Command: `npm run build` (auto-detected)
6. Output Directory: `dist` (auto-detected)
7. Install Command: `npm install` (auto-detected)

### 7.1 Environment variables (Vercel)

Project → Settings → Environment Variables:

| Key | Value | Environments |
|---|---|---|
| `VITE_API_BASE_URL` | Render API URL | Production, Preview, Development |
| `VITE_ENVIRONMENT` | `production` / `staging` / `development` | map per env |
| `VITE_BRAND_NAME` | `Travel System` | all |

Render API URL: e.g. `https://travel-system-api.onrender.com` (shown after API web service deploys). For Preview (PRs), point to staging API if you have a staging Render service.

> `vercel.json` (already committed) handles SPA rewrites + security headers (CSP allows `connect-src` to `*.onrender.com`).

### 7.2 Deploy

- Push to `main` → Production deploy
- PRs → Preview deployments (use staging API for Preview if desired)

---

## 8. Post-deploy wiring & verification

### 8.1 Run migrations (automatic)

API has `preDeployCommand: alembic upgrade head` (uses `DATABASE_URL_DIRECT`). After first successful deploy, confirm tables exist in Neon (`crm.users`, `crm.clients`, `crm.audit_log`).

### 8.2 CORS

Ensure `CORS_ORIGINS` includes Vercel production domain(s) and any custom domains. Also `FRONTEND_URL` matches frontend.

### 8.3 Health check

```bash
curl https://<your-api>.onrender.com/api/v1/health
# expect: {"status":"healthy","environment":"production","version":"0.1.0","db":"ok"}
```

### 8.4 Seed (dev/staging only)

Seed script is guarded: refuses if `ENVIRONMENT` not in `{development,dev,staging,test}`.

- Local: `make seed` (uses backend/.env)
- Staging Render: run one-off job or shell in worker? Or `python scripts/seed.py` via Render shell/cron one-off. **Never run on production**.
  - Render → Worker/Job → Run one-off command: `cd /app && python ../scripts/seed.py` (if mounted) or `python scripts/seed.py` from backend context. With Docker image, `cd /app && python scripts/seed.py` (paths vary). Safer: create a one-off job service or run in API shell (Render “Shell”).

Default seed creates `admin@example.com` / `Admin123!` (dev/staging). **Change password immediately in staging/prod if kept.**

### 8.5 Smoke test

```bash
python scripts/smoke_test.py https://<your-api>.onrender.com
```
Expected: health, login, list clients, create client → all PASS.

### 8.6 Frontend wake-up

On first load (free tier cold start), app shows paper-plane “Waking up server…” and polls `/health` every 3s until healthy, then logs in. This matches requirements.

---

## 9. Staging vs Production (recommended split)

Create **two Render environments** (separate web/worker services):

- **Staging**: branch `staging`, Neon staging branch, separate R2 bucket, Resend test keys, Vercel Preview points to staging API.
- **Production**: branch `main`, Neon main, prod R2/Resend, Vercel Production.

Blueprint can be reused (change `ENVIRONMENT`, branch, env vars).

---

## 10. Security checklist

- [ ] Secrets only in Render/Vercel/Neon (no `.env` committed)
- [ ] `ENCRYPTION_KEY` is 32-byte base64url, unique per environment
- [ ] Rotate `JWT_*` and `SECRET_KEY` if leaked (don’t reuse across envs)
- [ ] R2 bucket private, no public access
- [ ] CORS restricted to Vercel domains
- [ ] HTTPS enforced (Render/Vercel default)
- [ ] Admin password changed from seed in non-dev
- [ ] Backups enabled on Neon (default on paid; note free tier)

---

## 11. Troubleshooting (cold starts)

- Neon scale-to-zero: first query may take ~1–2s; SQLAlchemy `pool_pre_ping` + retry/backoff handles.
- Render free tier sleeps: frontend wake-up state + API health polling is implemented.
- Migrations: pre-deploy uses `DATABASE_URL_DIRECT` (non-pooled) — required for Alembic.

If health returns `degraded`, check DB connectivity in logs (Render → API → Logs).

---

**End of Phase 2.** After completing these steps, run smoke tests in staging, then promote to production.