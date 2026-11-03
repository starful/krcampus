"""Affiliate banners for KR Campus — Agoda Partners only (A8 KKday/Korean College removed)."""

from __future__ import annotations

import os
from typing import Any

GUIDE_A8_KKDAY: frozenset[str] = frozenset({"arrival", "packing-korea"})
GUIDE_A8_LANGUAGE: frozenset[str] = frozenset(
    {"topik", "topik-study-plan", "topik-vs-klat", "korean-study-apps"}
)
GUIDE_A8_AGODA: frozenset[str] = frozenset(
    {
        "dorm-application",
        "goshiwon-guide",
        "housing",
        "seoul-neighborhoods",
        "urban-lifestyle-seoul-schools",
        "busan-student-life",
        "monthly-budget-seoul",
        "monthly-budget-busan",
    }
)

_BANNERS: dict[str, dict[str, str]] = {
    "agoda": {
        "id": "agoda",
        # Agoda Partners (CID) — filled in _copy
        "click_url": "",
        "image_url": "",
        "pixel_url": "",
        "label_en": "Agoda — Korea stays",
        "label_ja": "Agoda — 韓国宿泊",
        "desc_en": "Hotels and guesthouses for Korea study trips.",
        "desc_ja": "韓国留学・旅行の宿泊予約。",
        "alt_en": "Agoda — hotels",
        "alt_ja": "Agoda — 宿泊",
    },
}


def _enabled() -> bool:
    return os.getenv("A8_KRCAMPUS_ENABLED", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _normalize(slug: str) -> str:
    s = (slug or "").strip().lower()
    if s.endswith("_ja"):
        s = s[:-3]
    if s.startswith("guide_"):
        s = s[6:]
    return s


def _copy(banner_id: str, *, lang: str) -> dict[str, str]:
    src = _BANNERS[banner_id]
    is_ja = (lang or "en").lower().startswith("ja")
    suffix = "ja" if is_ja else "en"
    try:
        from agoda_partners import url_for_location
    except ImportError:
        from .agoda_partners import url_for_location
    click = url_for_location(
        lang=lang,
        country="kr",
        default_city=14690,
    )
    return {
        "id": src["id"],
        "click_url": click,
        "image_url": "",
        "pixel_url": "",
        "label": src[f"label_{suffix}"],
        "desc": src[f"desc_{suffix}"],
        "alt": src[f"alt_{suffix}"],
    }


def a8_housing_context(
    *,
    page_kind: str = "stays_list",
    lang: str = "en",
    stay_id: str = "",
) -> dict[str, Any]:
    """Agoda CTA on the student-housing list/detail pages (no Korea share-house A8 program yet)."""
    if not _enabled():
        return {
            "show_a8_housing": False,
            "a8_housing_banners": [],
            "a8_housing_note": "",
            "a8_housing_title": "",
            "a8_housing_desc": "",
        }

    is_ja = (lang or "en").lower().startswith("ja")
    banner = _copy("agoda", lang=lang)
    return {
        "show_a8_housing": True,
        "a8_housing_banners": [banner],
        "a8_housing_title": "留学生向け住居パートナー（広告）" if is_ja else "Student housing partners",
        "a8_housing_desc": "",
        "a8_housing_note": "アフィリエイト広告 · 新しいタブで開きます" if is_ja else "Affiliate ads · opens in new tab",
    }


def a8_banners_context(
    *,
    slug: str = "",
    lang: str = "en",
    item_type: str = "guide",
) -> dict[str, Any]:
    if not _enabled():
        return {
            "show_a8_banners": False,
            "a8_banners": [],
            "agoda_cta": None,
            "show_agoda_cta": False,
        }

    key = _normalize(slug)
    kind = (item_type or "guide").strip().lower()
    keys: list[str] = []

    # Agoda only — KKday / Korean College (px.a8.net) removed.
    if (
        kind in ("school", "university")
        or key in GUIDE_A8_KKDAY
        or key in GUIDE_A8_LANGUAGE
        or key in GUIDE_A8_AGODA
    ):
        keys = ["agoda"]

    if not keys:
        return {
            "show_a8_banners": False,
            "a8_banners": [],
            "agoda_cta": None,
            "show_agoda_cta": False,
        }

    is_ja = (lang or "en").lower().startswith("ja")
    banners = [_copy(k, lang=lang) for k in keys]
    agoda = next((b for b in banners if b.get("id") == "agoda"), None)
    return {
        "show_a8_banners": True,
        "a8_banners": banners,
        "a8_banners_title": (
            "韓国留学サポート（広告）" if is_ja else "Korea study partners"
        ),
        "a8_banners_note": (
            "アフィリエイト広告 · 新しいタブで開きます"
            if is_ja
            else "Affiliate ads · opens in new tab"
        ),
        "agoda_cta": agoda,
        "show_agoda_cta": agoda is not None,
    }
