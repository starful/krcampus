#!/usr/bin/env python3
"""
SEO smoke checks that should run before deployment.

Checks:
- core pages return 200
- canonical tag exists and matches expected URL
- no accidental noindex directives in HTML
- robots.txt includes sitemap and does not block crawling
- sitemap.xml is valid enough for indexing
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from dataclasses import dataclass

from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.main import app, DOMAIN
from app.utils import load_school_data, load_guides


@dataclass
class CheckResult:
    ok: bool
    message: str


def _extract_canonical(html: str) -> str | None:
    match = re.search(
        r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']',
        html,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    return match.group(1).strip()


def _has_noindex(html: str) -> bool:
    return bool(
        re.search(
            r'<meta[^>]+name=["\']robots["\'][^>]+content=["\'][^"\']*noindex',
            html,
            flags=re.IGNORECASE,
        )
    )


def _has_meta_description(html: str) -> bool:
    return bool(
        re.search(
            r'<meta[^>]+name=["\']description["\'][^>]+content=["\'][^"\']+["\']',
            html,
            flags=re.IGNORECASE,
        )
    )


def run_checks() -> tuple[list[CheckResult], list[CheckResult]]:
    client = TestClient(app)
    passed: list[CheckResult] = []
    failed: list[CheckResult] = []

    html_targets = [
        ("/", f"{DOMAIN}/"),
        ("/?lang=kr", f"{DOMAIN}/?lang=kr"),
        ("/schools", f"{DOMAIN}/schools"),
        ("/schools?lang=kr", f"{DOMAIN}/schools?lang=kr"),
        ("/universities", f"{DOMAIN}/universities"),
        ("/universities?lang=kr", f"{DOMAIN}/universities?lang=kr"),
        ("/guide", f"{DOMAIN}/guide"),
        ("/guide?lang=kr", f"{DOMAIN}/guide?lang=kr"),
        ("/about", f"{DOMAIN}/about"),
        ("/policy", f"{DOMAIN}/policy"),
        ("/contact", f"{DOMAIN}/contact"),
    ]

    for path, expected_canonical in html_targets:
        res = client.get(path)
        if res.status_code != 200:
            failed.append(CheckResult(False, f"{path}: expected 200, got {res.status_code}"))
            continue

        html = res.text
        canonical = _extract_canonical(html)
        if not canonical:
            failed.append(CheckResult(False, f"{path}: canonical tag missing"))
            continue
        if canonical != expected_canonical:
            failed.append(
                CheckResult(
                    False,
                    f"{path}: canonical mismatch (expected {expected_canonical}, got {canonical})",
                )
            )
            continue
        if _has_noindex(html):
            failed.append(CheckResult(False, f"{path}: noindex detected in robots meta"))
            continue
        if not _has_meta_description(html):
            failed.append(CheckResult(False, f"{path}: meta description missing"))
            continue

        passed.append(CheckResult(True, f"{path}: HTML SEO checks passed"))

    schools, _ = load_school_data("en")
    school_samples = [s.get("id") for s in schools if s.get("id")][:3]
    guide_samples = []
    for guide in load_guides("en"):
        slug = guide.get("link", "").split("/")[-1].split("?")[0]
        if slug:
            guide_samples.append(slug)
        if len(guide_samples) >= 3:
            break

    for school_id in school_samples:
        detail_path = f"/school/{school_id}"
        res = client.get(detail_path)
        if res.status_code != 200:
            failed.append(CheckResult(False, f"{detail_path}: expected 200, got {res.status_code}"))
            continue
        canonical = _extract_canonical(res.text)
        expected = f"{DOMAIN}{detail_path}"
        if canonical != expected:
            failed.append(CheckResult(False, f"{detail_path}: canonical mismatch"))
        elif _has_noindex(res.text):
            failed.append(CheckResult(False, f"{detail_path}: noindex detected"))
        else:
            passed.append(CheckResult(True, f"{detail_path}: detail SEO checks passed"))

    for slug in guide_samples:
        detail_path = f"/guide/{slug}"
        res = client.get(detail_path)
        if res.status_code != 200:
            failed.append(CheckResult(False, f"{detail_path}: expected 200, got {res.status_code}"))
            continue
        canonical = _extract_canonical(res.text)
        expected = f"{DOMAIN}{detail_path}"
        if canonical != expected:
            failed.append(CheckResult(False, f"{detail_path}: canonical mismatch"))
        elif _has_noindex(res.text):
            failed.append(CheckResult(False, f"{detail_path}: noindex detected"))
        else:
            passed.append(CheckResult(True, f"{detail_path}: detail SEO checks passed"))

    robots = client.get("/robots.txt")
    if robots.status_code != 200:
        failed.append(CheckResult(False, f"/robots.txt: expected 200, got {robots.status_code}"))
    else:
        body = robots.text
        if "Disallow: /" in body:
            failed.append(CheckResult(False, "/robots.txt: blocks entire site with Disallow: /"))
        elif f"Sitemap: {DOMAIN}/sitemap.xml" not in body:
            failed.append(CheckResult(False, "/robots.txt: sitemap URL missing or incorrect"))
        else:
            passed.append(CheckResult(True, "/robots.txt: checks passed"))

    sitemap = client.get("/sitemap.xml")
    if sitemap.status_code != 200:
        failed.append(CheckResult(False, f"/sitemap.xml: expected 200, got {sitemap.status_code}"))
    else:
        body = sitemap.text
        if "<urlset" not in body or "<loc>" not in body:
            failed.append(CheckResult(False, "/sitemap.xml: missing urlset/loc tags"))
        elif "<lastmod>" not in body:
            failed.append(CheckResult(False, "/sitemap.xml: missing lastmod tags"))
        elif 'hreflang="en"' not in body or 'hreflang="ja"' not in body:
            failed.append(CheckResult(False, "/sitemap.xml: missing hreflang alternates"))
        elif "http://127.0.0.1" in body or "localhost" in body:
            failed.append(CheckResult(False, "/sitemap.xml: found localhost URL"))
        else:
            passed.append(CheckResult(True, "/sitemap.xml: checks passed"))

    redirect_res = client.get("/privacy", follow_redirects=False)
    if redirect_res.status_code != 301:
        failed.append(CheckResult(False, "/privacy: expected 301 legacy redirect"))
    elif redirect_res.headers.get("location") != "/policy":
        failed.append(CheckResult(False, "/privacy: redirect target mismatch"))
    else:
        passed.append(CheckResult(True, "/privacy: legacy redirect checks passed"))

    for icon_path in ["/favicon.ico", "/favicon-32x32.png", "/favicon-48x48.png", "/site.webmanifest"]:
        icon_res = client.get(icon_path)
        if icon_res.status_code != 200:
            failed.append(CheckResult(False, f"{icon_path}: expected 200, got {icon_res.status_code}"))
        else:
            passed.append(CheckResult(True, f"{icon_path}: checks passed"))

    home = client.get("/")
    if home.status_code == 200:
        for needle in [
            'rel="icon" href="/favicon.ico"',
            'href="/favicon-48x48.png"',
            'href="/site.webmanifest"',
            '"@type": "Organization"',
        ]:
            if needle not in home.text:
                failed.append(CheckResult(False, f"/: missing {needle}"))
            else:
                passed.append(CheckResult(True, f"/: contains {needle}"))

    return passed, failed


def main() -> int:
    passed, failed = run_checks()

    print("== SEO Guard Results ==")
    for item in passed:
        print(f"[PASS] {item.message}")
    for item in failed:
        print(f"[FAIL] {item.message}")

    if failed:
        print(f"\nSEO guard failed: {len(failed)} issue(s).")
        return 1

    print(f"\nSEO guard passed: {len(passed)} checks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
