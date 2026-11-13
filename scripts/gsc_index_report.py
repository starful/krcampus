#!/usr/bin/env python3
"""
Search Console 색인 공백 URL 추출 스크립트.

GSC URL Inspection API로 사이트의 모든 URL(언어별)을 점검해 "색인되지 않음"
상태인 URL만 모아 우선순위(sitemap priority) 순으로 출력한다. GSC API는
재제출(Request Indexing) 자체를 지원하지 않으므로, 이 스크립트는 Search
Console UI에서 수동으로 재제출할 URL 목록을 뽑아주는 역할만 한다.

필요 환경변수:
  GOOGLE_APPLICATION_CREDENTIALS  서비스 계정 키 파일 경로
                                   (해당 계정이 Search Console 속성에 사용자로 추가되어 있어야 함)
  GSC_SITE_URL                    Search Console에 등록된 속성 값
                                   예: "https://krcampus.net/" 또는 "sc-domain:krcampus.net"
                                   (미설정 시 app.settings.DOMAIN 기준으로 추정)

사용 예:
  python scripts/gsc_index_report.py
  python scripts/gsc_index_report.py --limit 20       # 테스트용 일부만 점검
  python scripts/gsc_index_report.py --out report.csv # CSV로도 저장
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from pathlib import Path

import requests

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.content_loader import load_guides, load_school_data
from app.settings import DOMAIN, SHOW_STAYS_UI

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
INSPECT_ENDPOINT = "https://searchconsole.googleapis.com/v1/urlInspection/index:inspect"
REQUEST_INTERVAL_SEC = 0.3  # GSC 할당량: 속성당 분당 약 600건


def collect_site_urls() -> list[dict[str, str]]:
    """app/routes/seo_routes.py 의 sitemap과 동일한 기준으로 점검 대상 URL을 만든다."""
    urls: list[dict[str, str]] = []

    def add(path: str, priority: str):
        urls.append({"path": path, "lang": "en", "url": f"{DOMAIN}{path}", "priority": priority})
        urls.append({"path": path, "lang": "ja", "url": f"{DOMAIN}{path}?lang=ja", "priority": priority})

    add("/", "1.0")
    static_pages = ["/about", "/guide", "/schools", "/universities", "/contact", "/policy", "/compare"]
    if SHOW_STAYS_UI:
        static_pages.append("/stays")
    for page in static_pages:
        add(page, "0.8")

    schools_en, _ = load_school_data("en")
    for school in schools_en:
        school_id = school.get("id")
        if school_id:
            add(f"/school/{school_id}", "0.9")

    for guide in load_guides("en"):
        slug = guide["link"].split("/")[-1].split("?")[0]
        add(f"/guide/{slug}", "0.7")

    return urls


def load_credentials(scopes: list[str] | None = None):
    from google.auth.transport.requests import Request as AuthRequest
    from google.oauth2 import service_account

    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not cred_path or not os.path.exists(cred_path):
        raise RuntimeError(
            "GOOGLE_APPLICATION_CREDENTIALS가 설정되어 있지 않거나 파일을 찾을 수 없습니다. "
            "Search Console 속성에 사용자로 추가된 서비스 계정 키 파일 경로를 지정하세요."
        )
    creds = service_account.Credentials.from_service_account_file(cred_path, scopes=scopes or SCOPES)
    creds.refresh(AuthRequest())
    return creds


def inspect_url(session, token: str, site_url: str, inspection_url: str) -> dict:
    resp = session.post(
        INSPECT_ENDPOINT,
        headers={"Authorization": f"Bearer {token}"},
        json={"inspectionUrl": inspection_url, "siteUrl": site_url},
        timeout=30,
    )
    resp.raise_for_status()
    status = resp.json().get("inspectionResult", {}).get("indexStatusResult", {})
    return {
        "verdict": status.get("verdict", "VERDICT_UNSPECIFIED"),
        "coverage_state": status.get("coverageState", ""),
        "last_crawl_time": status.get("lastCrawlTime", ""),
    }


def main() -> int:
    from google.auth.transport.requests import Request as AuthRequest

    parser = argparse.ArgumentParser(description="GSC 색인 공백 URL 추출")
    parser.add_argument("--limit", type=int, default=None, help="점검할 URL 수 제한 (테스트용)")
    parser.add_argument("--out", default=None, help="결과를 CSV로도 저장할 경로")
    args = parser.parse_args()

    site_url = os.getenv("GSC_SITE_URL", f"{DOMAIN}/")

    try:
        creds = load_credentials()
    except Exception as e:
        print(f"[ERROR] {e}")
        return 1

    targets = collect_site_urls()
    if args.limit:
        targets = targets[: args.limit]

    session = requests.Session()
    unindexed: list[dict[str, str]] = []

    for i, target in enumerate(targets, start=1):
        if not creds.valid:
            creds.refresh(AuthRequest())
        try:
            result = inspect_url(session, creds.token, site_url, target["url"])
        except Exception as e:
            print(f"[WARN] {target['url']}: 점검 실패 — {e}")
            time.sleep(REQUEST_INTERVAL_SEC)
            continue

        if result["verdict"] != "PASS":
            unindexed.append({**target, **result})
            print(f"[MISSING] ({target['priority']}) {target['url']} — {result['coverage_state'] or result['verdict']}")
        else:
            print(f"[OK]      ({target['priority']}) {target['url']}")

        if i < len(targets):
            time.sleep(REQUEST_INTERVAL_SEC)

    unindexed.sort(key=lambda row: row["priority"], reverse=True)

    print(f"\n점검 완료: {len(targets)}건 중 미색인 {len(unindexed)}건")
    for row in unindexed:
        print(f"  ({row['priority']}) {row['url']} — {row['coverage_state'] or row['verdict']}")

    if args.out:
        out_path = Path(args.out)
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=["priority", "lang", "path", "url", "verdict", "coverage_state", "last_crawl_time"]
            )
            writer.writeheader()
            writer.writerows(unindexed)
        print(f"\nCSV 저장: {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
