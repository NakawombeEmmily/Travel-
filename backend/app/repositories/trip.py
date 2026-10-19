from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.trip import Trip
from app.repositories.base import BaseRepository


class TripRepository(BaseRepository[Trip]):
    model = Trip

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def search(
        self,
        *,
        client_id: Optional[UUID] = None,
        status: Optional[str] = None,
        q: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[tuple[Trip, Optional[str]]], int]:
        conditions = []
        if client_id:
            conditions.append(Trip.client_id == client_id)
        if status:
            conditions.append(Trip.status == status)
        if q:
            like = f"%{q}%"
            conditions.append(
                or_(
                    Trip.destination_country.ilike(like),
                    Client.full_name.ilike(like),
                )
            )

        base = select(Trip).join(Client, Trip.client_id == Client.id)
        count_stmt = (
            select(func.count()).select_from(Trip).join(
                Client, Trip.client_id == Client.id
            ).where(*conditions)
        )
        total = int((await self.session.execute(count_stmt)).scalar_one())

        stmt = (
            base.where(*conditions)
            .add_columns(Client.full_name)
            .order_by(Trip.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await self.session.execute(stmt)).all()
        return [(row[0], row[1]) for row in rows], total

    async def get_with_client(
        self, id_: UUID
    ) -> Optional[tuple[Trip, Optional[str]]]:
        stmt = (
            select(Trip)
            .join(Client, Trip.client_id == Client.id)
            .add_columns(Client.full_name)
            .where(Trip.id == id_)
        )
        row = (await self.session.execute(stmt)).first()
        return (row[0], row[1]) if row else None

    async def counts_by_status(self) -> dict[str, int]:
        stmt = select(Trip.status, func.count()).group_by(Trip.status)
        rows = (await self.session.execute(stmt)).all()
        return {status: int(count) for status, count in rows}

    async def get(self, id_: UUID) -> Optional[Trip]:
        return await self.session.get(Trip, id_)
