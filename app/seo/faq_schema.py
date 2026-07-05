import json

from app.seo.serp_overrides import guide_lang_key

_GUIDE_FAQ: dict[tuple[str, str], list[tuple[str, str]]] = {
    ("housing", "en"): [
        (
            "What are the main housing options for international students in Korea?",
            "Most students choose between university dormitories (gisuksa), goshiwon micro-rooms, or private one-room apartments. "
            "Each differs in upfront costs, privacy, and commute time.",
        ),
        (
            "Which housing type usually has the lowest move-in cost?",
            "University dorms often have lower upfront costs than private apartments, but availability and curfew rules vary by school.",
        ),
        (
            "What should I check before signing a rental contract in Korea?",
            "Review deposit (jeonse/wolse), maintenance fees, contract length, and whether your school or a licensed agent assists with registration.",
        ),
    ],
    ("housing", "ja"): [
        (
            "韓国留学の住居選択肢は？",
            "大学寮（ギスクサ）、ゴシウォン、ワンルームが代表的で、初期費用・プライバシー・通学時間が異なります。",
        ),
        (
            "初期費用を抑えるなら？",
            "大学寮はワンルームより初期費用が低いことが多いですが、空室と門限ルールを先に確認してください。",
        ),
        (
            "契約前に確認することは？",
            "保証金・管理費・契約期間・外国人登録の手続き支援の有無を書面で確認しましょう。",
        ),
    ],
    ("topik-study-plan", "en"): [
        (
            "How long does it take to reach TOPIK Level 3 or 4?",
            "Timeline depends on your starting level and study hours; many intensive programs target one level gain per 3–6 months of full-time study.",
        ),
        (
            "Which TOPIK level do Korean universities usually require?",
            "Requirements vary by program; verify each university's latest admissions guide rather than assuming one national standard.",
        ),
    ],
}


def guide_faq_json_ld(slug: str, lang: str) -> str | None:
    rows = _GUIDE_FAQ.get((slug, guide_lang_key(lang)))
    if not rows:
        return None
    entities = [
        {
            "@type": "Question",
            "name": q,
            "acceptedAnswer": {"@type": "Answer", "text": a},
        }
        for q, a in rows
    ]
    payload = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": entities}
    return json.dumps(payload, ensure_ascii=False)
