from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    analytics,
    auth,
    clients,
    dashboard,
    documents,
    feedback,
    health,
    interactions,
    leads,
    payments,
    reminders,
    tags,
    tasks,
    trips,
    users,
    visas,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(clients.router)
api_router.include_router(trips.router)
api_router.include_router(visas.router)
api_router.include_router(documents.router)
api_router.include_router(feedback.router)
api_router.include_router(interactions.router)
api_router.include_router(leads.router)
api_router.include_router(tags.router)
api_router.include_router(tasks.router)
api_router.include_router(payments.router)
api_router.include_router(analytics.router)
api_router.include_router(dashboard.router)
api_router.include_router(reminders.router)
