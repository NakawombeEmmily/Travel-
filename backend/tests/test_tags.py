from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_tag_lifecycle(
    client: AsyncClient, auth_headers: dict[str, str], sample_client: dict
) -> None:
    create = await client.post(
        "/api/v1/tags",
        json={"name": "VIP", "color": "#F97316"},
        headers=auth_headers,
    )
    assert create.status_code == 201, create.text
    tag = create.json()

    duplicate = await client.post(
        "/api/v1/tags",
        json={"name": "VIP", "color": "#111111"},
        headers=auth_headers,
    )
    assert duplicate.status_code == 409

    listing = await client.get("/api/v1/tags", headers=auth_headers)
    assert listing.status_code == 200
    assert any(t["id"] == tag["id"] for t in listing.json()["items"])

    attach = await client.post(
        f"/api/v1/clients/{sample_client['id']}/tags/{tag['id']}",
        headers=auth_headers,
    )
    assert attach.status_code == 204, attach.text

    client_tags = await client.get(
        f"/api/v1/clients/{sample_client['id']}/tags", headers=auth_headers
    )
    assert client_tags.status_code == 200
    assert any(t["id"] == tag["id"] for t in client_tags.json()["items"])

    detach = await client.delete(
        f"/api/v1/clients/{sample_client['id']}/tags/{tag['id']}",
        headers=auth_headers,
    )
    assert detach.status_code == 204

    delete = await client.delete(f"/api/v1/tags/{tag['id']}", headers=auth_headers)
    assert delete.status_code == 204


@pytest.mark.asyncio
async def test_tags_require_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/tags")
    assert resp.status_code == 401
