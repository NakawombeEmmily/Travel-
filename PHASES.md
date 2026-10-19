# Travel System - Phases Overview

All six phases are delivered; see the status table in [README.md](README.md).

## Phase 1: Setup, Core Foundation & App Shell
**Focus**: Scaffolding, Neon config, auth+RBAC, clients, audit log, theme tokens, logo, app shell

## Phase 2: Trips, Visas, Documents, Reminders
- Trips CRUD and linking to clients
- Visa tracking with kanban board
- Document uploads (encrypted, S3)
- Reminder system (email) + Celery tasks
- Visa status history

## Phase 3: Feedback & CRM
- Feedback with sentiment calculation
- Interaction log
- Lead pipeline (kanban)
- Tags/segments, follow-up tasks
- CRM dashboard widgets

## Phase 4: Payments, Outbox Sync, Invoices, Reconciliation
- Payments with instalments, partial payments
- PaymentProvider interface + mock + stubs
- Transactional outbox + worker
- PDF invoices/receipts generation
- Admin ledger sync
- Nightly reconciliation + retry endpoint

## Phase 5: Analytics
- Dashboard analytics (ratings, conversion, nationality breakdown, visa approval rate)
- Revenue summary views
- CSV export improvements

## Phase 6: Deployment (Hosting Sequence), Hardening, CI
- Apply full deployment sequence
- render.yaml, vercel.json, Dockerfiles
- GitHub Actions (lint, typecheck, test, deploy)
- Smoke test
- Final docs
