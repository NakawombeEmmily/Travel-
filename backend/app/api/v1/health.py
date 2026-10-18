from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import get_session
from app.core.config import settings
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    db_ok = True
    try:
        await session.execute(text("SELECT 1"))
    except Exception:  # pragma: no cover - depends on live db
        db_ok = False
    return {
        "status": "healthy" if db_ok else "degraded",
        "environment": settings.ENVIRONMENT,
        "version": "0.1.0",
        "db": "ok" if db_ok else "error",
    }
