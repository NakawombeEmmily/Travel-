from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _create_full(
    client: AsyncClient,
    headers: dict[str, str],
    sample_client: dict,
    amount: str = "1500.00",
) -> dict:
    resp = await client.post(
        "/api/v1/payments",
        json={
            "client_id": sample_client["id"],
            "amount": amount,
            "currency": "USD",
            "method": "card",
            "provider": "mock",
            "notes": "Deposit",
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.mark.asyncio
async def test_create_full_payment_syncs_outbox_and_invoice(
    client: AsyncClient,
    auth_headers: dict[str, str],
    sample_client: dict,
) -> None:
    payment = await _create_full(client, auth_headers, sample_client)
    assert payment["status"] == "completed"
    assert payment["provider"] == "mock"
    assert payment["provider_transaction_id"].startswith("mock_")
    assert payment["invoice_number"].startswith("INV-")
    assert payment["installments"] == []

    listing = await client.get("/api/v1/payments", headers=auth_headers)
    assert listing.status_code == 200
    assert listing.json()["total"] >= 1

    stats = await client.get("/api/v1/payments/stats", headers=auth_headers)
    assert stats.status_code == 200
    body = stats.json()
    assert body["count"] >= 1
    assert float(body["total_collected"]) >= 1500.0

    outbox = await client.get("/api/v1/payments/outbox", headers=auth_headers)
    assert outbox.status_code == 200
    events = [
        e
        for e in outbox.json()["items"]
        if e["aggregate_id"] == payment["id"]
    ]
    assert events
    assert all(e["status"] == "completed" for e in events)

    revenue = await client.get("/api/v1/payments/revenue", headers=auth_headers)
    assert revenue.status_code == 200
    assert revenue.json()

    invoice = await client.get(
        f"/api/v1/payments/{payment['id']}/invoice", headers=auth_headers
    )
    assert invoice.status_code == 200, invoice.text
    assert invoice.headers["content-type"] == "application/pdf"
    assert invoice.content.startswith(b"%PDF")


@pytest.mark.asyncio
async def test_installment_plan_partial_then_complete(
    client: AsyncClient,
    auth_headers: dict[str, str],
    sample_client: dict,
) -> None:
    resp = await client.post(
        "/api/v1/payments",
        json={
            "client_id": sample_client["id"],
            "amount": "3000.00",
            "currency": "USD",
            "method": "mobile_money",
            "provider": "mock",
            "installments": [
                {"amount": "1000.00", "due_date": "2026-11-01"},
                {"amount": "2000.00", "due_date": "2026-12-01"},
            ],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    payment = resp.json()
    assert payment["status"] == "partial"
    assert payment["invoice_number"] is None
    assert len(payment["installments"]) == 2

    first, second = payment["installments"]

    paid_first = await client.post(
        f"/api/v1/payments/{payment['id']}/installments/{first['id']}/pay",
        headers=auth_headers,
    )
    assert paid_first.status_code == 200, paid_first.text
    assert paid_first.json()["status"] == "partial"

    paid_second = await client.post(
        f"/api/v1/payments/{payment['id']}/installments/{second['id']}/pay",
        headers=auth_headers,
    )
    assert paid_second.status_code == 200, paid_second.text
    completed = paid_second.json()
    assert completed["status"] == "completed"
    assert completed["invoice_number"].startswith("INV-")
    assert all(i["status"] == "paid" for i in completed["installments"])

    invoice = await client.get(
        f"/api/v1/payments/{payment['id']}/invoice", headers=auth_headers
    )
    assert invoice.status_code == 200
    assert invoice.content.startswith(b"%PDF")

    repeat = await client.post(
        f"/api/v1/payments/{payment['id']}/installments/{first['id']}/pay",
        headers=auth_headers,
    )
    assert repeat.status_code == 409


@pytest.mark.asyncio
async def test_installments_must_sum_to_amount(
    client: AsyncClient,
    auth_headers: dict[str, str],
    sample_client: dict,
) -> None:
    resp = await client.post(
        "/api/v1/payments",
        json={
            "client_id": sample_client["id"],
            "amount": "1000.00",
            "installments": [{"amount": "400.00"}],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 400, resp.text


@pytest.mark.asyncio
async def test_refund_flow(
    client: AsyncClient,
    auth_headers: dict[str, str],
    sample_client: dict,
) -> None:
    payment = await _create_full(client, auth_headers, sample_client, "500.00")
    resp = await client.post(
        f"/api/v1/payments/{payment['id']}/refund", headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "refunded"

    again = await client.post(
        f"/api/v1/payments/{payment['id']}/refund", headers=auth_headers
    )
    assert again.status_code == 400


@pytest.mark.asyncio
async def test_payment_requires_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/payments")).status_code == 401
    assert (await client.get("/api/v1/payments/outbox")).status_code == 401
    assert (await client.post("/api/v1/payments/reconcile")).status_code == 401
