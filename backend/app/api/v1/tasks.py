from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.models.task import FollowUpTask
from app.models.user import User
from app.schemas.task import (
    TaskCreate,
    TaskListResponse,
    TaskRead,
    TaskStats,
    TaskUpdate,
)
from app.services.audit import record_audit
from app.services.exceptions import ClientNotFoundError
from app.services.task import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    client_id: UUID | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    assigned_to: UUID | None = None,
    q: str | None = None,
    page: int = 1,
    page_size: int = 50,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> TaskListResponse:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 200)
    items, total = await TaskService(session).search(
        client_id=client_id,
        status=status_filter,
        assigned_to=assigned_to,
        q=q,
        page=page,
        page_size=page_size,
    )
    return TaskListResponse(
        items=items, total=total, page=page, page_size=page_size
    )


@router.get("/stats", response_model=TaskStats)
async def task_stats(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> TaskStats:
    return await TaskService(session).stats()


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> TaskRead:
    service = TaskService(session)
    try:
        item = await service.create(payload, actor_id=user.id)
    except ClientNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Client not found") from exc
    await record_audit(
        session,
        action="create",
        entity_type="task",
        actor_id=user.id,
        entity_id=item.id,
    )
    await session.commit()
    row = await service.repo.get_with_client(item.id)
    name = row[1] if row else None
    return service.to_read(item, name)


async def _get_or_404(session: AsyncSession, task_id: UUID) -> FollowUpTask:
    item = await session.get(FollowUpTask, task_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return item


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(
    task_id: UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> TaskRead:
    service = TaskService(session)
    row = await service.repo.get_with_client(task_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")
    item, name = row
    return service.to_read(item, name)


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: UUID,
    payload: TaskUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> TaskRead:
    item = await _get_or_404(session, task_id)
    service = TaskService(session)
    item = await service.update(item, payload)
    await record_audit(
        session,
        action="update",
        entity_type="task",
        actor_id=user.id,
        entity_id=item.id,
    )
    await session.commit()
    row = await service.repo.get_with_client(item.id)
    name = row[1] if row else None
    return service.to_read(item, name)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> None:
    item = await _get_or_404(session, task_id)
    await TaskService(session).delete(item)
    await record_audit(
        session,
        action="delete",
        entity_type="task",
        actor_id=user.id,
        entity_id=task_id,
    )
    await session.commit()
