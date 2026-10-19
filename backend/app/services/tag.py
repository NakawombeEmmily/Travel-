from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.tag import Tag
from app.repositories.tag import TagRepository
from app.schemas.tag import TagCreate, TagRead, TagUpdate
from app.services.exceptions import ClientNotFoundError, ConflictError, NotFoundError


class TagService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = TagRepository(session)

    def to_read(self, item: Tag) -> TagRead:
        return TagRead.model_validate(item)

    async def list_tags(self) -> list[TagRead]:
        return [self.to_read(t) for t in await self.repo.list_ordered()]

    async def create(self, payload: TagCreate) -> Tag:
        if await self.repo.get_by_name(payload.name) is not None:
            raise ConflictError(f"Tag '{payload.name}' already exists")
        tag = Tag(name=payload.name, color=payload.color)
        await self.repo.add(tag)
        return tag

    async def update(self, tag: Tag, payload: TagUpdate) -> Tag:
        data = payload.model_dump(exclude_unset=True)
        new_name = data.get("name")
        if new_name and new_name != tag.name:
            existing = await self.repo.get_by_name(new_name)
            if existing is not None and existing.id != tag.id:
                raise ConflictError(f"Tag '{new_name}' already exists")
        for key, value in data.items():
            setattr(tag, key, value)
        await self.session.flush()
        return tag

    async def delete(self, tag: Tag) -> None:
        await self.session.delete(tag)

    async def _ensure_client(self, client_id: UUID) -> None:
        client = await self.session.get(Client, client_id)
        if client is None or client.is_deleted:
            raise ClientNotFoundError(str(client_id))

    async def tags_for_client(self, client_id: UUID) -> list[TagRead]:
        return [self.to_read(t) for t in await self.repo.tags_for_client(client_id)]

    async def attach(self, client_id: UUID, tag_id: UUID) -> None:
        await self._ensure_client(client_id)
        if await self.repo.get(tag_id) is None:
            raise NotFoundError(f"Tag {tag_id} not found")
        await self.repo.attach(client_id, tag_id)

    async def detach(self, client_id: UUID, tag_id: UUID) -> None:
        await self._ensure_client(client_id)
        removed = await self.repo.detach(client_id, tag_id)
        if not removed:
            raise NotFoundError(f"Tag {tag_id} not attached to client {client_id}")
