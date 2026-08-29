"""Affiliate CTAs for KR Campus — Rakuten Travel/eSIM (Klook removed)."""

from __future__ import annotations

from typing import Any

RAKUTEN_KOREA_TRAVEL_URL = "https://a.r10.to/hPhGZl"
RAKUTEN_KOREA_ESIM_URL = "https://a.r10.to/h9O1Fq"

GUIDE_PREP_ESIM: frozenset[str] = frozenset({"sim-esim-korea", "mobile"})

GUIDE_PREP_SLUGS: frozenset[str] = frozenset(
    {
        "dorm-application",
        "goshiwon-guide",
        "housing",
        "packing-korea",
        "seoul-neighborhoods",
        "urban-lifestyle-seoul-schools",
        "busan-student-life",
        "arrival",
        "mobile",
        "sim-esim-korea",
        "korean-study-apps",
        "emergency-contacts-korea",
        "t-money-guide",
        "climate-card-seoul",
        "convenience-store-korea",
        "korean-food-student-budget",
        "korean-delivery-apps",
        "cost",
        "monthly-budget-seoul",
        "monthly-budget-busan",
        "weather-korea",
        "winter-korea-student",
        "bicycle-korea",
        "culture-shock-korea",
        "topik",
        "topik-study-plan",
        "topik-vs-klat",
    }
)


def normalize_guide_slug(slug: str) -> str:
    s = (slug or "").strip().lower()
    if s.endswith("_ja"):
        s = s[: -len("_ja")]
    if s.endswith("_kr") or s.endswith("_ko"):
        s = s[:-3]
    if s.startswith("guide_"):
        s = s[len("guide_") :]
    return s


def rakuten_travel_url() -> str:
    return RAKUTEN_KOREA_TRAVEL_URL


def rakuten_esim_url() -> str:
    return RAKUTEN_KOREA_ESIM_URL


def _hidden() -> dict[str, Any]:
    return {
        "show_affiliate": False,
        "show_rakuten_travel": False,
        "show_rakuten_esim": False,
    }


def affiliate_context(
    slug: str = "",
    *,
    lang: str = "en",
    item_type: str = "guide",
) -> dict[str, Any]:
    """Rakuten Travel/eSIM on prep guides and school pages."""
    kind_raw = (item_type or "guide").strip().lower()
    key = normalize_guide_slug(slug)
    is_ja = (lang or "en").lower().startswith("ja")

    if kind_raw in ("school", "university"):
        show_rakuten_travel = True
        show_rakuten_esim = True
    else:
        in_prep = key in GUIDE_PREP_SLUGS
        show_rakuten_travel = in_prep
        show_rakuten_esim = key in GUIDE_PREP_ESIM

    if not show_rakuten_travel and not show_rakuten_esim:
        return _hidden()

    if is_ja:
        parts = []
        if show_rakuten_travel:
            parts.append("楽天トラベル")
        if show_rakuten_esim:
            parts.append("韓国eSIM")
        title = (
            ("留学の準備 — " if kind_raw in ("school", "university") else "留学・生活の準備 — ")
            + " / ".join(parts)
        )
        bits = []
        if show_rakuten_travel:
            bits.append("宿泊・韓国旅行は楽天")
        if show_rakuten_esim:
            bits.append("韓国eSIMは楽天")
        desc = "、".join(bits) + "できます。" if bits else ""
        travel_label = "楽天で韓国旅行を見る ↗"
        esim_label = "楽天で韓国eSIMを見る ↗"
        note = "アフィリエイトリンク · 新しいタブで開きます"
    else:
        parts = []
        if show_rakuten_travel:
            parts.append("Rakuten Travel")
        if show_rakuten_esim:
            parts.append("Korea eSIM")
        title = "Prep for Korea — " + " / ".join(parts) if parts else "Related links"
        bits = []
        if show_rakuten_travel:
            bits.append("Rakuten for Korea travel")
        if show_rakuten_esim:
            bits.append("Rakuten for Korea eSIM")
        desc = ". ".join(bits) + "." if bits else ""
        travel_label = "Korea travel on Rakuten ↗"
        esim_label = "Korea eSIM on Rakuten ↗"
        note = "Affiliate links · opens in new tab"

    return {
        "show_affiliate": True,
        "show_rakuten_travel": show_rakuten_travel,
        "show_rakuten_esim": show_rakuten_esim,
        "affiliate_title": title,
        "affiliate_desc": desc,
        "affiliate_note": note,
        "affiliate_category": key if key in GUIDE_PREP_SLUGS else "",
        "rakuten_travel_url": rakuten_travel_url() if show_rakuten_travel else "",
        "rakuten_travel_button_label": (
            travel_label if show_rakuten_travel else ""
        ),
        "rakuten_esim_url": rakuten_esim_url() if show_rakuten_esim else "",
        "rakuten_esim_button_label": esim_label if show_rakuten_esim else "",
    }
