from __future__ import annotations

from datetime import date
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.task import FollowUpTask
from app.repositories.task import TaskRepository
from app.schemas.task import TaskCreate, TaskRead, TaskStats, TaskUpdate
from app.services.exceptions import ClientNotFoundError


class TaskService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = TaskRepository(session)

    def to_read(
        self, item: FollowUpTask, client_name: Optional[str] = None
    ) -> TaskRead:
        read = TaskRead.model_validate(item)
        read.client_name = client_name
        return read

    async def _ensure_client(self, client_id: UUID) -> None:
        client = await self.session.get(Client, client_id)
        if client is None or client.is_deleted:
            raise ClientNotFoundError(str(client_id))

    async def create(
        self, payload: TaskCreate, *, actor_id: Optional[UUID] = None
    ) -> FollowUpTask:
        await self._ensure_client(payload.client_id)
        item = FollowUpTask(
            client_id=payload.client_id,
            title=payload.title,
            description=payload.description,
            assigned_to=payload.assigned_to,
            due_date=payload.due_date,
            status=payload.status.value,
            priority=payload.priority.value,
            created_by=actor_id,
        )
        await self.repo.add(item)
        return item

    async def update(self, item: FollowUpTask, payload: TaskUpdate) -> FollowUpTask:
        data = payload.model_dump(exclude_unset=True)
        if data.get("status") is not None:
            data["status"] = data["status"].value
        if data.get("priority") is not None:
            data["priority"] = data["priority"].value
        for key, value in data.items():
            setattr(item, key, value)
        await self.session.flush()
        return item

    async def delete(self, item: FollowUpTask) -> None:
        await self.session.delete(item)

    async def search(
        self,
        *,
        client_id: Optional[UUID] = None,
        status: Optional[str] = None,
        assigned_to: Optional[UUID] = None,
        q: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[TaskRead], int]:
        rows, total = await self.repo.search(
            client_id=client_id,
            status=status,
            assigned_to=assigned_to,
            q=q,
            page=page,
            page_size=page_size,
        )
        return [self.to_read(item, name) for item, name in rows], total

    async def stats(self) -> TaskStats:
        today = date.today()
        return TaskStats(
            open=await self.repo.open_count(),
            overdue=await self.repo.overdue_count(today),
            due_soon=await self.repo.due_soon_count(today),
        )
