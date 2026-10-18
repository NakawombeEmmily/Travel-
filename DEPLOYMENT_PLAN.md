# Travel System - Deployment Plan (Following Hosting Sequence Exactly)

## Environments
- development (local: Docker Compose)
- staging (Neon staging branch, Render staging services, Vercel preview)
- production (Neon main branch, Render prod services, Vercel prod)

## 1. Neon (Database First)
- Create Neon project with branches: main, staging, dev
- Create schemas: crm and dmin in each branch
- Get pooled connection string (PgBouncer) for API/workers
- Get direct (non-pooled) connection string for Alembic migrations
- Configure SQLAlchemy: pool_pre_ping=True, pool_recycle=300, retry logic for cold starts (Neon scale-to-zero)
- Run migrations + seed on staging/dev only (never seed prod automatically)

## 2. Object Storage & Email
- S3-compatible: Cloudflare R2 (recommended, egress-free) or AWS S3
- Bucket: private, versioning optional, server-side encryption
- MinIO for local dev
- Email: Resend (prod), Mailpit (local). Provider-agnostic interface
- Store credentials as Render env vars

## 3. Render Key Value (Redis)
- Provision Render Key Value before API/worker
- Internal URL used for Celery broker, rate limiting (slowapi with Redis), caching

## 4. Render API Web Service (FastAPI)
- Deploy from Docker (Dockerfile.api)
- Includes system libs for PDF generation (weasyhtml/reportlab as needed)
- Health check: /api/v1/health
- Pre-deploy command: lembic upgrade head (uses DATABASE_URL_DIRECT)
- Env vars: DATABASE_URL (pooled), DATABASE_URL_DIRECT, ADMIN_DATABASE_URL, REDIS_URL, JWT_SECRET, ENCRYPTION_KEY, STORAGE_*, EMAIL_*, CORS_ORIGINS, FRONTEND_URL, ENVIRONMENT

## 5. Render Background Worker + Cron Jobs
- Worker service: outbox sync, email sending, reminders
- Cron jobs (Render cron): nightly reconciliation, daily visa/passport expiry reminders, daily revenue summary
- All in single ender.yaml blueprint for one-click deploy

## 6. Vercel Frontend
- Deploy /frontend with Vite preset
- VITE_API_BASE_URL = Render API URL
- ercel.json: SPA rewrites, security headers (CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy)
- Preview deployments for PRs point to staging API + Neon staging

## 7. Wiring
- CORS_ORIGINS and FRONTEND_URL set to Vercel domain(s)
- Payment webhook URLs registered with providers (point to Render API)
- Custom domains + HTTPS
- Server waking: frontend shows paper plane loading animation while backend wakes (free tiers sleep)

## 8. Smoke Test & Go Live
- scripts/smoke_test.py: checks health, login, client create/read, mock payment, admin ledger sync completion
- Run on production after wiring

## Key Considerations
- Free tiers sleep (Render), Neon scales to zero ? retry/backoff on cold starts
- No disk persistence on Render ? uploads to object storage, PDFs generated/stored in bucket
- Encryption key rotation supported (ENCRYPTION_KEY_CURRENT + ENCRYPTION_KEY_PREVIOUS if needed)
- Secrets only in Render/Vercel/Neon dashboards, never in repo
- Admin DB can be same Neon project (different schema) or separate connection (ADMIN_DATABASE_URL)
