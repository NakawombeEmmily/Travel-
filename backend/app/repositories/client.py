from __future__ import annotations

from collections.abc import Sequence
from typing import Optional
from uuid import UUID

from sqlalchemy import ColumnElement, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.repositories.base import BaseRepository


class ClientRepository(BaseRepository[Client]):
    model = Client

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_passport_hash(self, passport_hash: str) -> Optional[Client]:
        stmt = select(Client).where(
            Client.passport_number_hash == passport_hash,
            Client.is_deleted.is_(False),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def search(
        self,
        *,
        q: Optional[str] = None,
        nationality: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        include_deleted: bool = False,
    ) -> tuple[Sequence[Client], int]:
        conditions: list[ColumnElement[bool]] = []
        if not include_deleted:
            conditions.append(Client.is_deleted.is_(False))
        if q:
            like = f"%{q}%"
            conditions.append(
                or_(
                    Client.full_name.ilike(like),
                    Client.email.ilike(like),
                    Client.phone.ilike(like),
                )
            )
        if nationality:
            conditions.append(Client.nationality == nationality)

        count_stmt = select(func.count()).select_from(Client).where(*conditions)
        total = int((await self.session.execute(count_stmt)).scalar_one())

        stmt = (
            select(Client)
            .where(*conditions)
            .order_by(Client.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    async def get(self, id_: UUID) -> Optional[Client]:
        return await self.session.get(Client, id_)
