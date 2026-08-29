"""A8.net affiliate banners for KR Campus."""

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
        "click_url": "https://px.a8.net/svt/ejp?a8mat=4BAH9J+13AP0Q+4X1W+5ZMCH",
        "image_url": "https://www21.a8.net/svt/bgt?aid=260829415066&wid=004&eno=01&mid=s00000022946001006000&mc=1",
        "pixel_url": "https://www14.a8.net/0.gif?a8mat=4BAH9J+13AP0Q+4X1W+5ZMCH",
        "label_en": "Agoda — Korea stays",
        "label_ja": "Agoda — 韓国宿泊",
        "desc_en": "Hotels and guesthouses for Korea study trips.",
        "desc_ja": "韓国留学・旅行の宿泊予約。",
        "alt_en": "Agoda — affiliate",
        "alt_ja": "Agoda — アフィリエイト",
    },
    "kkday": {
        "id": "kkday",
        "click_url": "https://px.a8.net/svt/ejp?a8mat=4BAH9J+4DRYEI+52F8+5ZMCH",
        "image_url": "https://www27.a8.net/svt/bgt?aid=260829415265&wid=004&eno=01&mid=s00000023642001006000&mc=1",
        "pixel_url": "https://www14.a8.net/0.gif?a8mat=4BAH9J+4DRYEI+52F8+5ZMCH",
        "label_en": "KKday — Korea activities",
        "label_ja": "KKday — 韓国アクティビティ",
        "desc_en": "Airport transfers and day tours in Korea.",
        "desc_ja": "空港送迎・韓国ツアー予約。",
        "alt_en": "KKday — affiliate",
        "alt_ja": "KKday — アフィリエイト",
    },
    "korean_college": {
        "id": "korean_college",
        "click_url": "https://px.a8.net/svt/ejp?a8mat=4BAH9J+3ME0KQ+51XQ+63OY9",
        "image_url": "https://www23.a8.net/svt/bgt?aid=260829415219&wid=004&eno=01&mid=s00000023579001025000&mc=1",
        "pixel_url": "https://www18.a8.net/0.gif?a8mat=4BAH9J+3ME0KQ+51XQ+63OY9",
        "label_en": "Korean College — online classes",
        "label_ja": "コリアンカレッジ — オンライン韓国語",
        "desc_en": "Online Korean lessons before you arrive.",
        "desc_ja": "渡航前のオンライン韓国語教室。",
        "alt_en": "Korean College — affiliate",
        "alt_ja": "コリアンカレッジ — アフィリエイト",
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
    key = banner_id.upper()
    return {
        "id": src["id"],
        "click_url": os.getenv(f"A8_{key}_CLICK_URL", src["click_url"]),
        "image_url": os.getenv(f"A8_{key}_BANNER_URL", src["image_url"]),
        "pixel_url": os.getenv(f"A8_{key}_PIXEL_URL", src["pixel_url"]),
        "label": src[f"label_{suffix}"],
        "desc": src[f"desc_{suffix}"],
        "alt": src[f"alt_{suffix}"],
    }


def a8_banners_context(
    *,
    slug: str = "",
    lang: str = "en",
    item_type: str = "guide",
) -> dict[str, Any]:
    if not _enabled():
        return {"show_a8_banners": False, "a8_banners": []}

    key = _normalize(slug)
    kind = (item_type or "guide").strip().lower()
    keys: list[str] = []

    if kind in ("school", "university"):
        keys = ["agoda", "korean_college"]
    elif key in GUIDE_A8_KKDAY:
        keys = ["kkday"]
    elif key in GUIDE_A8_LANGUAGE:
        keys = ["korean_college"]
    elif key in GUIDE_A8_AGODA:
        keys = ["agoda"]

    if not keys:
        return {"show_a8_banners": False, "a8_banners": []}

    is_ja = (lang or "en").lower().startswith("ja")
    banners = [_copy(k, lang=lang) for k in keys]
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
    }
