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
    feedback_count: int = 0
    feedback_average: float = 0.0
    feedback_by_sentiment: dict[str, int] = {}
    open_leads: int = 0
    leads_by_status: dict[str, int] = {}
    open_tasks: int = 0
    overdue_tasks: int = 0
