# Travel System - Architecture

## Folder Structure (Planned)

`
travel-system/
+-- backend/
¦   +-- app/
¦   ¦   +-- api/v1/          # REST endpoints (routers)
¦   ¦   +-- core/            # config, security, db, logging
¦   ¦   +-- models/          # SQLAlchemy models
¦   ¦   +-- schemas/         # Pydantic v2 schemas
¦   ¦   +-- services/        # business logic
¦   ¦   +-- repositories/    # data access
¦   ¦   +-- utils/           # helpers, encryption, validators
¦   ¦   +-- workers/         # Celery tasks (outbox, reminders, reconciliation)
¦   ¦   +-- middleware/      # audit, rate limiting
¦   ¦   +-- main.py
¦   +-- alembic/             # migrations
¦   +-- scripts/             # seed.py, smoke_test.py
¦   +-- tests/
¦   +-- pyproject.toml
¦   +-- Dockerfile.api
¦   +-- Dockerfile.worker
¦   +-- .env.example
+-- frontend/
¦   +-- src/
¦   ¦   +-- assets/brand/    # logo SVGs, favicon
¦   ¦   +-- components/     # Logo, UI components
¦   ¦   +-- config/          # theme, api
¦   ¦   +-- features/        # feature modules
¦   ¦   +-- hooks/
¦   ¦   +-- lib/
¦   ¦   +-- pages/
¦   ¦   +-- routes/
¦   ¦   +-- styles/          # theme.css
¦   ¦   +-- utils/
¦   ¦   +-- App.tsx
¦   +-- tailwind.config.ts
¦   +-- vite.config.ts
¦   +-- vercel.json
¦   +-- .env.example
+-- infra/
¦   +-- docker-compose.yml
¦   +-- render.yaml
¦   +-- github-workflows (or .github/workflows)
+-- docs/
¦   +-- DEPLOYMENT.md
+-- README.md
`

## Design Principles
- Modular (routers/services/repos/schemas)
- Type-safe end-to-end (TS strict + mypy)
- Security-first (encryption, masking, audit)
- Cloud-native for Render/Vercel/Neon
- Production-ready from day one
