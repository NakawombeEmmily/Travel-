from __future__ import annotations

from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.task import FollowUpTask, TaskStatus
from app.repositories.base import BaseRepository

OPEN_STATUSES = {TaskStatus.pending.value, TaskStatus.in_progress.value}


class TaskRepository(BaseRepository[FollowUpTask]):
    model = FollowUpTask

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def search(
        self,
        *,
        client_id: Optional[UUID] = None,
        status: Optional[str] = None,
        assigned_to: Optional[UUID] = None,
        q: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[tuple[FollowUpTask, Optional[str]]], int]:
        conditions = []
        if client_id:
            conditions.append(FollowUpTask.client_id == client_id)
        if status:
            conditions.append(FollowUpTask.status == status)
        if assigned_to:
            conditions.append(FollowUpTask.assigned_to == assigned_to)
        if q:
            like = f"%{q}%"
            conditions.append(
                or_(
                    FollowUpTask.title.ilike(like),
                    Client.full_name.ilike(like),
                )
            )

        base = select(FollowUpTask).join(Client, FollowUpTask.client_id == Client.id)
        count_stmt = (
            select(func.count())
            .select_from(FollowUpTask)
            .join(Client, FollowUpTask.client_id == Client.id)
            .where(*conditions)
        )
        total = int((await self.session.execute(count_stmt)).scalar_one())

        stmt = (
            base.where(*conditions)
            .add_columns(Client.full_name)
            .order_by(FollowUpTask.due_date.asc().nulls_last(), FollowUpTask.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await self.session.execute(stmt)).all()
        return [(row[0], row[1]) for row in rows], total

    async def get_with_client(
        self, id_: UUID
    ) -> Optional[tuple[FollowUpTask, Optional[str]]]:
        stmt = (
            select(FollowUpTask)
            .join(Client, FollowUpTask.client_id == Client.id)
            .add_columns(Client.full_name)
            .where(FollowUpTask.id == id_)
        )
        row = (await self.session.execute(stmt)).first()
        return (row[0], row[1]) if row else None

    async def open_count(self) -> int:
        stmt = (
            select(func.count())
            .select_from(FollowUpTask)
            .where(FollowUpTask.status.in_(OPEN_STATUSES))
        )
        return int((await self.session.execute(stmt)).scalar_one())

    async def overdue_count(self, today: date) -> int:
        stmt = (
            select(func.count())
            .select_from(FollowUpTask)
            .where(
                FollowUpTask.status.in_(OPEN_STATUSES),
                FollowUpTask.due_date.is_not(None),
                FollowUpTask.due_date < today,
            )
        )
        return int((await self.session.execute(stmt)).scalar_one())

    async def due_soon_count(self, today: date, days: int = 7) -> int:
        soon = today + timedelta(days=days)
        stmt = (
            select(func.count())
            .select_from(FollowUpTask)
            .where(
                FollowUpTask.status.in_(OPEN_STATUSES),
                FollowUpTask.due_date.is_not(None),
                FollowUpTask.due_date >= today,
                FollowUpTask.due_date <= soon,
            )
        )
        return int((await self.session.execute(stmt)).scalar_one())
