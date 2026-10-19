from __future__ import annotations

import asyncio
import base64
import os
import tempfile
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

_TMP_DB = os.path.join(tempfile.gettempdir(), "travel_system_test.db")

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-0123456789abcdef")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-0123456789abcdef")
os.environ.setdefault("JWT_REFRESH_SECRET", "test-refresh-0123456789abcdef")
os.environ.setdefault(
    "ENCRYPTION_KEY",
    base64.urlsafe_b64encode(b"0123456789abcdef0123456789abcdef").decode(),
)
os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{_TMP_DB}")
os.environ.setdefault("DATABASE_URL_DIRECT", f"sqlite+aiosqlite:///{_TMP_DB}")
os.environ.setdefault("ADMIN_DATABASE_URL", f"sqlite+aiosqlite:///{_TMP_DB}")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault(
    "STORAGE_LOCAL_DIR",
    os.path.join(tempfile.gettempdir(), "travel_system_storage"),
)

from app.api.deps import get_session  # noqa: E402
from app.core.security.passwords import hash_password  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.main import app  # noqa: E402
from app.models import (  # noqa: E402
    AuditLog,
    Client,
    User,
    UserRole,
)

if os.path.exists(_TMP_DB):
    os.remove(_TMP_DB)

_test_engine = create_async_engine(
    f"sqlite+aiosqlite:///{_TMP_DB}",
    execution_options={"schema_translate_map": {"crm": None, "admin": None}},
)
_TestSession = async_sessionmaker(
    bind=_test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _create_schema():
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await _test_engine.dispose()


@pytest_asyncio.fixture()
async def session() -> AsyncGenerator[AsyncSession, None]:
    async with _TestSession() as s:
        yield s


@pytest_asyncio.fixture()
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _override() -> AsyncGenerator[AsyncSession, None]:
        yield session

    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture()
async def admin_user(session: AsyncSession) -> User:
    from sqlalchemy import select

    existing = (
        await session.execute(
            select(User).where(User.email == "admin@example.com")
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing
    user = User(
        email="admin@example.com",
        password_hash=hash_password("AdminPass123!"),
        full_name="Admin User",
        role=UserRole.super_admin,
        is_active=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest_asyncio.fixture()
async def auth_headers(
    client: AsyncClient, admin_user: User
) -> dict[str, str]:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": admin_user.email, "password": "AdminPass123!"},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture()
async def sample_client(
    client: AsyncClient, auth_headers: dict[str, str]
) -> dict:
    existing = await client.get(
        "/api/v1/clients?q=traveller@example.com", headers=auth_headers
    )
    if existing.status_code == 200 and existing.json()["items"]:
        return existing.json()["items"][0]

    resp = await client.post(
        "/api/v1/clients",
        json={
            "full_name": "Test Traveller",
            "email": "traveller@example.com",
            "phone": "+256700000000",
            "nationality": "Ugandan",
            "passport_number": "UG1234567",
            "consent_given": True,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


__all__ = [
    "app",
    "AuditLog",
    "Client",
    "User",
    "UserRole",
]
