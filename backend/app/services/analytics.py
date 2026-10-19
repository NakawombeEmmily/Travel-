from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.models.admin import AdminRevenueSummary
from app.models.client import Client
from app.models.feedback import Feedback
from app.models.lead import Lead, LeadStatus
from app.models.payment import Payment, PaymentStatus
from app.models.trip import Trip
from app.models.visa import VisaStatus
from app.repositories.feedback import FeedbackRepository
from app.repositories.lead import LeadRepository
from app.repositories.trip import TripRepository
from app.repositories.visa import VisaRepository
from app.schemas.analytics import (
    AnalyticsSummary,
    BreakdownItem,
    ConversionMetrics,
    CurrencyRevenue,
    RatingDistribution,
    TrendPoint,
    VisaMetrics,
)

OPEN_LEAD_STATUSES = {
    LeadStatus.lead.value,
    LeadStatus.contacted.value,
    LeadStatus.quote_sent.value,
    LeadStatus.negotiation.value,
}


def _month_keys(months: int) -> list[str]:
    today = date.today()
    year, month = today.year, today.month
    keys: list[str] = []
    for _ in range(months):
        keys.append(f"{year:04d}-{month:02d}")
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return list(reversed(keys))


def _month_key(value: datetime) -> str:
    return f"{value.year:04d}-{value.month:02d}"


class AnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.feedback = FeedbackRepository(session)
        self.leads = LeadRepository(session)
        self.trips = TripRepository(session)
        self.visas = VisaRepository(session)

    async def _count(self, stmt: Select[Any]) -> int:
        return int((await self.session.execute(stmt)).scalar_one())

    async def _rating_distribution(self) -> RatingDistribution:
        count, average = await self.feedback.average_rating()
        stmt = (
            select(Feedback.rating, func.count())
            .group_by(Feedback.rating)
            .order_by(Feedback.rating.asc())
        )
        rows = (await self.session.execute(stmt)).all()
        distribution = {str(rating): int(total) for rating, total in rows}
        return RatingDistribution(
            count=count,
            average=round(average, 2),
            distribution=distribution,
        )

    async def _conversion(self) -> ConversionMetrics:
        by_status = await self.leads.counts_by_status()
        total = sum(by_status.values())
        won = by_status.get(LeadStatus.won.value, 0)
        lost = by_status.get(LeadStatus.lost.value, 0)
        open_count = sum(by_status.get(s, 0) for s in OPEN_LEAD_STATUSES)
        rate = round((won / total) * 100, 2) if total else 0.0
        return ConversionMetrics(
            total_leads=total,
            won=won,
            lost=lost,
            open=open_count,
            conversion_rate=rate,
        )

    async def _visas(self) -> VisaMetrics:
        by_status = await self.visas.counts_by_status()
        approved = by_status.get(VisaStatus.approved.value, 0)
        rejected = by_status.get(VisaStatus.rejected.value, 0)
        decided = approved + rejected
        rate = round((approved / decided) * 100, 2) if decided else 0.0
        return VisaMetrics(
            total=sum(by_status.values()),
            approved=approved,
            rejected=rejected,
            decided=decided,
            approval_rate=rate,
            by_status=by_status,
        )

    async def nationalities(self, limit: int = 10) -> list[BreakdownItem]:
        stmt = (
            select(Client.nationality, func.count())
            .where(
                Client.is_deleted.is_(False),
                Client.nationality.is_not(None),
            )
            .group_by(Client.nationality)
        )
        rows = (await self.session.execute(stmt)).all()
        items = [
            BreakdownItem(label=nationality, count=int(count))
            for nationality, count in rows
            if nationality
        ]
        items.sort(key=lambda item: item.count, reverse=True)
        return items[:limit]

    async def revenue_by_currency(self) -> list[CurrencyRevenue]:
        stmt = (
            select(
                Payment.currency,
                func.count(),
                func.coalesce(func.sum(Payment.amount), 0),
            )
            .where(Payment.status == PaymentStatus.completed.value)
            .group_by(Payment.currency)
        )
        rows = (await self.session.execute(stmt)).all()
        items = [
            CurrencyRevenue(
                currency=currency,
                total=Decimal(str(total or 0)).quantize(Decimal("0.01")),
                count=int(count),
            )
            for currency, count, total in rows
        ]
        items.sort(key=lambda item: item.total, reverse=True)
        return items

    async def summary(self, top_nationalities: int = 10) -> AnalyticsSummary:
        total_clients = await self._count(
            select(func.count())
            .select_from(Client)
            .where(Client.is_deleted.is_(False))
        )
        total_trips = await self._count(
            select(func.count()).select_from(Trip)
        )

        return AnalyticsSummary(
            total_clients=total_clients,
            total_trips=total_trips,
            ratings=await self._rating_distribution(),
            conversion=await self._conversion(),
            visas=await self._visas(),
            nationalities=await self.nationalities(top_nationalities),
            revenue_by_currency=await self.revenue_by_currency(),
            trips_by_status=await self.trips.counts_by_status(),
            feedback_by_sentiment=await self.feedback.counts_by_sentiment(),
            feedback_by_category=await self.feedback.counts_by_category(),
            generated_at=datetime.now(UTC),
        )

    async def trends(self, months: int = 6) -> list[TrendPoint]:
        months = max(1, min(months, 24))
        keys = _month_keys(months)
        counts: dict[str, dict[str, int]] = {
            key: {"clients": 0, "leads": 0, "payments": 0, "feedback": 0}
            for key in keys
        }
        revenue: dict[str, Decimal] = {key: Decimal("0.00") for key in keys}

        earliest = keys[0]
        start_year, start_month = int(earliest[:4]), int(earliest[5:7])
        start = datetime(start_year, start_month, 1, tzinfo=UTC)

        async def _bump(field: str, column: InstrumentedAttribute[datetime]) -> None:
            rows = (
                await self.session.execute(select(column).where(column >= start))
            ).all()
            for (value,) in rows:
                if value is None:
                    continue
                key = _month_key(value)
                if key in counts:
                    counts[key][field] += 1

        await _bump("clients", Client.created_at)
        await _bump("leads", Lead.created_at)
        await _bump("feedback", Feedback.created_at)

        payment_rows = (
            await self.session.execute(
                select(
                    Payment.created_at,
                    Payment.amount,
                    Payment.exchange_rate,
                    Payment.status,
                ).where(Payment.created_at >= start)
            )
        ).all()
        for created_at, amount, exchange_rate, status in payment_rows:
            key = _month_key(created_at)
            if key not in counts:
                continue
            counts[key]["payments"] += 1
            if status == PaymentStatus.completed.value:
                base = Decimal(str(amount)) * Decimal(str(exchange_rate))
                revenue[key] += base

        points: list[TrendPoint] = []
        for key in keys:
            bucket = counts[key]
            points.append(
                TrendPoint(
                    month=key,
                    clients=bucket["clients"],
                    leads=bucket["leads"],
                    payments=bucket["payments"],
                    revenue=revenue[key].quantize(Decimal("0.01")),
                    feedback=bucket["feedback"],
                )
            )
        return points

    async def revenue_summaries(
        self,
        *,
        period_type: Optional[str] = None,
        currency: Optional[str] = None,
        limit: int = 60,
    ) -> list[AdminRevenueSummary]:
        stmt = select(AdminRevenueSummary)
        if period_type:
            stmt = stmt.where(AdminRevenueSummary.period_type == period_type)
        if currency:
            stmt = stmt.where(AdminRevenueSummary.currency == currency)
        stmt = stmt.order_by(
            AdminRevenueSummary.summary_date.desc(),
            AdminRevenueSummary.period_type.asc(),
        ).limit(limit)
        return list((await self.session.execute(stmt)).scalars().all())
