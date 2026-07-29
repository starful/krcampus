"""Affiliate CTAs for KR Campus.

- Amazon.co.jp search: EN + JA (Associates tag)
- Coupang category banners: EN + JA lifestyle guides
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

DISCLOSURE_KO = (
    "이 포스팅은 쿠팡 파트너스 활동의 일환으로, "
    "이에 따른 일정액의 수수료를 제공받습니다."
)

# Coupang category banners (Partners issuance order)
COUPANG_CATEGORIES: dict[str, dict[str, Any]] = {
    "home_interior": {
        "label_ko": "홈인테리어",
        "label_en": "Home & Interior",
        "label_ja": "ホームインテリア",
        "desktop_href": "https://link.coupang.com/a/fnGue9xDuC",
        "desktop_img": (
            "https://ads-partners.coupang.com/banners/1006707"
            "?trackingCode=AF2731529&subId=&traceId=V0-301-2f679fc6bd8f2e58-I1006707"
            "&w=728&h=90"
        ),
        "mobile_href": "https://link.coupang.com/a/fnGv29k0aW",
        "mobile_img": (
            "https://ads-partners.coupang.com/banners/1006708"
            "?trackingCode=AF2731529&subId=&traceId=V0-301-2f679fc6bd8f2e58-I1006708"
            "&w=320&h=100"
        ),
    },
    "appliances_digital": {
        "label_ko": "가전/디지털",
        "label_en": "Appliances & Digital",
        "label_ja": "家電・デジタル",
        "desktop_href": "https://link.coupang.com/a/fnGxMqeYIC",
        "desktop_img": (
            "https://ads-partners.coupang.com/banners/1006709"
            "?trackingCode=AF2731529&subId=&traceId=V0-301-5f9bd61900e673c0-I1006709"
            "&w=728&h=90"
        ),
        "mobile_href": "https://link.coupang.com/a/fnGykZbB0u",
        "mobile_img": (
            "https://ads-partners.coupang.com/banners/1006710"
            "?trackingCode=AF2731529&subId=&traceId=V0-301-5f9bd61900e673c0-I1006710"
            "&w=320&h=100"
        ),
    },
    "kitchen": {
        "label_ko": "주방용품",
        "label_en": "Kitchen",
        "label_ja": "キッチン用品",
        "desktop_href": "https://link.coupang.com/a/fnGy7ggYfY",
        "desktop_img": (
            "https://ads-partners.coupang.com/banners/1006711"
            "?trackingCode=AF2731529&subId=&traceId=V0-301-2b8ef06377ec8f50-I1006711"
            "&w=728&h=90"
        ),
        "mobile_href": "https://link.coupang.com/a/fnGzFpn6HY",
        "mobile_img": (
            "https://ads-partners.coupang.com/banners/1006712"
            "?trackingCode=AF2731529&subId=&traceId=V0-301-2b8ef06377ec8f50-I1006712"
            "&w=320&h=100"
        ),
    },
    "fashion": {
        "label_ko": "패션",
        "label_en": "Fashion",
        "label_ja": "ファッション",
        "desktop_href": "https://link.coupang.com/a/fnGAohCHvw",
        "desktop_img": (
            "https://ads-partners.coupang.com/banners/1006713"
            "?trackingCode=AF2731529&subId=&traceId=V0-301-5a8c79a76485eb21-I1006713"
            "&w=728&h=90"
        ),
        "mobile_href": "https://link.coupang.com/a/fnGARfEjEy",
        "mobile_img": (
            "https://ads-partners.coupang.com/banners/1006715"
            "?trackingCode=AF2731529&subId=&traceId=V0-301-5a8c79a76485eb21-I1006715"
            "&w=320&h=100"
        ),
    },
}

# Lifestyle guides → Coupang category (EN + JA)
GUIDE_COUPANG_MAP: dict[str, str] = {
    "dorm-application": "home_interior",
    "goshiwon-guide": "home_interior",
    "housing": "home_interior",
    "packing-korea": "home_interior",
    "seoul-neighborhoods": "home_interior",
    "urban-lifestyle-seoul-schools": "home_interior",
    "busan-student-life": "home_interior",
    "arrival": "appliances_digital",
    "mobile": "appliances_digital",
    "sim-esim-korea": "appliances_digital",
    "korean-study-apps": "appliances_digital",
    "emergency-contacts-korea": "appliances_digital",
    "t-money-guide": "appliances_digital",
    "climate-card-seoul": "appliances_digital",
    "convenience-store-korea": "kitchen",
    "korean-food-student-budget": "kitchen",
    "korean-delivery-apps": "kitchen",
    "cost": "kitchen",
    "monthly-budget-seoul": "kitchen",
    "monthly-budget-busan": "kitchen",
    "weather-korea": "fashion",
    "winter-korea-student": "fashion",
    "bicycle-korea": "fashion",
    "culture-shock-korea": "fashion",
}

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
    # study books (Amazon only, no Coupang)
    "topik": "TOPIK 問題集",
    "topik-study-plan": "TOPIK 問題集",
    "topik-vs-klat": "TOPIK 問題集",
}

# Back-compat aliases for tests / older imports
CATEGORIES = COUPANG_CATEGORIES
GUIDE_AFFILIATE_MAP = GUIDE_COUPANG_MAP


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
        "show_coupang": False,
        "show_klook": False,
    }


def affiliate_context(
    slug: str = "",
    *,
    lang: str = "en",
    item_type: str = "guide",
) -> dict[str, Any]:
    """Amazon.jp + Coupang (guides) + Klook. School/university → Amazon + Klook."""
    kind_raw = (item_type or "guide").strip().lower()
    key = normalize_guide_slug(slug)
    is_ja = (lang or "en").lower().startswith("ja")

    if kind_raw in ("school", "university"):
        amazon_kw = (
            SCHOOL_BOOK_KEYWORD if kind_raw == "school" else UNIVERSITY_BOOK_KEYWORD
        )
        show_amazon = True
        show_coupang = False
        show_klook = True
        coupang_cat_id = None
    else:
        amazon_kw = GUIDE_AMAZON_MAP.get(key)
        show_amazon = bool(amazon_kw)
        coupang_cat_id = GUIDE_COUPANG_MAP.get(key)
        if coupang_cat_id and coupang_cat_id not in COUPANG_CATEGORIES:
            coupang_cat_id = None
        show_coupang = bool(coupang_cat_id)
        show_klook = key in GUIDE_KLOOK_SLUGS

    if not show_amazon and not show_coupang and not show_klook:
        return _hidden()

    cat_label = ""
    if show_coupang and coupang_cat_id:
        cat = COUPANG_CATEGORIES[coupang_cat_id]
        cat_label = cat["label_ja"] if is_ja else cat["label_en"]

    if is_ja:
        parts = []
        if show_amazon:
            parts.append("Amazon")
        if show_coupang:
            parts.append("Coupang")
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
            if show_coupang:
                bits.append("到着後用に Coupang カテゴリをチェック")
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
        if show_coupang:
            parts.append("Coupang")
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
            if show_coupang:
                bits.append(f"Coupang «{cat_label}» for after you arrive")
            if show_klook:
                bits.append("Klook for eSIM & airport transfer")
            desc = ". ".join(bits) + "." if bits else ""
        amazon_label = f"Search 「{amazon_kw}」 on Amazon Japan ↗" if amazon_kw else ""
        klook_label = "eSIM & airport transfer on Klook ↗"
        note = "Affiliate links · opens in a new tab"

    out: dict[str, Any] = {
        "show_affiliate": True,
        "show_amazon": show_amazon,
        "show_coupang": show_coupang,
        "show_klook": show_klook,
        "affiliate_title": title,
        "affiliate_desc": desc,
        "affiliate_note": note,
        "amazon_search_url": amazon_search_url(amazon_kw) if amazon_kw else "",
        "amazon_button_label": amazon_label,
        "amazon_keyword": amazon_kw or "",
        "affiliate_disclosure": DISCLOSURE_KO if show_coupang else "",
        "affiliate_category": coupang_cat_id or "",
        "affiliate_category_label": cat_label,
        "coupang_desktop_href": "",
        "coupang_desktop_img": "",
        "coupang_mobile_href": "",
        "coupang_mobile_img": "",
        "klook_url": klook_url(lang=lang) if show_klook else "",
        "klook_button_label": klook_label if show_klook else "",
    }

    if show_coupang and coupang_cat_id:
        cat = COUPANG_CATEGORIES[coupang_cat_id]
        out["coupang_desktop_href"] = cat["desktop_href"]
        out["coupang_desktop_img"] = cat["desktop_img"]
        out["coupang_mobile_href"] = cat["mobile_href"]
        out["coupang_mobile_img"] = cat["mobile_img"]

    return out
