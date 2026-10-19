from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_visa_status_history(
    client: AsyncClient, auth_headers: dict[str, str], sample_client: dict
) -> None:
    create = await client.post(
        "/api/v1/visas",
        json={
            "client_id": sample_client["id"],
            "destination_country": "United Kingdom",
            "visa_type": "Standard Visitor",
            "status": "not_started",
        },
        headers=auth_headers,
    )
    assert create.status_code == 201, create.text
    visa = create.json()

    for new_status in ("documents_pending", "submitted", "approved"):
        resp = await client.patch(
            f"/api/v1/visas/{visa['id']}",
            json={"status": new_status, "status_note": f"moved to {new_status}"},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text

    detail = await client.get(f"/api/v1/visas/{visa['id']}", headers=auth_headers)
    assert detail.status_code == 200
    body = detail.json()
    assert body["status"] == "approved"
    assert body["approval_date"] is not None
    assert len(body["history"]) == 3
    assert body["history"][0]["new_status"] == "approved"

    history = await client.get(
        f"/api/v1/visas/{visa['id']}/history", headers=auth_headers
    )
    assert history.status_code == 200
    assert len(history.json()) == 3


@pytest.mark.asyncio
async def test_visa_list_by_status(
    client: AsyncClient, auth_headers: dict[str, str], sample_client: dict
) -> None:
    await client.post(
        "/api/v1/visas",
        json={
            "client_id": sample_client["id"],
            "destination_country": "Schengen",
            "status": "in_review",
        },
        headers=auth_headers,
    )
    resp = await client.get(
        "/api/v1/visas?status=in_review", headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1
    assert all(v["status"] == "in_review" for v in resp.json()["items"])
