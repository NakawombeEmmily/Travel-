from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_feedback_crud_and_sentiment(
    client: AsyncClient, auth_headers: dict[str, str], sample_client: dict
) -> None:
    positive = await client.post(
        "/api/v1/feedback",
        json={
            "client_id": sample_client["id"],
            "rating": 5,
            "comment": "Great service, very helpful team",
            "category": "service",
        },
        headers=auth_headers,
    )
    assert positive.status_code == 201, positive.text
    body = positive.json()
    assert body["sentiment"] == "positive"
    assert body["client_name"] == "Test Traveller"

    negative = await client.post(
        "/api/v1/feedback",
        json={"client_id": sample_client["id"], "rating": 1, "comment": "Slow and rude"},
        headers=auth_headers,
    )
    assert negative.status_code == 201
    assert negative.json()["sentiment"] == "negative"

    mixed = await client.post(
        "/api/v1/feedback",
        json={"client_id": sample_client["id"], "rating": 5, "comment": "Good but delayed"},
        headers=auth_headers,
    )
    assert mixed.status_code == 201
    assert mixed.json()["sentiment"] == "mixed"

    listing = await client.get("/api/v1/feedback", headers=auth_headers)
    assert listing.status_code == 200
    assert listing.json()["total"] >= 3

    stats = await client.get("/api/v1/feedback/stats", headers=auth_headers)
    assert stats.status_code == 200
    assert stats.json()["count"] >= 3
    assert "positive" in stats.json()["by_sentiment"]

    update = await client.patch(
        f"/api/v1/feedback/{body['id']}",
        json={"rating": 2, "comment": "Very slow and rude"},
        headers=auth_headers,
    )
    assert update.status_code == 200, update.text
    assert update.json()["sentiment"] == "negative"

    delete = await client.delete(
        f"/api/v1/feedback/{body['id']}", headers=auth_headers
    )
    assert delete.status_code == 204


@pytest.mark.asyncio
async def test_feedback_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/feedback")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_feedback_unknown_client(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    resp = await client.post(
        "/api/v1/feedback",
        json={
            "client_id": "00000000-0000-0000-0000-000000000000",
            "rating": 4,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 404
