"""Create (or reset) an admin user in crm.users.

Works against any Postgres, including Neon production.

Usage (PowerShell), run from the repo root:
    $env:DATABASE_URL_DIRECT = "postgresql+asyncpg://...@...neon.tech/neondb?ssl=require"
    python scripts/create_admin.py --email you@company.com --password "S3cretPass!" --name "Your Name" --role super_admin --yes

Roles: super_admin | admin | agent | accountant | read_only
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "backend"))

import asyncpg  # noqa: E402
from app.core.security.passwords import hash_password  # noqa: E402
from app.models.user import UserRole  # noqa: E402


def as_asyncpg_url(url: str) -> str:
    return url.replace("postgresql+asyncpg://", "postgresql://", 1)


async def run(email: str, password: str, name: str, role: str) -> None:
    url = os.environ.get("DATABASE_URL_DIRECT") or os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit("Set DATABASE_URL_DIRECT (or DATABASE_URL) first.")

    conn = await asyncpg.connect(as_asyncpg_url(url))
    try:
        password_hash = hash_password(password)
        existing = await conn.fetchval(
            "SELECT id FROM crm.users WHERE email = $1", email
        )
        if existing:
            await conn.execute(
                "UPDATE crm.users SET password_hash = $1, full_name = $2, "
                "role = $3::crm.user_role, is_active = true, updated_at = $4 "
                "WHERE email = $5",
                password_hash, name, role, datetime.now(timezone.utc), email,
            )
            print(f"Updated existing user: {email} ({role})")
        else:
            await conn.execute(
                "INSERT INTO crm.users (id, email, password_hash, full_name, role, "
                "is_active, assigned_clients_only, created_at, updated_at) "
                "VALUES ($1, $2, $3, $4, $5::crm.user_role, true, false, $6, $6)",
                uuid.uuid4(), email, password_hash, name, role,
                datetime.now(timezone.utc),
            )
            print(f"Created user: {email} ({role})")
    finally:
        await conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Create/reset an admin user.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--name", default="System Admin")
    parser.add_argument(
        "--role", default="super_admin", choices=[r.value for r in UserRole]
    )
    parser.add_argument(
        "--yes", action="store_true", help="Confirm writing to the database"
    )
    args = parser.parse_args()

    if not args.yes:
        raise SystemExit("Refusing to write without --yes")

    asyncio.run(run(args.email, args.password, args.name, args.role))


if __name__ == "__main__":
    main()
