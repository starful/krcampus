"""Amazon JP Associates — content-kind search links (tag=starful06-22)."""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import quote_plus

TAG = os.getenv("AMAZON_JP_TAG", "starful06-22")

# kind → Japanese search keyword (Amazon.co.jp)
_KEYWORDS: dict[str, str] = {
    "default": "韓国 留学 グッズ",
    "housing": "一人暮らし 寝具",
    "language": "韓国語 参考書",
    "topik": "韓国語 参考書",
    "arrival": "海外旅行 便利グッズ",
    "packing": "海外旅行 便利グッズ",
    "school": "留学 準備",
}

# kind → (label_en, label_ja, desc_en, desc_ja)
_COPY: dict[str, tuple[str, str, str, str]] = {
    "default": (
        "Amazon — Korea study goods",
        "Amazon — 韓国留学グッズ",
        "Handy items for studying in Korea.",
        "韓国留学に役立つグッズ。",
    ),
    "housing": (
        "Amazon — bedding for living alone",
        "Amazon — 一人暮らし 寝具",
        "Bedding and basics for your new room.",
        "新生活の寝具・生活用品。",
    ),
    "language": (
        "Amazon — Korean study books",
        "Amazon — 韓国語 参考書",
        "Textbooks and TOPIK prep books.",
        "韓国語の参考書・TOPIK対策本。",
    ),
    "arrival": (
        "Amazon — travel gadgets",
        "Amazon — 海外旅行 便利グッズ",
        "Useful gear for arrival and trips abroad.",
        "渡航・海外生活に便利なグッズ。",
    ),
    "school": (
        "Amazon — study abroad prep",
        "Amazon — 留学 準備",
        "Items to prepare before you leave.",
        "留学前の準備アイテム。",
    ),
}
_COPY["topik"] = _COPY["language"]
_COPY["packing"] = _COPY["arrival"]

_GUIDE_KIND: dict[str, str] = {
    "arrival": "arrival",
    "packing-korea": "packing",
    "topik": "topik",
    "topik-study-plan": "topik",
    "topik-vs-klat": "topik",
    "korean-study-apps": "language",
    "dorm-application": "housing",
    "goshiwon-guide": "housing",
    "housing": "housing",
}


def search_url(keyword: str) -> str:
    k = (keyword or "").strip() or _KEYWORDS["default"]
    return (
        f"https://www.amazon.co.jp/s?k={quote_plus(k)}"
        f"&tag={TAG}&linkCode=ll2&ref_=as_li_ss_tl"
    )


def _enabled() -> bool:
    return os.getenv("AMAZON_KRCAMPUS_ENABLED", "1").strip().lower() in (
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


def kind_for(slug: str = "", item_type: str = "guide") -> str:
    """Map a page (guide slug / school type) to an Amazon kind."""
    if (item_type or "guide").strip().lower() in ("school", "university"):
        return "school"
    return _GUIDE_KIND.get(_normalize(slug), "default")


def amazon_context(*, kind: str = "default", lang: str = "en") -> dict[str, Any]:
    if not _enabled():
        return {"show_amazon": False, "amazon_cta": None, "amazon_note": ""}
    key = (kind or "default").strip().lower() or "default"
    if key not in _KEYWORDS:
        key = "default"
    keyword = _KEYWORDS[key]
    is_ja = (lang or "en").lower().startswith("ja")
    label_en, label_ja, desc_en, desc_ja = _COPY[key]
    return {
        "show_amazon": True,
        "amazon_note": (
            "アフィリエイト広告 · 新しいタブで開きます" if is_ja else "Affiliate ads · opens in new tab"
        ),
        "amazon_cta": {
            "id": "amazon",
            "click_url": search_url(keyword),
            "label": label_ja if is_ja else label_en,
            "desc": desc_ja if is_ja else desc_en,
            "keyword": keyword,
        },
    }
