#!/usr/bin/env python3
"""
미색인 URL 우선순위별 재제출 스크립트.

scripts/gsc_index_report.py 가 뽑아낸 "미색인" URL 목록을 받아, Google
Indexing API(urlNotifications:publish)로 재크롤링을 요청한다. sitemap
priority가 높은 URL부터 순서대로 보내고, 하루 할당량(기본 180건, 여유분
확보)을 넘기지 않는다.

주의: Indexing API는 공식적으로는 JobPosting/BroadcastEvent 구조화 데이터가
있는 페이지용으로 안내되어 있다. 일반 페이지에도 요청 자체는 받아주지만
재색인을 보장하지는 않으므로, 이 스크립트는 "최대한 빨리 크롤링 신호를
보내는" 보조 수단이며 Search Console 수동 재제출을 대체하지 않는다.

필요 환경변수:
  GOOGLE_APPLICATION_CREDENTIALS  서비스 계정 키 파일 경로
                                   (해당 계정이 Search Console 속성에
                                   "소유자"로 추가되어 있어야 함 — Indexing
                                   API는 user 권한으로는 호출할 수 없음)
  GSC_SITE_URL                    gsc_index_report.py 와 동일 (CSV 재사용 시 불필요)

사용 예:
  # 1) 먼저 미색인 목록을 CSV로 뽑고
  python scripts/gsc_index_report.py --out unindexed.csv

  # 2) 우선순위 순으로 재제출
  python scripts/gsc_resubmit.py --from-csv unindexed.csv
  python scripts/gsc_resubmit.py --from-csv unindexed.csv --dry-run
  python scripts/gsc_resubmit.py --from-csv unindexed.csv --quota 50
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
SCRIPTS_DIR = Path(__file__).resolve().parent
for p in (ROOT_DIR, SCRIPTS_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from gsc_index_report import collect_site_urls, inspect_url, load_credentials  # noqa: E402

INDEXING_SCOPES = ["https://www.googleapis.com/auth/indexing"]
PUBLISH_ENDPOINT = "https://indexing.googleapis.com/v3/urlNotifications:publish"
DEFAULT_QUOTA = 180  # Indexing API 일일 할당량은 보통 200건 — 여유분 확보
REQUEST_INTERVAL_SEC = 1.0


def load_unindexed_from_csv(path: str) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    rows.sort(key=lambda row: row.get("priority", "0"), reverse=True)
    return rows


def find_unindexed(limit: int | None) -> list[dict[str, str]]:
    """GSC URL Inspection API로 미색인 URL을 직접 조회한다 (--from-csv 미지정 시)."""
    from google.auth.transport.requests import Request as AuthRequest
    from app.settings import DOMAIN

    site_url = os.getenv("GSC_SITE_URL", f"{DOMAIN}/")
    creds = load_credentials()

    targets = collect_site_urls()
    if limit:
        targets = targets[:limit]

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
        if i < len(targets):
            time.sleep(REQUEST_INTERVAL_SEC)

    unindexed.sort(key=lambda row: row["priority"], reverse=True)
    return unindexed


def publish(session, token: str, url: str) -> dict:
    resp = session.post(
        PUBLISH_ENDPOINT,
        headers={"Authorization": f"Bearer {token}"},
        json={"url": url, "type": "URL_UPDATED"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def main() -> int:
    from google.auth.transport.requests import Request as AuthRequest

    parser = argparse.ArgumentParser(description="미색인 URL 우선순위별 재제출")
    parser.add_argument("--from-csv", default=None, help="gsc_index_report.py --out 결과 CSV 경로")
    parser.add_argument("--limit", type=int, default=None, help="--from-csv 미지정 시 점검할 URL 수 제한")
    parser.add_argument("--quota", type=int, default=DEFAULT_QUOTA, help="이번 실행에서 재제출할 최대 건수")
    parser.add_argument("--dry-run", action="store_true", help="실제로 보내지 않고 대상만 출력")
    args = parser.parse_args()

    if args.from_csv:
        unindexed = load_unindexed_from_csv(args.from_csv)
    else:
        unindexed = find_unindexed(args.limit)

    targets = unindexed[: args.quota]
    print(f"재제출 대상: {len(unindexed)}건 중 {len(targets)}건 (quota={args.quota})")

    if args.dry_run:
        for row in targets:
            print(f"  [DRY] ({row['priority']}) {row['url']}")
        return 0

    try:
        creds = load_credentials(INDEXING_SCOPES)
    except Exception as e:
        print(f"[ERROR] {e}")
        return 1

    session = requests.Session()
    ok, failed = 0, 0
    for i, row in enumerate(targets, start=1):
        if not creds.valid:
            creds.refresh(AuthRequest())
        try:
            publish(session, creds.token, row["url"])
            ok += 1
            print(f"[SENT]   ({row['priority']}) {row['url']}")
        except Exception as e:
            failed += 1
            print(f"[FAILED] ({row['priority']}) {row['url']} — {e}")
        if i < len(targets):
            time.sleep(REQUEST_INTERVAL_SEC)

    print(f"\n재제출 완료: 성공 {ok}건 / 실패 {failed}건")
    return 0


if __name__ == "__main__":
    sys.exit(main())
