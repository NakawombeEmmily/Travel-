from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    auth,
    clients,
    dashboard,
    documents,
    health,
    reminders,
    trips,
    visas,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(clients.router)
api_router.include_router(trips.router)
api_router.include_router(visas.router)
api_router.include_router(documents.router)
api_router.include_router(dashboard.router)
api_router.include_router(reminders.router)
