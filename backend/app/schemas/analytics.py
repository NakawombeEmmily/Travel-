from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class BreakdownItem(BaseModel):
    label: str
    count: int


class RatingDistribution(BaseModel):
    count: int
    average: float
    distribution: dict[str, int]


class ConversionMetrics(BaseModel):
    total_leads: int
    won: int
    lost: int
    open: int
    conversion_rate: float


class VisaMetrics(BaseModel):
    total: int
    approved: int
    rejected: int
    decided: int
    approval_rate: float
    by_status: dict[str, int]


class CurrencyRevenue(BaseModel):
    currency: str
    total: Decimal
    count: int


class AnalyticsSummary(BaseModel):
    total_clients: int
    total_trips: int
    ratings: RatingDistribution
    conversion: ConversionMetrics
    visas: VisaMetrics
    nationalities: list[BreakdownItem]
    revenue_by_currency: list[CurrencyRevenue]
    trips_by_status: dict[str, int]
    feedback_by_sentiment: dict[str, int]
    feedback_by_category: dict[str, int]
    generated_at: datetime


class TrendPoint(BaseModel):
    month: str
    clients: int
    leads: int
    payments: int
    revenue: Decimal
    feedback: int
