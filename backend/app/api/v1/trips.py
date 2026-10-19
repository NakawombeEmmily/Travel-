from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.models.trip import Trip
from app.models.user import User
from app.schemas.trip import TripCreate, TripListResponse, TripRead, TripUpdate
from app.services.audit import record_audit
from app.services.trip import ClientNotFoundError, TripService

router = APIRouter(prefix="/trips", tags=["trips"])


@router.get("", response_model=TripListResponse)
async def list_trips(
    client_id: UUID | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    q: str | None = None,
    page: int = 1,
    page_size: int = 20,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> TripListResponse:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    service = TripService(session)
    items, total = await service.search(
        client_id=client_id,
        status=status_filter,
        q=q,
        page=page,
        page_size=page_size,
    )
    return TripListResponse(
        items=items, total=total, page=page, page_size=page_size
    )


@router.post("", response_model=TripRead, status_code=status.HTTP_201_CREATED)
async def create_trip(
    payload: TripCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> TripRead:
    service = TripService(session)
    try:
        trip = await service.create(payload, actor_id=user.id)
    except ClientNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Client not found") from exc
    await record_audit(
        session,
        action="create",
        entity_type="trip",
        actor_id=user.id,
        entity_id=trip.id,
    )
    await session.commit()
    row = await service.repo.get_with_client(trip.id)
    client_name = row[1] if row else None
    return service.to_read(trip, client_name)


async def _get_trip_or_404(session: AsyncSession, trip_id: UUID) -> Trip:
    trip = await session.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


@router.get("/{trip_id}", response_model=TripRead)
async def get_trip(
    trip_id: UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> TripRead:
    service = TripService(session)
    row = await service.repo.get_with_client(trip_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    trip, client_name = row
    return service.to_read(trip, client_name)


@router.patch("/{trip_id}", response_model=TripRead)
async def update_trip(
    trip_id: UUID,
    payload: TripUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> TripRead:
    trip = await _get_trip_or_404(session, trip_id)
    service = TripService(session)
    trip = await service.update(trip, payload)
    await record_audit(
        session,
        action="update",
        entity_type="trip",
        actor_id=user.id,
        entity_id=trip.id,
    )
    await session.commit()
    row = await service.repo.get_with_client(trip.id)
    client_name = row[1] if row else None
    return service.to_read(trip, client_name)


@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trip(
    trip_id: UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> None:
    trip = await _get_trip_or_404(session, trip_id)
    service = TripService(session)
    await service.delete(trip)
    await record_audit(
        session,
        action="delete",
        entity_type="trip",
        actor_id=user.id,
        entity_id=trip_id,
    )
    await session.commit()
