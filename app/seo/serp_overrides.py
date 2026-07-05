"""SERP title/description overrides for low-CTR guides."""

_GUIDE_SERP_OVERRIDES: dict[tuple[str, str], dict[str, str]] = {
    ("housing", "en"): {
        "title": "Student Housing in Korea: Dorm, Goshiwon vs Apartment (2026)",
        "description": (
            "Compare dormitories, goshiwon, and one-room apartments for international students in Korea — "
            "costs, contracts, and what to check before signing."
        ),
    },
    ("housing", "ja"): {
        "title": "韓国留学の住居比較：寮・ゴシウォン・ワンルーム (2026)",
        "description": (
            "留学生向けに寮・ゴシウォン・ワンルームの初期費用・契約・注意点を比較します。"
        ),
    },
    ("topik-study-plan", "en"): {
        "title": "TOPIK Study Plan: Levels, Timeline & Resources for Korea (2026)",
        "description": (
            "Build a practical TOPIK prep schedule with level targets, study order, and resources "
            "aligned to language school and university admissions in Korea."
        ),
    },
    ("topik-study-plan", "ja"): {
        "title": "TOPIK学習計画：レベル別スケジュールと対策 (2026)",
        "description": (
            "韓国留学・大学進学に合わせたTOPIK目標レベルと学習順序、おすすめリソースを整理します。"
        ),
    },
}


def guide_lang_key(lang: str) -> str:
    return "ja" if lang == "ja" else "en"


def apply_guide_serp_overrides(slug: str, lang: str, item: dict) -> tuple[str, str]:
    lk = guide_lang_key(lang)
    ov = _GUIDE_SERP_OVERRIDES.get((slug, lk))
    if not ov:
        return item.get("title", "Study in Korea Guide"), item.get("description", "")
    return ov.get("title", item.get("title", "")), ov.get("description", item.get("description", ""))
