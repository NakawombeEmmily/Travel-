"""Post-deploy smoke test.

Usage:
    python scripts/smoke_test.py [api_base_url]

The base URL may also come from SMOKE_API_URL. Credentials come from
SMOKE_ADMIN_EMAIL / SMOKE_ADMIN_PASSWORD and fall back to the seeded demo
super admin. Render free instances sleep, so the health check retries with a
delay before giving up.

Covered: health, login, client read + create, mock payment create, invoice PDF,
refund, outbox read, admin-ledger reconciliation, analytics summary, CSV export.
The client created here is soft-deleted at the end unless SMOKE_SKIP_CLEANUP=1.
"""
from __future__ import annotations

import os
import sys
import time
import uuid
from typing import Any

import httpx

ADMIN_EMAIL = os.environ.get("SMOKE_ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.environ.get("SMOKE_ADMIN_PASSWORD", "Admin-Demo-2026")
TIMEOUT = float(os.environ.get("SMOKE_TIMEOUT", "30"))
HEALTH_ATTEMPTS = int(os.environ.get("SMOKE_HEALTH_ATTEMPTS", "24"))
HEALTH_DELAY = float(os.environ.get("SMOKE_HEALTH_DELAY", "5"))
SKIP_CLEANUP = os.environ.get("SMOKE_SKIP_CLEANUP", "").lower() in {"1", "true", "yes"}


class Smoke:
    def __init__(self, base: str) -> None:
        self.base = base.rstrip("/")
        self.failures: list[str] = []

    def check(self, name: str, ok: bool, detail: str = "") -> bool:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}{f' {detail}' if detail else ''}")
        if not ok:
            self.failures.append(name)
        return ok

    def section(self, title: str) -> None:
        print(f"\n== {title} ==")

    def wait_for_health(self, client: httpx.Client) -> bool:
        url = f"{self.base}/api/v1/health"
        last = ""
        for attempt in range(1, HEALTH_ATTEMPTS + 1):
            try:
                response = client.get(url, timeout=TIMEOUT)
                last = str(response.status_code)
                if response.status_code == 200:
                    if attempt > 1:
                        print(f"       healthy after {attempt} attempts ({last})")
                    return True
            except httpx.HTTPError as exc:
                last = type(exc).__name__
            print(f"       waiting for cold start {attempt}/{HEALTH_ATTEMPTS} ({last})")
            time.sleep(HEALTH_DELAY)
        return False


def main(base: str) -> int:
    smoke = Smoke(base)
    run = uuid.uuid4().hex[:8]
    headers: dict[str, str] = {}
    client_id: str | None = None
    payment_id: str | None = None

    print(f"Smoke test against {smoke.base} (run {run})")

    with httpx.Client(timeout=TIMEOUT, base_url=smoke.base) as client:
        smoke.section("health")
        if not smoke.wait_for_health(client):
            smoke.check("health", False, f"no response from {smoke.base} after {HEALTH_ATTEMPTS} attempts")
            return report(smoke)
        smoke.check("health", True)

        smoke.section("auth")
        response = client.post(
            f"{smoke.base}/api/v1/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        )
        token = ""
        if smoke.check("login", response.status_code == 200, str(response.status_code)):
            token = response.json().get("access_token", "")
            smoke.check("login_token", bool(token), f"as {ADMIN_EMAIL}")
        if not token:
            return report(smoke)
        headers = {"Authorization": f"Bearer {token}"}

        smoke.section("clients")
        response = client.get("/api/v1/clients?page=1&page_size=5", headers=headers)
        body = response.json() if response.status_code == 200 else {}
        smoke.check(
            "list_clients",
            response.status_code == 200 and isinstance(body.get("items"), list),
            f"status={response.status_code} total={body.get('total', '?')}",
        )

        payload = {
            "full_name": f"Smoke Test Client {run}",
            "passport_number": f"SMOKE-{run}",
            "nationality": "Ugandan",
            "consent_given": True,
        }
        response = client.post("/api/v1/clients", json=payload, headers=headers)
        if smoke.check(
            "create_client", response.status_code == 201, f"status={response.status_code}"
        ):
            client_id = response.json().get("id")

        smoke.section("payments (mock provider)")
        if client_id:
            payment_payload = {
                "client_id": client_id,
                "amount": "10.00",
                "currency": "USD",
                "method": "cash",
                "notes": f"Smoke test {run}",
            }
            response = client.post("/api/v1/payments", json=payment_payload, headers=headers)
            payment_body = response.json() if response.status_code == 201 else {}
            if smoke.check(
                "create_payment",
                response.status_code == 201 and bool(payment_body.get("id")),
                f"status={response.status_code} state={payment_body.get('status', '?')}",
            ):
                payment_id = payment_body.get("id")

        if payment_id:
            response = client.get(f"/api/v1/payments/{payment_id}/invoice", headers=headers)
            is_pdf = response.status_code == 200 and response.content.startswith(b"%PDF")
            smoke.check(
                "invoice_pdf",
                is_pdf,
                f"status={response.status_code} bytes={len(response.content)}",
            )

            response = client.post(f"/api/v1/payments/{payment_id}/refund", headers=headers)
            refund_body = response.json() if response.status_code == 200 else {}
            smoke.check(
                "refund_payment",
                response.status_code == 200 and refund_body.get("status") == "refunded",
                f"status={response.status_code} state={refund_body.get('status', '?')}",
            )

        smoke.section("outbox + admin ledger")
        response = client.get("/api/v1/payments/outbox?page=1&page_size=5", headers=headers)
        outbox_body = response.json() if response.status_code == 200 else {}
        smoke.check(
            "outbox_readable",
            response.status_code == 200 and "total" in outbox_body,
            f"status={response.status_code} total={outbox_body.get('total', '?')}",
        )

        response = client.post("/api/v1/payments/reconcile", headers=headers)
        reconcile_body = response.json() if response.status_code == 200 else {}
        errors = reconcile_body.get("errors", [])
        smoke.check(
            "ledger_reconcile",
            response.status_code == 200 and isinstance(errors, list) and not errors,
            "status={status} checked={checked} created={created} updated={updated} "
            "mismatched={mismatched} errors={err}".format(
                status=response.status_code,
                checked=reconcile_body.get("checked", "?"),
                created=reconcile_body.get("created", "?"),
                updated=reconcile_body.get("updated", "?"),
                mismatched=reconcile_body.get("mismatched", "?"),
                err=len(errors),
            ),
        )

        smoke.section("analytics")
        response = client.get("/api/v1/analytics/summary", headers=headers)
        summary: dict[str, Any] = response.json() if response.status_code == 200 else {}
        smoke.check(
            "analytics_summary",
            response.status_code == 200 and isinstance(summary.get("total_clients"), int),
            "status={status} clients={clients} trips={trips} currencies={cur}".format(
                status=response.status_code,
                clients=summary.get("total_clients", "?"),
                trips=summary.get("total_trips", "?"),
                cur=len(summary.get("revenue_by_currency", [])),
            ),
        )

        response = client.get("/api/v1/analytics/export/payments", headers=headers)
        disposition = response.headers.get("content-disposition", "")
        csv_ok = (
            response.status_code == 200
            and response.headers.get("content-type", "").startswith("text/csv")
            and b"\n" in response.content
            and len(response.content) > 0
        )
        smoke.check(
            "export_csv",
            csv_ok,
            f"status={response.status_code} bytes={len(response.content)} {disposition}",
        )

        smoke.section("cleanup")
        if client_id and not SKIP_CLEANUP:
            response = client.delete(f"/api/v1/clients/{client_id}", headers=headers)
            smoke.check("cleanup_client", response.status_code == 204, str(response.status_code))
        else:
            print("[SKIP] cleanup_client (already deleted or SMOKE_SKIP_CLEANUP=1)")

    return report(smoke)


def report(smoke: Smoke) -> int:
    failed = len(smoke.failures)
    print(f"\nSmoke test {'PASSED' if not failed else 'FAILED'}: {failed} failure(s)")
    if smoke.failures:
        print(f"Failed: {', '.join(smoke.failures)}")
    return 0 if not failed else 1


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("SMOKE_API_URL")
    if not target:
        print("Usage: python scripts/smoke_test.py <api_base_url>")
        print("   or: SMOKE_API_URL=... python scripts/smoke_test.py")
        sys.exit(2)
    sys.exit(main(target))
