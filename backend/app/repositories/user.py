from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email.lower())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get(self, id_: UUID) -> Optional[User]:
        return await self.session.get(User, id_)

    async def list_ordered(self) -> list[User]:
        stmt = select(User).order_by(User.created_at.asc(), User.email.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
