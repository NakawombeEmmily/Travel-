from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class UpcomingDeparture(BaseModel):
    trip_id: UUID
    client_name: Optional[str] = None
    destination_country: str
    travel_start_date: date
    status: str


class DashboardSummary(BaseModel):
    active_clients: int
    trips_in_progress: int
    pending_visas: int
    revenue_mtd: Decimal
    passports_expiring_soon: int
    visas_expiring_soon: int
    trips_by_status: dict[str, int]
    visas_by_status: dict[str, int]
    upcoming_departures: list[UpcomingDeparture]
