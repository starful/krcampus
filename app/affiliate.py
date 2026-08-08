"""Affiliate CTAs for KR Campus.

- Amazon.co.jp search: EN + JA (Associates tag)
- Rakuten Travel short link (韓国旅行) + Rakuten Korea eSIM
- Klook: airport / fallback only (eSIM intent uses Rakuten)
"""

from __future__ import annotations

import os
from typing import Any, Literal
from urllib.parse import quote_plus

AMAZON_TAG = os.getenv("AMAZON_ASSOCIATE_TAG", "starful06-22")

RAKUTEN_KOREA_TRAVEL_URL = "https://a.r10.to/hPhGZl"
RAKUTEN_KOREA_ESIM_URL = "https://a.r10.to/h9O1Fq"

KlookIntent = Literal["esim", "airport", "fallback"]

# Travelpayouts krcampus Klook short links (airport / fallback; eSIM → Rakuten).
KLOOK_URLS: dict[str, str] = {
    "esim_en": "https://klook.tpo.mx/ei41OcMK",
    "esim_ja": "https://klook.tpo.mx/sVI2GsrC",
    "airport_en": "https://klook.tpo.mx/BSwK5MnY",
    "airport_ja": "https://klook.tpo.mx/N6y8DtrW",
    "fallback_en": "https://klook.tpo.mx/IHDxaMD6",
    "fallback_ja": "https://klook.tpo.mx/sVI2GsrC",
}

KLOOK_URL_DEFAULT = KLOOK_URLS["fallback_en"]
KLOOK_URL_EN = os.getenv("KLOOK_URL_EN", KLOOK_URL_DEFAULT)
KLOOK_URL_JA = os.getenv("KLOOK_URL_JA", KLOOK_URLS["esim_ja"])

SCHOOL_BOOK_KEYWORD = "TOPIK II 問題集"
UNIVERSITY_BOOK_KEYWORD = "TOPIK II 問題集"

GUIDE_KLOOK_ESIM: frozenset[str] = frozenset({"sim-esim-korea", "mobile"})
GUIDE_KLOOK_AIRPORT: frozenset[str] = frozenset({"arrival"})
GUIDE_KLOOK_FALLBACK: frozenset[str] = frozenset({"packing-korea"})

GUIDE_KLOOK_SLUGS: frozenset[str] = (
    GUIDE_KLOOK_ESIM | GUIDE_KLOOK_AIRPORT | GUIDE_KLOOK_FALLBACK
)

GUIDE_AMAZON_MAP: dict[str, str] = {
    "dorm-application": "寝具セット シングル",
    "goshiwon-guide": "寝具セット シングル",
    "housing": "衣類圧縮袋",
    "packing-korea": "スーツケース キャリーケース",
    "seoul-neighborhoods": "旅行用圧縮袋",
    "urban-lifestyle-seoul-schools": "衣類圧縮袋",
    "busan-student-life": "衣類圧縮袋",
    "arrival": "海外変換プラグ 韓国",
    "mobile": "モバイルバッテリー 大容量",
    "sim-esim-korea": "モバイルバッテリー 大容量",
    "korean-study-apps": "タブレット スタンド",
    "emergency-contacts-korea": "常備薬 セット",
    "t-money-guide": "ネックポーチ パスポート",
    "climate-card-seoul": "折りたたみ傘",
    "convenience-store-korea": "電気ケトル",
    "korean-food-student-budget": "フライパン セット",
    "korean-delivery-apps": "箸 スプーン セット",
    "cost": "家計簿 ノート",
    "monthly-budget-seoul": "水筒 ステンレス",
    "monthly-budget-busan": "水筒 ステンレス",
    "weather-korea": "折りたたみ傘",
    "winter-korea-student": "ダウンジャケット メンズ",
    "bicycle-korea": "自転車 鍵",
    "culture-shock-korea": "韓国語 会話 本",
    "topik": "TOPIK II 問題集",
    "topik-study-plan": "TOPIK II 問題集",
    "topik-vs-klat": "TOPIK II 問題集",
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


def rakuten_travel_url() -> str:
    return RAKUTEN_KOREA_TRAVEL_URL


def rakuten_esim_url() -> str:
    return RAKUTEN_KOREA_ESIM_URL


def resolve_klook_intent(
    slug: str = "",
    *,
    item_type: str = "guide",
) -> KlookIntent:
    kind = (item_type or "guide").strip().lower()
    if kind in ("school", "university"):
        return "esim"
    key = normalize_guide_slug(slug)
    if key in GUIDE_KLOOK_AIRPORT:
        return "airport"
    if key in GUIDE_KLOOK_ESIM:
        return "esim"
    return "fallback"


def klook_url(*, lang: str = "en", slug: str = "", item_type: str = "guide") -> str:
    intent = resolve_klook_intent(slug, item_type=item_type)
    is_ja = (lang or "en").lower().startswith("ja")
    suffix = "ja" if is_ja else "en"
    key = f"{intent}_{suffix}"
    if key in KLOOK_URLS:
        return KLOOK_URLS[key]
    return KLOOK_URL_JA if is_ja else KLOOK_URL_EN


def _hidden() -> dict[str, Any]:
    return {
        "show_affiliate": False,
        "show_amazon": False,
        "show_klook": False,
        "show_rakuten_travel": False,
        "show_rakuten_esim": False,
    }


def affiliate_context(
    slug: str = "",
    *,
    lang: str = "en",
    item_type: str = "guide",
) -> dict[str, Any]:
    """Amazon.jp + Rakuten Travel/eSIM + Klook (airport/fallback)."""
    kind_raw = (item_type or "guide").strip().lower()
    key = normalize_guide_slug(slug)
    is_ja = (lang or "en").lower().startswith("ja")
    intent = resolve_klook_intent(slug, item_type=kind_raw)

    if kind_raw in ("school", "university"):
        amazon_kw = (
            SCHOOL_BOOK_KEYWORD if kind_raw == "school" else UNIVERSITY_BOOK_KEYWORD
        )
        show_amazon = True
        show_rakuten_travel = True
        show_rakuten_esim = True
        show_klook = False
    else:
        amazon_kw = GUIDE_AMAZON_MAP.get(key)
        show_amazon = bool(amazon_kw)
        show_rakuten_travel = show_amazon or key in GUIDE_KLOOK_SLUGS
        show_rakuten_esim = intent == "esim" or key in GUIDE_KLOOK_ESIM
        # Keep Klook only for airport / generic fallback — not eSIM.
        show_klook = intent in ("airport", "fallback") and key in GUIDE_KLOOK_SLUGS

    if not any((show_amazon, show_klook, show_rakuten_travel, show_rakuten_esim)):
        return _hidden()

    if is_ja:
        parts = []
        if show_amazon:
            parts.append("Amazon")
        if show_rakuten_travel:
            parts.append("楽天トラベル")
        if show_rakuten_esim:
            parts.append("韓国eSIM")
        if show_klook:
            parts.append("Klook")
        title = (
            ("留学の準備 — " if kind_raw in ("school", "university") else "留学・生活の準備 — ")
            + " / ".join(parts)
            if parts
            else "関連リンク"
        )
        bits = []
        if show_amazon:
            bits.append(f"「Amazon.co.jp」で「{amazon_kw}」を検索")
        if show_rakuten_travel:
            bits.append("宿泊・韓国旅行は楽天")
        if show_rakuten_esim:
            bits.append("韓国eSIMは楽天")
        if show_klook:
            bits.append("空港アクセスは Klook")
        desc = "、".join(bits) + "できます。" if bits else ""
        amazon_label = f"Amazonで「{amazon_kw}」を検索 ↗" if amazon_kw else ""
        rakuten_travel_label = "楽天で韓国旅行を見る ↗"
        rakuten_esim_label = "楽天で韓国eSIMを見る ↗"
        klook_label = "Klookで空港アクセスを見る ↗"
        note = "アフィリエイトリンク · 新しいタブで開きます"
    else:
        parts = []
        if show_amazon:
            parts.append("Amazon")
        if show_rakuten_travel:
            parts.append("Rakuten Travel")
        if show_rakuten_esim:
            parts.append("Korea eSIM")
        if show_klook:
            parts.append("Klook")
        title = "Prep for Korea — " + " / ".join(parts) if parts else "Related links"
        bits = []
        if show_amazon:
            bits.append(f"Amazon.co.jp search for 「{amazon_kw}」")
        if show_rakuten_travel:
            bits.append("Rakuten for Korea travel")
        if show_rakuten_esim:
            bits.append("Rakuten for Korea eSIM")
        if show_klook:
            bits.append("Klook for airport transfer")
        desc = ". ".join(bits) + "." if bits else ""
        amazon_label = f"Search 「{amazon_kw}」 on Amazon Japan ↗" if amazon_kw else ""
        rakuten_travel_label = "Korea travel on Rakuten ↗"
        rakuten_esim_label = "Korea eSIM on Rakuten ↗"
        klook_label = "Airport transfers on Klook ↗"
        note = "Affiliate links · opens in a new tab"

    return {
        "show_affiliate": True,
        "show_amazon": show_amazon,
        "show_klook": show_klook,
        "show_rakuten_travel": show_rakuten_travel,
        "show_rakuten_esim": show_rakuten_esim,
        "affiliate_title": title,
        "affiliate_desc": desc,
        "affiliate_note": note,
        "amazon_search_url": amazon_search_url(amazon_kw) if amazon_kw else "",
        "amazon_button_label": amazon_label,
        "amazon_keyword": amazon_kw or "",
        "affiliate_category": "",
        "rakuten_travel_url": rakuten_travel_url() if show_rakuten_travel else "",
        "rakuten_travel_button_label": (
            rakuten_travel_label if show_rakuten_travel else ""
        ),
        "rakuten_esim_url": rakuten_esim_url() if show_rakuten_esim else "",
        "rakuten_esim_button_label": rakuten_esim_label if show_rakuten_esim else "",
        "klook_url": (
            klook_url(lang=lang, slug=slug, item_type=kind_raw) if show_klook else ""
        ),
        "klook_button_label": klook_label if show_klook else "",
    }
