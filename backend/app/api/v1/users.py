from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_client_ip, get_session, require_roles
from app.models.user import User, UserRole
from app.repositories.user import UserRepository
from app.schemas.auth import UserRead, UserRoleUpdate
from app.services.audit import record_audit

router = APIRouter(prefix="/users", tags=["users"])

MANAGER_ROLES = (UserRole.super_admin, UserRole.admin)


async def _get_user(session: AsyncSession, user_id: UUID) -> User:
    user = await UserRepository(session).get(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.get("", response_model=list[UserRead])
async def list_users(
    session: AsyncSession = Depends(get_session),
    actor: User = Depends(require_roles(*MANAGER_ROLES)),
) -> list[UserRead]:
    users = await UserRepository(session).list_ordered()
    return [UserRead.model_validate(user) for user in users]


@router.patch("/{user_id}/role", response_model=UserRead)
async def update_user_role(
    user_id: UUID,
    payload: UserRoleUpdate,
    request: Request,
    session: AsyncSession = Depends(get_session),
    actor: User = Depends(require_roles(*MANAGER_ROLES)),
) -> UserRead:
    target = await _get_user(session, user_id)

    if target.id == actor.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot change your own role",
        )
    if target.role == UserRole.super_admin and actor.role != UserRole.super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only a super admin can change a super admin",
        )
    if payload.role == UserRole.super_admin and actor.role != UserRole.super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only a super admin can assign the super admin role",
        )
    if target.role == payload.role:
        return UserRead.model_validate(target)

    previous_role = target.role
    target.role = payload.role
    await record_audit(
        session,
        action="update_role",
        entity_type="user",
        actor_id=actor.id,
        entity_id=target.id,
        ip_address=get_client_ip(request),
        metadata={"from": previous_role.value, "to": payload.role.value},
    )
    await session.commit()
    await session.refresh(target)
    return UserRead.model_validate(target)
