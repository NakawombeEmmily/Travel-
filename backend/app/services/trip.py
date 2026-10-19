from __future__ import annotations

from datetime import UTC, datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.trip import Trip
from app.repositories.trip import TripRepository
from app.schemas.trip import TripCreate, TripRead, TripUpdate


class ClientNotFoundError(Exception):
    pass


class TripService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = TripRepository(session)

    def to_read(self, trip: Trip, client_name: Optional[str] = None) -> TripRead:
        read = TripRead.model_validate(trip)
        read.client_name = client_name
        return read

    async def _ensure_client(self, client_id: UUID) -> None:
        client = await self.session.get(Client, client_id)
        if client is None or client.is_deleted:
            raise ClientNotFoundError(str(client_id))

    async def create(
        self, payload: TripCreate, *, actor_id: Optional[UUID] = None
    ) -> Trip:
        await self._ensure_client(payload.client_id)
        trip = Trip(
            **payload.model_dump(exclude={"status", "purpose"}),
            status=payload.status.value,
            purpose=payload.purpose.value,
            created_by=actor_id,
        )
        await self.repo.add(trip)
        return trip

    async def update(
        self, trip: Trip, payload: TripUpdate
    ) -> Trip:
        data = payload.model_dump(exclude_unset=True)
        if "status" in data and data["status"] is not None:
            data["status"] = data["status"].value
        if "purpose" in data and data["purpose"] is not None:
            data["purpose"] = data["purpose"].value
        for key, value in data.items():
            setattr(trip, key, value)
        trip.updated_at = datetime.now(UTC)
        await self.session.flush()
        return trip

    async def delete(self, trip: Trip) -> None:
        await self.session.delete(trip)

    async def search(
        self,
        *,
        client_id: Optional[UUID] = None,
        status: Optional[str] = None,
        q: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[TripRead], int]:
        rows, total = await self.repo.search(
            client_id=client_id,
            status=status,
            q=q,
            page=page,
            page_size=page_size,
        )
        return [self.to_read(trip, name) for trip, name in rows], total
