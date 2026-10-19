from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_analytics_summary_shape(
    client: AsyncClient,
    auth_headers: dict[str, str],
    sample_client: dict,
) -> None:
    resp = await client.get("/api/v1/analytics/summary", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert set(
        [
            "total_clients",
            "total_trips",
            "ratings",
            "conversion",
            "visas",
            "nationalities",
            "revenue_by_currency",
            "trips_by_status",
            "feedback_by_sentiment",
            "generated_at",
        ]
    ).issubset(body.keys())
    assert body["total_clients"] >= 1
    assert "distribution" in body["ratings"]
    assert "conversion_rate" in body["conversion"]
    assert "approval_rate" in body["visas"]
    assert isinstance(body["nationalities"], list)
    assert isinstance(body["revenue_by_currency"], list)


@pytest.mark.asyncio
async def test_analytics_nationalities_include_sample(
    client: AsyncClient,
    auth_headers: dict[str, str],
    sample_client: dict,
) -> None:
    resp = await client.get(
        "/api/v1/analytics/nationalities?limit=5", headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    labels = {item["label"]: item["count"] for item in resp.json()}
    assert labels.get("Ugandan", 0) >= 1


@pytest.mark.asyncio
async def test_analytics_trends_months(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    resp = await client.get(
        "/api/v1/analytics/trends?months=3", headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    points = resp.json()
    assert len(points) == 3
    months = [p["month"] for p in points]
    assert months == sorted(months)
    assert all(
        set(["month", "clients", "leads", "payments", "revenue", "feedback"])
        == set(p.keys())
        for p in points
    )


@pytest.mark.asyncio
async def test_analytics_revenue_rows(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    resp = await client.get(
        "/api/v1/analytics/revenue?period_type=daily", headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_csv_export_clients(
    client: AsyncClient,
    auth_headers: dict[str, str],
    sample_client: dict,
) -> None:
    resp = await client.get("/api/v1/analytics/export/clients", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"].startswith("text/csv")
    assert "attachment" in resp.headers["content-disposition"]
    text = resp.content.decode("utf-8-sig")
    assert "full_name" in text.splitlines()[0]
    assert "Test Traveller" in text


@pytest.mark.asyncio
async def test_csv_export_unknown_dataset(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    resp = await client.get(
        "/api/v1/analytics/export/nonsense", headers=auth_headers
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_analytics_requires_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/analytics/summary")).status_code == 401
    assert (await client.get("/api/v1/analytics/export/clients")).status_code == 401
