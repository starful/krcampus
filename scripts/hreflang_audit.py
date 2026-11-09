#!/usr/bin/env python3
"""
school 상세 페이지 등 전체 페이지의 hreflang(en/ja) 누락 여부 점검.

주의: krcampus.net은 en/ja 두 언어만 서비스한다 (app/i18n.py, app/middleware.py의
lang_kr_alias_middleware 참고 — "kr"은 ko 콘텐츠가 아니라 "ja"의 구 별칭이다).
그래서 ko 전용 hreflang은 의도적으로 존재하지 않으며, 이 스크립트도 ko를
"없는데 고쳐야 할 결함"이 아니라 "원래 없는 언어"로 취급한다. 점검 대상은
en/ja/x-default 세 태그가 실제 응답 HTML에 빠짐없이 나오는지 뿐이다.

사용:
  python scripts/hreflang_audit.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient

from app.content_loader import load_guides, load_school_data
from app.main import app
from app.settings import DOMAIN

REQUIRED_HREFLANGS = ("en", "ja", "x-default")

HREFLANG_RE = re.compile(
    r'<link[^>]+rel=["\']alternate["\'][^>]+hreflang=["\']([^"\']+)["\'][^>]+href=["\']([^"\']+)["\']',
    re.IGNORECASE,
)


def extract_hreflangs(html: str) -> dict[str, str]:
    return {lang: href for lang, href in HREFLANG_RE.findall(html)}


def check_page(client: TestClient, path: str) -> list[str]:
    """path에 대해 발견된 문제 메시지 목록을 반환한다 (문제 없으면 빈 리스트)."""
    problems: list[str] = []
    res = client.get(path)
    if res.status_code != 200:
        problems.append(f"{path}: 페이지가 {res.status_code}를 반환해 hreflang을 확인할 수 없음")
        return problems

    tags = extract_hreflangs(res.text)
    for required in REQUIRED_HREFLANGS:
        if required not in tags:
            problems.append(f"{path}: hreflang='{required}' 태그 누락")

    en_href = tags.get("en")
    ja_href = tags.get("ja")
    if en_href and not en_href.startswith(DOMAIN):
        problems.append(f"{path}: hreflang='en' href가 DOMAIN({DOMAIN})으로 시작하지 않음 ({en_href})")
    if ja_href and "lang=ja" not in ja_href:
        problems.append(f"{path}: hreflang='ja' href에 lang=ja 쿼리가 없음 ({ja_href})")

    return problems


def main() -> int:
    client = TestClient(app)
    problems: list[str] = []
    checked = 0

    static_pages = ["/", "/about", "/guide", "/schools", "/universities", "/contact", "/policy", "/compare"]
    for path in static_pages:
        problems.extend(check_page(client, path))
        checked += 1

    schools_en, _ = load_school_data("en")
    for school in schools_en:
        school_id = school.get("id")
        if not school_id:
            continue
        problems.extend(check_page(client, f"/school/{school_id}"))
        checked += 1

    for guide in load_guides("en"):
        slug = guide["link"].split("/")[-1].split("?")[0]
        problems.extend(check_page(client, f"/guide/{slug}"))
        checked += 1

    print("== hreflang 점검 (en/ja/x-default, ko는 미서비스 언어로 대상 아님) ==")
    print(f"점검한 페이지: {checked}개")
    if problems:
        print(f"발견된 문제: {len(problems)}건")
        for p in problems:
            print(f"[FAIL] {p}")
        return 1

    print("문제 없음: 모든 페이지에 hreflang en/ja/x-default가 정상적으로 존재함")
    return 0


if __name__ == "__main__":
    sys.exit(main())
