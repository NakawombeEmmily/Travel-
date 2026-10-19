from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.visa import Visa, VisaStatusHistory
from app.repositories.base import BaseRepository


class VisaRepository(BaseRepository[Visa]):
    model = Visa

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def search(
        self,
        *,
        client_id: Optional[UUID] = None,
        trip_id: Optional[UUID] = None,
        status: Optional[str] = None,
        q: Optional[str] = None,
        page: int = 1,
        page_size: int = 100,
    ) -> tuple[list[tuple[Visa, Optional[str]]], int]:
        conditions = []
        if client_id:
            conditions.append(Visa.client_id == client_id)
        if trip_id:
            conditions.append(Visa.trip_id == trip_id)
        if status:
            conditions.append(Visa.status == status)
        if q:
            like = f"%{q}%"
            conditions.append(
                or_(
                    Visa.destination_country.ilike(like),
                    Visa.reference_number.ilike(like),
                    Client.full_name.ilike(like),
                )
            )

        count_stmt = (
            select(func.count()).select_from(Visa).join(
                Client, Visa.client_id == Client.id
            ).where(*conditions)
        )
        total = int((await self.session.execute(count_stmt)).scalar_one())

        stmt = (
            select(Visa)
            .join(Client, Visa.client_id == Client.id)
            .add_columns(Client.full_name)
            .where(*conditions)
            .order_by(Visa.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await self.session.execute(stmt)).all()
        return [(row[0], row[1]) for row in rows], total

    async def get_with_client(
        self, id_: UUID
    ) -> Optional[tuple[Visa, Optional[str]]]:
        stmt = (
            select(Visa)
            .join(Client, Visa.client_id == Client.id)
            .add_columns(Client.full_name)
            .where(Visa.id == id_)
        )
        row = (await self.session.execute(stmt)).first()
        return (row[0], row[1]) if row else None

    async def history(self, visa_id: UUID) -> list[VisaStatusHistory]:
        stmt = (
            select(VisaStatusHistory)
            .where(VisaStatusHistory.visa_id == visa_id)
            .order_by(VisaStatusHistory.changed_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def counts_by_status(self) -> dict[str, int]:
        stmt = select(Visa.status, func.count()).group_by(Visa.status)
        rows = (await self.session.execute(stmt)).all()
        return {status: int(count) for status, count in rows}

    async def get(self, id_: UUID) -> Optional[Visa]:
        return await self.session.get(Visa, id_)
