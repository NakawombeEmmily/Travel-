from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session, require_roles
from app.models.user import User, UserRole
from app.services.audit import record_audit
from app.services.reminders import collect_reminders, run_reminders

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.get("/preview")
async def preview_reminders(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return await collect_reminders(session)


@router.post("/run")
async def trigger_reminders(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(
        require_roles(UserRole.super_admin, UserRole.admin)
    ),
) -> dict[str, Any]:
    result = await run_reminders(session)
    await record_audit(
        session,
        action="run",
        entity_type="reminders",
        actor_id=user.id,
        metadata=result,
    )
    await session.commit()
    return result
