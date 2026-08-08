"""Affiliate CTAs for KR Campus.

- Amazon.co.jp search: EN + JA (Associates tag)
- Rakuten Travel: 韓国 ホテル (school/univ + mapped pages)
- Klook Travelpayouts links: arrival / eSIM / packing guides + school/university
"""

from __future__ import annotations

import os
from typing import Any, Literal
from urllib.parse import quote, quote_plus

AMAZON_TAG = os.getenv("AMAZON_ASSOCIATE_TAG", "starful06-22")
RAKUTEN_TRAVEL_HGC = os.getenv(
    "RAKUTEN_TRAVEL_HGC", "55b9427b.a63c2df8.55b9427c.3a0d270c"
)
_RAKUTEN_UT = "eyJwYWdlIjoidXJsIiwidHlwZSI6InRleHQiLCJjb2wiOjF9"
RAKUTEN_TRAVEL_KEYWORD = "韓国 ホテル"

KlookIntent = Literal["esim", "airport", "fallback"]

# Travelpayouts krcampus Klook short links (also reused by krcare).
KLOOK_URLS: dict[str, str] = {
    "esim_en": "https://klook.tpo.mx/ei41OcMK",
    "esim_ja": "https://klook.tpo.mx/sVI2GsrC",
    "airport_en": "https://klook.tpo.mx/BSwK5MnY",
    "airport_ja": "https://klook.tpo.mx/N6y8DtrW",
    "fallback_en": "https://klook.tpo.mx/IHDxaMD6",
    # No dedicated JA fallback — reuse esim_ja.
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

# Guides that show a Klook Travelpayouts CTA (eSIM / arrival prep).
GUIDE_KLOOK_SLUGS: frozenset[str] = (
    GUIDE_KLOOK_ESIM | GUIDE_KLOOK_AIRPORT | GUIDE_KLOOK_FALLBACK
)

# slug → Amazon.co.jp search keyword (JP store — pre-departure buys)
GUIDE_AMAZON_MAP: dict[str, str] = {
    # housing / packing
    "dorm-application": "寝具セット シングル",
    "goshiwon-guide": "寝具セット シングル",
    "housing": "衣類圧縮袋",
    "packing-korea": "スーツケース キャリーケース",
    "seoul-neighborhoods": "旅行用圧縮袋",
    "urban-lifestyle-seoul-schools": "衣類圧縮袋",
    "busan-student-life": "衣類圧縮袋",
    # digital / arrival
    "arrival": "海外変換プラグ 韓国",
    "mobile": "モバイルバッテリー 大容量",
    "sim-esim-korea": "モバイルバッテリー 大容量",
    "korean-study-apps": "タブレット スタンド",
    "emergency-contacts-korea": "常備薬 セット",
    "t-money-guide": "ネックポーチ パスポート",
    "climate-card-seoul": "折りたたみ傘",
    # kitchen / budget
    "convenience-store-korea": "電気ケトル",
    "korean-food-student-budget": "フライパン セット",
    "korean-delivery-apps": "箸 スプーン セット",
    "cost": "家計簿 ノート",
    "monthly-budget-seoul": "水筒 ステンレス",
    "monthly-budget-busan": "水筒 ステンレス",
    # weather
    "weather-korea": "折りたたみ傘",
    "winter-korea-student": "ダウンジャケット メンズ",
    "bicycle-korea": "自転車 鍵",
    "culture-shock-korea": "韓国語 会話 本",
    # study books
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


def rakuten_travel_url(keyword: str = RAKUTEN_TRAVEL_KEYWORD) -> str:
    raw = (
        "https://kw.travel.rakuten.co.jp/keyword/Search.do?"
        + "f_key="
        + quote_plus(keyword)
    )
    pc = quote(raw, safe="")
    return (
        f"https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_TRAVEL_HGC}/"
        f"?pc={pc}&link_type=text&ut={_RAKUTEN_UT}"
    )


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
    }


def affiliate_context(
    slug: str = "",
    *,
    lang: str = "en",
    item_type: str = "guide",
) -> dict[str, Any]:
    """Amazon.jp + Rakuten Travel + Klook. School/university → all three."""
    kind_raw = (item_type or "guide").strip().lower()
    key = normalize_guide_slug(slug)
    is_ja = (lang or "en").lower().startswith("ja")

    if kind_raw in ("school", "university"):
        amazon_kw = (
            SCHOOL_BOOK_KEYWORD if kind_raw == "school" else UNIVERSITY_BOOK_KEYWORD
        )
        show_amazon = True
        show_klook = True
        show_rakuten_travel = True
    else:
        amazon_kw = GUIDE_AMAZON_MAP.get(key)
        show_amazon = bool(amazon_kw)
        show_klook = key in GUIDE_KLOOK_SLUGS
        show_rakuten_travel = show_amazon or show_klook

    if not show_amazon and not show_klook and not show_rakuten_travel:
        return _hidden()

    if is_ja:
        parts = []
        if show_amazon:
            parts.append("Amazon")
        if show_rakuten_travel:
            parts.append("楽天トラベル")
        if show_klook:
            parts.append("Klook")
        if kind_raw in ("school", "university"):
            title = "留学の準備 — " + " / ".join(parts) if parts else "関連リンク"
            bits = []
            if show_amazon:
                bits.append(f"「Amazon.co.jp」で「{amazon_kw}」を検索")
            if show_rakuten_travel:
                bits.append("宿泊は楽天トラベルで「韓国 ホテル」")
            if show_klook:
                bits.append("eSIM・空港アクセスは Klook")
            desc = "、".join(bits) + "できます。" if bits else ""
        else:
            title = "留学・生活の準備 — " + " / ".join(parts) if parts else "関連リンク"
            bits = []
            if show_amazon:
                bits.append(f"「Amazon.co.jp」で「{amazon_kw}」を検索")
            if show_rakuten_travel:
                bits.append("宿泊は楽天トラベルで「韓国 ホテル」")
            if show_klook:
                bits.append("eSIM・空港アクセスは Klook")
            desc = "、".join(bits) + "できます。" if bits else ""
        amazon_label = f"Amazonで「{amazon_kw}」を検索 ↗" if amazon_kw else ""
        rakuten_travel_label = "楽天トラベルで韓国ホテルを検索 ↗"
        klook_label = "Klookで eSIM・空港アクセスを見る ↗"
        note = "アフィリエイトリンク · 新しいタブで開きます"
    else:
        parts = []
        if show_amazon:
            parts.append("Amazon")
        if show_rakuten_travel:
            parts.append("Rakuten Travel")
        if show_klook:
            parts.append("Klook")
        title = "Prep for Korea — " + " / ".join(parts) if parts else "Related links"
        bits = []
        if show_amazon:
            bits.append(f"Amazon.co.jp search for 「{amazon_kw}」")
        if show_rakuten_travel:
            bits.append("Rakuten Travel for Korea hotels")
        if show_klook:
            bits.append("Klook for eSIM & airport transfer")
        desc = ". ".join(bits) + "." if bits else ""
        amazon_label = f"Search 「{amazon_kw}」 on Amazon Japan ↗" if amazon_kw else ""
        rakuten_travel_label = "Search Korea hotels on Rakuten Travel ↗"
        klook_label = "eSIM & airport transfer on Klook ↗"
        note = "Affiliate links · opens in a new tab"

    return {
        "show_affiliate": True,
        "show_amazon": show_amazon,
        "show_klook": show_klook,
        "show_rakuten_travel": show_rakuten_travel,
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
        "klook_url": (
            klook_url(lang=lang, slug=slug, item_type=kind_raw) if show_klook else ""
        ),
        "klook_button_label": klook_label if show_klook else "",
    }
