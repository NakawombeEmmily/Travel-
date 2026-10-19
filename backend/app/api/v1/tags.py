from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.models.tag import Tag
from app.models.user import User
from app.schemas.tag import (
    ClientTagsResponse,
    TagCreate,
    TagListResponse,
    TagRead,
    TagUpdate,
)
from app.services.exceptions import ClientNotFoundError, ConflictError, NotFoundError
from app.services.tag import TagService

router = APIRouter(tags=["tags"])


@router.get("/tags", response_model=TagListResponse)
async def list_tags(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> TagListResponse:
    return TagListResponse(items=await TagService(session).list_tags())


@router.post("/tags", response_model=TagRead, status_code=status.HTTP_201_CREATED)
async def create_tag(
    payload: TagCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> TagRead:
    service = TagService(session)
    try:
        tag = await service.create(payload)
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    await session.commit()
    return service.to_read(tag)


async def _get_or_404(session: AsyncSession, tag_id: UUID) -> Tag:
    tag = await session.get(Tag, tag_id)
    if tag is None:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag


@router.patch("/tags/{tag_id}", response_model=TagRead)
async def update_tag(
    tag_id: UUID,
    payload: TagUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> TagRead:
    tag = await _get_or_404(session, tag_id)
    service = TagService(session)
    try:
        tag = await service.update(tag, payload)
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    await session.commit()
    return service.to_read(tag)


@router.delete("/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> None:
    tag = await _get_or_404(session, tag_id)
    await TagService(session).delete(tag)
    await session.commit()


@router.get("/clients/{client_id}/tags", response_model=ClientTagsResponse)
async def client_tags(
    client_id: UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> ClientTagsResponse:
    try:
        return ClientTagsResponse(
            items=await TagService(session).tags_for_client(client_id)
        )
    except ClientNotFoundError as err:
        raise HTTPException(status_code=404, detail="Client not found") from err


@router.post(
    "/clients/{client_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def attach_tag(
    client_id: UUID,
    tag_id: UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> None:
    try:
        await TagService(session).attach(client_id, tag_id)
    except ClientNotFoundError as exc1:
        raise HTTPException(status_code=404, detail="Client not found") from exc1
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await session.commit()


@router.delete(
    "/clients/{client_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def detach_tag(
    client_id: UUID,
    tag_id: UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> None:
    try:
        await TagService(session).detach(client_id, tag_id)
    except ClientNotFoundError as err1:
        raise HTTPException(status_code=404, detail="Client not found") from err1
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await session.commit()
