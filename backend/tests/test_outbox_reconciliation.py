from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_reconcile_reports_and_repairs(
    client: AsyncClient,
    auth_headers: dict[str, str],
    sample_client: dict,
) -> None:
    created = await client.post(
        "/api/v1/payments",
        json={
            "client_id": sample_client["id"],
            "amount": "250.00",
            "currency": "USD",
            "method": "cash",
            "provider": "mock",
        },
        headers=auth_headers,
    )
    assert created.status_code == 201, created.text

    resp = await client.post(
        "/api/v1/payments/reconcile", headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    result = resp.json()
    assert result["checked"] >= 1
    assert result["errors"] == []

    created_again = await client.post(
        "/api/v1/payments/reconcile", headers=auth_headers
    )
    assert created_again.status_code == 200
    assert created_again.json()["mismatched"] == 0


@pytest.mark.asyncio
async def test_process_pending_outbox_is_idempotent(
    client: AsyncClient,
    auth_headers: dict[str, str],
    sample_client: dict,
) -> None:
    created = await client.post(
        "/api/v1/payments",
        json={
            "client_id": sample_client["id"],
            "amount": "99.00",
            "currency": "USD",
            "method": "cash",
            "provider": "mock",
        },
        headers=auth_headers,
    )
    assert created.status_code == 201, created.text

    processed = await client.post(
        "/api/v1/payments/outbox/process", headers=auth_headers
    )
    assert processed.status_code == 200, processed.text
    assert processed.json()["pending"] == 0


@pytest.mark.asyncio
async def test_revenue_summary_reflects_completed_payments(
    client: AsyncClient,
    auth_headers: dict[str, str],
    sample_client: dict,
) -> None:
    await client.post(
        "/api/v1/payments",
        json={
            "client_id": sample_client["id"],
            "amount": "700.00",
            "currency": "USD",
            "method": "bank_transfer",
            "provider": "mock",
        },
        headers=auth_headers,
    )
    resp = await client.get("/api/v1/payments/revenue", headers=auth_headers)
    assert resp.status_code == 200
    summaries = resp.json()
    daily = [s for s in summaries if s["period_type"] == "daily"]
    assert daily
    assert float(daily[0]["total_amount"]) >= 700.0
