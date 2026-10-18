"""Post-deploy smoke test. Usage: python scripts/smoke_test.py <api_base_url>"""
from __future__ import annotations

import sys

import httpx


def main(base: str) -> int:
    base = base.rstrip("/")
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {name} {detail}")
        if not ok:
            failures.append(name)

    r = httpx.get(f"{base}/api/v1/health", timeout=30)
    check("health", r.status_code == 200, str(r.status_code))

    r = httpx.post(
        f"{base}/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "Admin123!"},
        timeout=30,
    )
    check("login", r.status_code == 200, str(r.status_code))
    if r.status_code != 200:
        print(f"Smoke test failed: {len(failures)} failure(s)")
        return 1

    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    r = httpx.get(f"{base}/api/v1/clients?page=1&page_size=5", headers=headers, timeout=30)
    check("list_clients", r.status_code == 200, str(r.status_code))

    payload = {
        "full_name": "Smoke Test Client",
        "passport_number": f"SMOKE{token[-6:]}",
        "nationality": "Ugandan",
        "consent_given": True,
    }
    r = httpx.post(f"{base}/api/v1/clients", json=payload, headers=headers, timeout=30)
    check("create_client", r.status_code == 201, str(r.status_code))

    print(f"\nSmoke test {'PASSED' if not failures else 'FAILED'}: {len(failures)} failure(s)")
    return 0 if not failures else 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/smoke_test.py <api_base_url>")
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
