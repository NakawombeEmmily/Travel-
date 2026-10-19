from __future__ import annotations

from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead
from app.repositories.base import BaseRepository


class LeadRepository(BaseRepository[Lead]):
    model = Lead

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def search(
        self,
        *,
        status: Optional[str] = None,
        q: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Lead], int]:
        conditions = []
        if status:
            conditions.append(Lead.status == status)
        if q:
            like = f"%{q}%"
            conditions.append(
                or_(
                    Lead.full_name.ilike(like),
                    Lead.email.ilike(like),
                    Lead.phone.ilike(like),
                )
            )

        count_stmt = select(func.count()).select_from(Lead).where(*conditions)
        total = int((await self.session.execute(count_stmt)).scalar_one())

        stmt = (
            select(Lead)
            .where(*conditions)
            .order_by(Lead.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await self.session.execute(stmt)).scalars().all()
        return list(rows), total

    async def counts_by_status(self) -> dict[str, int]:
        stmt = select(Lead.status, func.count()).group_by(Lead.status)
        rows = (await self.session.execute(stmt)).all()
        return {key: int(count) for key, count in rows if key is not None}
