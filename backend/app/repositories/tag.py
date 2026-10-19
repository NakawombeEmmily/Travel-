from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import ClientTag, Tag
from app.repositories.base import BaseRepository


class TagRepository(BaseRepository[Tag]):
    model = Tag

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def list_ordered(self) -> list[Tag]:
        stmt = select(Tag).order_by(Tag.name.asc())
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_by_name(self, name: str) -> Optional[Tag]:
        stmt = select(Tag).where(Tag.name == name)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def tags_for_client(self, client_id: UUID) -> list[Tag]:
        stmt = (
            select(Tag)
            .join(ClientTag, ClientTag.tag_id == Tag.id)
            .where(ClientTag.client_id == client_id)
            .order_by(Tag.name.asc())
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def attach(self, client_id: UUID, tag_id: UUID) -> None:
        existing = await self.session.get(ClientTag, (client_id, tag_id))
        if existing is not None:
            return
        self.session.add(ClientTag(client_id=client_id, tag_id=tag_id))
        await self.session.flush()

    async def detach(self, client_id: UUID, tag_id: UUID) -> bool:
        existing = await self.session.get(ClientTag, (client_id, tag_id))
        if existing is None:
            return False
        await self.session.delete(existing)
        await self.session.flush()
        return True
