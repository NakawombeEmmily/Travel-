from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.lead import LeadStatus
from app.models.trip import Trip, TripStatus
from app.models.visa import Visa, VisaStatus
from app.repositories.feedback import FeedbackRepository
from app.repositories.lead import LeadRepository
from app.repositories.payment import PaymentRepository
from app.repositories.task import TaskRepository
from app.repositories.trip import TripRepository
from app.repositories.visa import VisaRepository
from app.schemas.dashboard import DashboardSummary, UpcomingDeparture

PENDING_VISA_STATUSES = {
    VisaStatus.documents_pending.value,
    VisaStatus.submitted.value,
    VisaStatus.in_review.value,
}

OPEN_LEAD_STATUSES = {
    LeadStatus.lead.value,
    LeadStatus.contacted.value,
    LeadStatus.quote_sent.value,
    LeadStatus.negotiation.value,
}


class DashboardService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.trips = TripRepository(session)
        self.visas = VisaRepository(session)
        self.feedback = FeedbackRepository(session)
        self.leads = LeadRepository(session)
        self.tasks = TaskRepository(session)
        self.payments = PaymentRepository(session)

    async def _scalar(self, stmt: Select[Any]) -> int:
        return int((await self.session.execute(stmt)).scalar_one())

    async def summary(self) -> DashboardSummary:
        today = date.today()
        soon = today + timedelta(days=90)

        active_clients = await self._scalar(
            select(func.count())
            .select_from(Client)
            .where(Client.is_deleted.is_(False))
        )
        passports_expiring = await self._scalar(
            select(func.count())
            .select_from(Client)
            .where(
                Client.is_deleted.is_(False),
                Client.passport_expiry_date.is_not(None),
                Client.passport_expiry_date <= soon,
                Client.passport_expiry_date >= today,
            )
        )
        visas_expiring = await self._scalar(
            select(func.count())
            .select_from(Visa)
            .where(
                Visa.expiry_date.is_not(None),
                Visa.expiry_date <= soon,
                Visa.expiry_date >= today,
            )
        )

        trips_by_status = await self.trips.counts_by_status()
        visas_by_status = await self.visas.counts_by_status()

        feedback_count, feedback_average = await self.feedback.average_rating()
        feedback_by_sentiment = await self.feedback.counts_by_sentiment()
        leads_by_status = await self.leads.counts_by_status()
        open_tasks = await self.tasks.open_count()
        overdue_tasks = await self.tasks.overdue_count(today)

        upcoming_stmt = (
            select(Trip, Client.full_name)
            .join(Client, Trip.client_id == Client.id)
            .where(
                Trip.travel_start_date >= today,
                Trip.status != TripStatus.cancelled.value,
            )
            .order_by(Trip.travel_start_date.asc())
            .limit(5)
        )
        upcoming_rows = (await self.session.execute(upcoming_stmt)).all()

        month_start = datetime(today.year, today.month, 1, tzinfo=UTC)
        revenue_mtd = await self.payments.completed_total_since(month_start)

        return DashboardSummary(
            active_clients=active_clients,
            trips_in_progress=trips_by_status.get(
                TripStatus.in_progress.value, 0
            ),
            pending_visas=sum(
                visas_by_status.get(s, 0) for s in PENDING_VISA_STATUSES
            ),
            revenue_mtd=revenue_mtd,
            passports_expiring_soon=passports_expiring,
            visas_expiring_soon=visas_expiring,
            trips_by_status=trips_by_status,
            visas_by_status=visas_by_status,
            upcoming_departures=[
                UpcomingDeparture(
                    trip_id=trip.id,
                    client_name=name,
                    destination_country=trip.destination_country,
                    travel_start_date=trip.travel_start_date,
                    status=trip.status,
                )
                for trip, name in upcoming_rows
            ],
            feedback_count=feedback_count,
            feedback_average=round(feedback_average, 2),
            feedback_by_sentiment=feedback_by_sentiment,
            open_leads=sum(
                leads_by_status.get(s, 0) for s in OPEN_LEAD_STATUSES
            ),
            leads_by_status=leads_by_status,
            open_tasks=open_tasks,
            overdue_tasks=overdue_tasks,
        )
