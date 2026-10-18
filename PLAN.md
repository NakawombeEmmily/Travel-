# Travel System - Complete Plan

## PHASE 1: Setup, Core Foundation & App Shell

### Goals
- Project scaffolding with proper structure
- Environment configuration (dev/staging/prod)
- Neon PostgreSQL connection with crm/admin schemas
- Auth system (JWT access+refresh, RBAC)
- Client management core
- Audit logging
- Theme tokens (orange theme + dark mode)
- Paper plane logo + favicon + Logo component
- Basic app shell (frontend + backend skeleton)

### Deliverables
- Backend: FastAPI app with config, db, auth, users/roles, clients, audit
- Frontend: Vite + React + TS + Tailwind with theme and shell
- Migrations: Alembic setup with initial schema
- Config: .env.example (backend/frontend), Docker Compose
- Theme: tailwind.config.ts, theme.css, Logo component and assets

### Tasks
1. Backend scaffolding (app/, core/, api/v1/, models/, schemas/, services/, repos/, utils)
2. Database setup (Neon pooled/direct, SQLAlchemy 2.0, Alembic)
3. Auth & RBAC (argon2, JWT, roles/permissions)
4. Audit log middleware + service
5. Client model with encryption (passport) + hash
6. Theme tokens + CSS variables (orange palette + dark mode)
7. Logo SVG assets + Logo.tsx + favicon generation
8. Frontend app shell with sidebar, navbar, login
9. Docker Compose for local dev (api, worker, redis, minio, mailpit, postgres)
10. Initial migration + seed script (dev/staging safe)

### Success Criteria
- Tests for auth and clients pass
- Migrations run successfully
- Theme tokens defined once
- Logo renders in all required variants
- App shell works locally
