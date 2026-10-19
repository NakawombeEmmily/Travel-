from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_client_ip, get_current_user, get_session
from app.core.config import settings
from app.models.user import User, UserRole
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
    UserRead,
)
from app.services.audit import record_audit
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenPair)
async def login(
    payload: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> TokenPair:
    service = AuthService(session)
    user = await service.authenticate(payload.email, payload.password)
    if user is None:
        await record_audit(
            session,
            action="login",
            entity_type="user",
            ip_address=get_client_ip(request),
            metadata={"email": payload.email, "success": False},
        )
        await session.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    access, refresh = await service.issue_tokens(user)
    await record_audit(
        session,
        action="login",
        entity_type="user",
        actor_id=user.id,
        entity_id=user.id,
        ip_address=get_client_ip(request),
        metadata={"success": True},
    )
    await session.commit()
    return TokenPair(access_token=access, refresh_token=refresh)


@router.post(
    "/register", response_model=TokenPair, status_code=status.HTTP_201_CREATED
)
async def register(
    payload: RegisterRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> TokenPair:
    if not settings.ALLOW_SELF_REGISTRATION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Self-registration is disabled",
        )
    if settings.REGISTRATION_CODE and (
        payload.registration_code != settings.REGISTRATION_CODE
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid registration code",
        )

    service = AuthService(session)
    if await service.repo.get_by_email(str(payload.email)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    role = UserRole(settings.REGISTRATION_DEFAULT_ROLE)
    user = await service.register(
        email=str(payload.email),
        full_name=payload.full_name,
        password=payload.password,
        role=role,
    )
    await record_audit(
        session,
        action="register",
        entity_type="user",
        actor_id=user.id,
        entity_id=user.id,
        ip_address=get_client_ip(request),
        metadata={"email": user.email, "role": role.value},
    )
    await session.commit()
    access, refresh = await service.issue_tokens(user)
    return TokenPair(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenPair)
async def refresh(
    payload: RefreshRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenPair:
    service = AuthService(session)
    user = await service.refresh(payload.refresh_token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    access, new_refresh = await service.issue_tokens(user)
    return TokenPair(access_token=access, refresh_token=new_refresh)


@router.get("/me", response_model=UserRead)
async def me(user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(user)
