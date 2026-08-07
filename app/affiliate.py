"""Affiliate CTAs for KR Campus.

- Amazon.co.jp search: EN + JA (Associates tag)
- Klook Travelpayouts links: arrival / eSIM / packing guides + school/university
"""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import quote_plus

AMAZON_TAG = os.getenv("AMAZON_ASSOCIATE_TAG", "starful06-22")

# Travelpayouts krcampus Klook short link (Korea trip / eSIM — not JP onsen).
KLOOK_URL_DEFAULT = "https://klook.tpo.mx/ED7IfKaq"
KLOOK_URL_EN = os.getenv("KLOOK_URL_EN", KLOOK_URL_DEFAULT)
KLOOK_URL_JA = os.getenv("KLOOK_URL_JA", KLOOK_URL_DEFAULT)

SCHOOL_BOOK_KEYWORD = "TOPIK 問題集"
UNIVERSITY_BOOK_KEYWORD = "TOPIK 問題集"

# Guides that show a Klook Travelpayouts CTA (eSIM / arrival prep).
GUIDE_KLOOK_SLUGS: frozenset[str] = frozenset(
    {
        "arrival",
        "sim-esim-korea",
        "packing-korea",
        "mobile",
    }
)

# slug → Amazon.co.jp search keyword (JP store)
GUIDE_AMAZON_MAP: dict[str, str] = {
    # housing / packing
    "dorm-application": "寝具セット シングル",
    "goshiwon-guide": "寝具セット シングル",
    "housing": "収納ボックス",
    "packing-korea": "スーツケース",
    "seoul-neighborhoods": "旅行用圧縮袋",
    "urban-lifestyle-seoul-schools": "収納ボックス",
    "busan-student-life": "収納ボックス",
    # digital / arrival
    "arrival": "海外変換プラグ",
    "mobile": "モバイルバッテリー",
    "sim-esim-korea": "モバイルバッテリー",
    "korean-study-apps": "タブレット スタンド",
    "emergency-contacts-korea": "常備薬",
    "t-money-guide": "交通系ICカード ケース",
    "climate-card-seoul": "モバイルバッテリー",
    # kitchen / budget
    "convenience-store-korea": "電気ケトル",
    "korean-food-student-budget": "フライパン",
    "korean-delivery-apps": "弁当箱",
    "cost": "電気ケトル",
    "monthly-budget-seoul": "水筒",
    "monthly-budget-busan": "水筒",
    # weather
    "weather-korea": "折りたたみ傘",
    "winter-korea-student": "ダウンジャケット",
    "bicycle-korea": "自転車 鍵",
    "culture-shock-korea": "常備薬",
    # study books
    "topik": "TOPIK 問題集",
    "topik-study-plan": "TOPIK 問題集",
    "topik-vs-klat": "TOPIK 問題集",
}


def normalize_guide_slug(slug: str) -> str:
    s = (slug or "").strip().lower()
    if s.endswith("_ja"):
        s = s[: -len("_ja")]
    if s.endswith("_kr") or s.endswith("_ko"):
        s = s[:-3]
    if s.startswith("guide_"):
        s = s[len("guide_") :]
    return s


def amazon_search_url(keyword: str) -> str:
    return (
        "https://www.amazon.co.jp/s?k="
        + quote_plus(keyword)
        + "&tag="
        + quote_plus(AMAZON_TAG)
    )


def klook_url(*, lang: str = "en") -> str:
    if (lang or "en").lower().startswith("ja"):
        return KLOOK_URL_JA
    return KLOOK_URL_EN


def _hidden() -> dict[str, Any]:
    return {
        "show_affiliate": False,
        "show_amazon": False,
        "show_klook": False,
    }


def affiliate_context(
    slug: str = "",
    *,
    lang: str = "en",
    item_type: str = "guide",
) -> dict[str, Any]:
    """Amazon.jp + Klook. School/university → Amazon + Klook."""
    kind_raw = (item_type or "guide").strip().lower()
    key = normalize_guide_slug(slug)
    is_ja = (lang or "en").lower().startswith("ja")

    if kind_raw in ("school", "university"):
        amazon_kw = (
            SCHOOL_BOOK_KEYWORD if kind_raw == "school" else UNIVERSITY_BOOK_KEYWORD
        )
        show_amazon = True
        show_klook = True
    else:
        amazon_kw = GUIDE_AMAZON_MAP.get(key)
        show_amazon = bool(amazon_kw)
        show_klook = key in GUIDE_KLOOK_SLUGS

    if not show_amazon and not show_klook:
        return _hidden()

    if is_ja:
        parts = []
        if show_amazon:
            parts.append("Amazon")
        if show_klook:
            parts.append("Klook")
        if kind_raw in ("school", "university"):
            title = "留学の準備 — " + " / ".join(parts) if parts else "関連リンク"
            bits = []
            if show_amazon:
                bits.append(f"「Amazon.co.jp」で「{amazon_kw}」を検索")
            if show_klook:
                bits.append("eSIM・空港アクセスは Klook")
            desc = "、".join(bits) + "できます。" if bits else ""
        else:
            title = "留学・生活の準備 — " + " / ".join(parts) if parts else "関連リンク"
            bits = []
            if show_amazon:
                bits.append(f"「Amazon.co.jp」で「{amazon_kw}」を検索")
            if show_klook:
                bits.append("eSIM・空港アクセスは Klook")
            desc = "、".join(bits) + "できます。" if bits else ""
        amazon_label = f"Amazonで「{amazon_kw}」を検索 ↗" if amazon_kw else ""
        klook_label = "Klookで eSIM・空港アクセスを見る ↗"
        note = "アフィリエイトリンク · 新しいタブで開きます"
    else:
        parts = []
        if show_amazon:
            parts.append("Amazon")
        if show_klook:
            parts.append("Klook")
        if kind_raw in ("school", "university"):
            title = "Prep for Korea — " + " / ".join(parts) if parts else "Related links"
            bits = []
            if show_amazon:
                bits.append(f"Amazon.co.jp search for 「{amazon_kw}」")
            if show_klook:
                bits.append("Klook for eSIM & airport transfer")
            desc = ". ".join(bits) + "." if bits else ""
        else:
            title = "Prep for Korea — " + " / ".join(parts) if parts else "Related links"
            bits = []
            if show_amazon:
                bits.append(f"Amazon.co.jp search for 「{amazon_kw}」")
            if show_klook:
                bits.append("Klook for eSIM & airport transfer")
            desc = ". ".join(bits) + "." if bits else ""
        amazon_label = f"Search 「{amazon_kw}」 on Amazon Japan ↗" if amazon_kw else ""
        klook_label = "eSIM & airport transfer on Klook ↗"
        note = "Affiliate links · opens in a new tab"

    return {
        "show_affiliate": True,
        "show_amazon": show_amazon,
        "show_klook": show_klook,
        "affiliate_title": title,
        "affiliate_desc": desc,
        "affiliate_note": note,
        "amazon_search_url": amazon_search_url(amazon_kw) if amazon_kw else "",
        "amazon_button_label": amazon_label,
        "amazon_keyword": amazon_kw or "",
        "affiliate_category": "",
        "klook_url": klook_url(lang=lang) if show_klook else "",
        "klook_button_label": klook_label if show_klook else "",
    }
