from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.interaction import Interaction
from app.repositories.base import BaseRepository


class InteractionRepository(BaseRepository[Interaction]):
    model = Interaction

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def search(
        self,
        *,
        client_id: Optional[UUID] = None,
        interaction_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[tuple[Interaction, Optional[str]]], int]:
        conditions = []
        if client_id:
            conditions.append(Interaction.client_id == client_id)
        if interaction_type:
            conditions.append(Interaction.interaction_type == interaction_type)

        base = select(Interaction).join(Client, Interaction.client_id == Client.id)
        count_stmt = (
            select(func.count())
            .select_from(Interaction)
            .join(Client, Interaction.client_id == Client.id)
            .where(*conditions)
        )
        total = int((await self.session.execute(count_stmt)).scalar_one())

        stmt = (
            base.where(*conditions)
            .add_columns(Client.full_name)
            .order_by(Interaction.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await self.session.execute(stmt)).all()
        return [(row[0], row[1]) for row in rows], total

    async def get_with_client(
        self, id_: UUID
    ) -> Optional[tuple[Interaction, Optional[str]]]:
        stmt = (
            select(Interaction)
            .join(Client, Interaction.client_id == Client.id)
            .add_columns(Client.full_name)
            .where(Interaction.id == id_)
        )
        row = (await self.session.execute(stmt)).first()
        return (row[0], row[1]) if row else None
