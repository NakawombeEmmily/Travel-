from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.passwords import hash_password, verify_password
from app.core.security.tokens import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.models.user import User, UserRole
from app.repositories.user import UserRepository


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = UserRepository(session)

    async def authenticate(self, email: str, password: str) -> Optional[User]:
        user = await self.repo.get_by_email(email)
        if user is None or not user.is_active:
            return None
        if not verify_password(password, user.password_hash):
            return None
        user.last_login_at = datetime.now(timezone.utc)
        await self.repo.session.flush()
        return user

    async def register(
        self, *, email: str, full_name: str, password: str, role: UserRole
    ) -> User:
        user = User(
            email=email.lower(),
            full_name=full_name.strip(),
            password_hash=hash_password(password),
            role=role,
            is_active=True,
            assigned_clients_only=False,
        )
        self.repo.session.add(user)
        await self.repo.session.flush()
        return user

    async def issue_tokens(self, user: User) -> tuple[str, str]:
        access = create_access_token(str(user.id), user.role.value)
        refresh = create_refresh_token(str(user.id), user.role.value)
        return access, refresh

    async def refresh(self, refresh_token: str) -> Optional[User]:
        try:
            payload = decode_refresh_token(refresh_token)
        except Exception:
            return None
        if payload.get("type") != "refresh":
            return None
        subject = payload.get("sub")
        if not subject:
            return None
        user = await self.repo.get(UUID(subject))
        if user is None or not user.is_active:
            return None
        return user
