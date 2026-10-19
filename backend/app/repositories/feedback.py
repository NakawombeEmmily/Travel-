from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.feedback import Feedback
from app.repositories.base import BaseRepository


class FeedbackRepository(BaseRepository[Feedback]):
    model = Feedback

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def search(
        self,
        *,
        client_id: Optional[UUID] = None,
        sentiment: Optional[str] = None,
        category: Optional[str] = None,
        q: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[tuple[Feedback, Optional[str]]], int]:
        conditions = []
        if client_id:
            conditions.append(Feedback.client_id == client_id)
        if sentiment:
            conditions.append(Feedback.sentiment == sentiment)
        if category:
            conditions.append(Feedback.category == category)
        if q:
            like = f"%{q}%"
            conditions.append(
                or_(Client.full_name.ilike(like), Feedback.comment.ilike(like))
            )

        base = select(Feedback).join(Client, Feedback.client_id == Client.id)
        count_stmt = (
            select(func.count())
            .select_from(Feedback)
            .join(Client, Feedback.client_id == Client.id)
            .where(*conditions)
        )
        total = int((await self.session.execute(count_stmt)).scalar_one())

        stmt = (
            base.where(*conditions)
            .add_columns(Client.full_name)
            .order_by(Feedback.feedback_date.desc(), Feedback.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await self.session.execute(stmt)).all()
        return [(row[0], row[1]) for row in rows], total

    async def get_with_client(
        self, id_: UUID
    ) -> Optional[tuple[Feedback, Optional[str]]]:
        stmt = (
            select(Feedback)
            .join(Client, Feedback.client_id == Client.id)
            .add_columns(Client.full_name)
            .where(Feedback.id == id_)
        )
        row = (await self.session.execute(stmt)).first()
        return (row[0], row[1]) if row else None

    async def average_rating(self) -> tuple[int, float]:
        stmt = select(func.count(), func.coalesce(func.avg(Feedback.rating), 0))
        row = (await self.session.execute(stmt)).one()
        return int(row[0]), float(row[1])

    async def counts_by_sentiment(self) -> dict[str, int]:
        stmt = select(Feedback.sentiment, func.count()).group_by(Feedback.sentiment)
        rows = (await self.session.execute(stmt)).all()
        return {key: int(count) for key, count in rows if key is not None}

    async def counts_by_category(self) -> dict[str, int]:
        stmt = select(Feedback.category, func.count()).group_by(Feedback.category)
        rows = (await self.session.execute(stmt)).all()
        return {key: int(count) for key, count in rows if key is not None}
