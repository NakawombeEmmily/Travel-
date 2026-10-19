from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.interaction import Interaction
from app.repositories.interaction import InteractionRepository
from app.schemas.interaction import (
    InteractionCreate,
    InteractionRead,
    InteractionUpdate,
)
from app.services.exceptions import ClientNotFoundError


class InteractionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = InteractionRepository(session)

    def to_read(
        self, item: Interaction, client_name: Optional[str] = None
    ) -> InteractionRead:
        read = InteractionRead.model_validate(item)
        read.client_name = client_name
        return read

    async def _ensure_client(self, client_id: UUID) -> None:
        client = await self.session.get(Client, client_id)
        if client is None or client.is_deleted:
            raise ClientNotFoundError(str(client_id))

    async def create(
        self, payload: InteractionCreate, *, actor_id: Optional[UUID] = None
    ) -> Interaction:
        await self._ensure_client(payload.client_id)
        item = Interaction(
            client_id=payload.client_id,
            interaction_type=payload.interaction_type.value,
            notes=payload.notes,
            follow_up_date=payload.follow_up_date,
            contacted_by=actor_id,
        )
        await self.repo.add(item)
        return item

    async def update(
        self, item: Interaction, payload: InteractionUpdate
    ) -> Interaction:
        data = payload.model_dump(exclude_unset=True)
        if data.get("interaction_type") is not None:
            data["interaction_type"] = data["interaction_type"].value
        for key, value in data.items():
            setattr(item, key, value)
        await self.session.flush()
        return item

    async def delete(self, item: Interaction) -> None:
        await self.session.delete(item)

    async def search(
        self,
        *,
        client_id: Optional[UUID] = None,
        interaction_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[InteractionRead], int]:
        rows, total = await self.repo.search(
            client_id=client_id,
            interaction_type=interaction_type,
            page=page,
            page_size=page_size,
        )
        return [self.to_read(item, name) for item, name in rows], total
