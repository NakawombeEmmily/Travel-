from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_document_upload_list_download(
    client: AsyncClient, auth_headers: dict[str, str], sample_client: dict
) -> None:
    upload = await client.post(
        "/api/v1/documents",
        data={"client_id": sample_client["id"]},
        files={"file": ("passport.txt", b"secret-bytes", "text/plain")},
        headers=auth_headers,
    )
    assert upload.status_code == 201, upload.text
    document = upload.json()
    assert document["original_filename"] == "passport.txt"
    assert document["is_encrypted"] is True

    listing = await client.get(
        f"/api/v1/documents?client_id={sample_client['id']}",
        headers=auth_headers,
    )
    assert listing.status_code == 200
    assert listing.json()["total"] >= 1

    download = await client.get(
        f"/api/v1/documents/{document['id']}/download", headers=auth_headers
    )
    assert download.status_code == 200
    assert download.content == b"secret-bytes"

    delete = await client.delete(
        f"/api/v1/documents/{document['id']}", headers=auth_headers
    )
    assert delete.status_code == 204


@pytest.mark.asyncio
async def test_document_requires_target(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    resp = await client.post(
        "/api/v1/documents",
        files={"file": ("orphan.txt", b"data", "text/plain")},
        headers=auth_headers,
    )
    assert resp.status_code == 400
