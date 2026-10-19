"""Maintenance CLI for the scheduled jobs.

Runs the outbox flush, reminder sweep and payment reconciliation without
needing Redis/Celery, so Render cron jobs can invoke them directly::

    python -m app.cli outbox [limit]
    python -m app.cli reminders
    python -m app.cli reconcile
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Any

from app.db.session import SessionLocal
from app.services.outbox import OutboxService
from app.services.reconciliation import ReconciliationService
from app.services.reminders import run_reminders


async def flush_outbox(limit: int) -> dict[str, int]:
    async with SessionLocal() as session:
        result = await OutboxService(session).process_pending(limit=limit)
        await session.commit()
        return result


async def send_reminders() -> dict[str, Any]:
    async with SessionLocal() as session:
        result = await run_reminders(session)
        await session.commit()
        return result


async def reconcile_payments() -> dict[str, Any]:
    async with SessionLocal() as session:
        result = await ReconciliationService(session).reconcile()
        await session.commit()
        return result.model_dump()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m app.cli",
        description="Run a scheduled maintenance job.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    outbox = sub.add_parser("outbox", help="flush pending outbox events")
    outbox.add_argument(
        "limit",
        nargs="?",
        type=int,
        default=100,
        help="maximum events to process (default: 100)",
    )
    sub.add_parser("reminders", help="send visa/passport expiry reminders")
    sub.add_parser("reconcile", help="reconcile payments against the admin ledger")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "outbox":
        if not 1 <= args.limit <= 10_000:
            parser.error("limit must be between 1 and 10000")
        payload: dict[str, Any] = asyncio.run(flush_outbox(args.limit))
    elif args.command == "reminders":
        payload = asyncio.run(send_reminders())
    else:
        payload = asyncio.run(reconcile_payments())

    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # pragma: no cover - surfaced to cron logs
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
