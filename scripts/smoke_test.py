#!/usr/bin/env python3
"""Smoke-test a running Lale Bistro deployment.

Usage:
    BASE_URL=https://your-domain TOOL_SECRET=... python scripts/smoke_test.py

Stdlib only on purpose: this must run against a deployed instance without
installing the project's own dependencies.
"""
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000").rstrip("/")
TOOL_SECRET = os.environ.get("TOOL_SECRET", "")


def _request(method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if TOOL_SECRET:
        req.add_header("X-Tool-Secret", TOOL_SECRET)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read() or b"{}")


def _next_open_slot_iso() -> str:
    dt = (datetime.now() + timedelta(days=1)).replace(
        hour=19, minute=0, second=0, microsecond=0
    )
    while dt.weekday() == 0:  # skip Monday
        dt += timedelta(days=1)
    return dt.isoformat()


def main() -> int:
    checks: list[tuple[str, bool]] = []

    status, _ = _request("GET", "/health")
    checks.append(("health", status == 200))

    status, body = _request(
        "POST",
        "/api/tools/check-availability",
        {
            "tool_call_id": "smoke-availability",
            "party_size": 2,
            "requested_time": _next_open_slot_iso(),
        },
    )
    checks.append(("check-availability", status == 200 and "available" in body))

    status, body = _request(
        "POST",
        "/api/tools/search-menu",
        {"tool_call_id": "smoke-menu", "query": "kebap"},
    )
    checks.append(("search-menu", status == 200 and "items" in body))

    for name, ok in checks:
        print(f"{'PASS' if ok else 'FAIL'}: {name}")

    failed = [name for name, ok in checks if not ok]
    if failed:
        print(f"smoke test failed: {', '.join(failed)}", file=sys.stderr)
        return 1

    print("smoke test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
