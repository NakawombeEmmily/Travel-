from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.models.user import User
from app.schemas.dashboard import DashboardSummary
from app.services.dashboard import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
async def summary(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> DashboardSummary:
    return await DashboardService(session).summary()
