#!/usr/bin/env python3
"""
Analytics infra sanity check for krcampus.

Checks:
- GA4 measurement ID is configured and looks like a real ID (not a placeholder)
- GA4 Measurement Protocol API secret is configured (needed for server-side events)
- robots.txt / sitemap.xml exist and are reachable, which GSC relies on for ownership
  verification via sitemap submission and crawl access
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient

from app.analytics import GA_API_SECRET, ga4_configured
from app.main import app
from app.settings import DOMAIN, GA_MEASUREMENT_ID

GA4_ID_PATTERN = re.compile(r"^G-[A-Z0-9]{8,}$")


def check_ga_measurement_id() -> tuple[bool, str]:
    if not GA_MEASUREMENT_ID:
        return False, "GA_MEASUREMENT_ID is not set"
    if not GA4_ID_PATTERN.match(GA_MEASUREMENT_ID):
        return False, f"GA_MEASUREMENT_ID '{GA_MEASUREMENT_ID}' does not look like a GA4 ID (G-XXXXXXXXXX)"
    return True, f"GA_MEASUREMENT_ID={GA_MEASUREMENT_ID}"


def check_ga_api_secret() -> tuple[bool, str]:
    if not GA_API_SECRET:
        return False, "GA_API_SECRET is not set; server-side page_view/reaction/compare events are disabled (no-op)"
    return True, "GA_API_SECRET is set; server-side events will be sent"


def check_crawl_access() -> list[tuple[bool, str]]:
    client = TestClient(app)
    results = []
    for path in ("/robots.txt", "/sitemap.xml"):
        resp = client.get(path)
        ok = resp.status_code == 200
        results.append((ok, f"{path} -> {resp.status_code}"))
    return results


def main() -> int:
    print(f"Domain: {DOMAIN}")
    checks = [check_ga_measurement_id(), check_ga_api_secret(), *check_crawl_access()]

    all_ok = True
    for ok, message in checks:
        print(f"[{'OK' if ok else 'WARN'}] {message}")
        all_ok = all_ok and ok

    print(f"[{'OK' if ga4_configured() else 'WARN'}] server-side GA4 event tracking configured: {ga4_configured()}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
