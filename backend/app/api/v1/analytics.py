from __future__ import annotations

import io

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.models.user import User
from app.schemas.analytics import AnalyticsSummary, BreakdownItem, TrendPoint
from app.schemas.payment import RevenueSummaryRead
from app.services.analytics import AnalyticsService
from app.services.exceptions import NotFoundError
from app.services.export import CSV_DATASETS, export_dataset

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
async def analytics_summary(
    top_nationalities: int = Query(default=10, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> AnalyticsSummary:
    return await AnalyticsService(session).summary(top_nationalities)


@router.get("/trends", response_model=list[TrendPoint])
async def analytics_trends(
    months: int = Query(default=6, ge=1, le=24),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> list[TrendPoint]:
    return await AnalyticsService(session).trends(months)


@router.get("/nationalities", response_model=list[BreakdownItem])
async def analytics_nationalities(
    limit: int = Query(default=10, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> list[BreakdownItem]:
    return await AnalyticsService(session).nationalities(limit)


@router.get("/revenue", response_model=list[RevenueSummaryRead])
async def analytics_revenue(
    period_type: str | None = None,
    currency: str | None = None,
    limit: int = Query(default=60, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> list[RevenueSummaryRead]:
    rows = await AnalyticsService(session).revenue_summaries(
        period_type=period_type,
        currency=currency.upper() if currency else None,
        limit=limit,
    )
    return [RevenueSummaryRead.model_validate(row) for row in rows]


@router.get("/export/{dataset}")
async def export_csv(
    dataset: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> StreamingResponse:
    if dataset not in CSV_DATASETS:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown dataset. Choose one of: {', '.join(CSV_DATASETS)}",
        )
    try:
        filename, data = await export_dataset(session, dataset)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return StreamingResponse(
        io.BytesIO(data),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
