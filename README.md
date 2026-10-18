# Travel System

Internal client management & CRM platform for a travel company. Employees enter and manage client data (no public client portal). Includes automatic payment syncing to the company admin database (later phases).

## Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, Celery
- **Frontend**: React + Vite + TypeScript (strict) + Tailwind, orange design tokens, dark mode
- **Data**: PostgreSQL 16 (Neon) with `crm` and `admin` schemas; Redis (Render KV)
- **Infra**: Render (API/worker/cron), Vercel (frontend), Cloudflare R2/MinIO, Resend/Mailpit

## Architecture

```mermaid
flowchart LR
  subgraph Client
    FE[Vercel Frontend<br/>React + Vite]
  end
  subgraph Render
    API[FastAPI API]
    W[Celery Worker]
    C[Render Crons]
    R[(Redis KV)]
  end
  subgraph Neon
    CRM[(crm schema)]
    ADMIN[(admin schema)]
  end
  subgraph Storage
    S3[(R2 / MinIO)]
    EM[Resend / Mailpit]
  end
  FE -->|VITE_API_BASE_URL| API
  API --> CRM
  API --> S3
  API --> EM
  API --> R
  W --> CRM
  W --> ADMIN
  C --> W
  W --> EM
  API --"outbox events"|> W
```

## Quickstart (local)

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
make up           # postgres, redis, minio, mailpit, api, worker, frontend
# or run pieces:
make api          # uvicorn on :8000
make test         # backend pytest
```

API docs: http://localhost:8000/docs

## Phase 1 status

- [x] Backend skeleton, config, DB session
- [x] Auth (JWT access+refresh) + RBAC roles
- [x] Clients with AES-256-GCM passport encryption, hash lookups, masking, soft delete, search/pagination
- [x] Audit logging (create/read/update/delete/reveal)
- [x] Alembic migration creating `crm` + `admin` schemas, users/audit/clients
- [x] Orange theme tokens + dark mode + paper-plane logo
- [x] Frontend app shell, login, clients page, waking-up state
- [x] Docker Compose, render.yaml, vercel.json, CI, seed, smoke test

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) and [docs/ERD.md](docs/ERD.md).

## Roadmap

- Phase 2: trips, visas, documents, reminders
- Phase 3: feedback & CRM pipeline
- Phase 4: payments, outbox sync, invoices, reconciliation
- Phase 5: analytics
- Phase 6: hardening + production deploy
