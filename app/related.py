"""Related content pickers — Korea region keywords."""

from app.content_loader import load_guides, load_school_data
from app.thumbnails import assign_thumbnails

KOREA_CITY_KEYWORDS = [
    "seoul", "busan", "daegu", "gwangju", "incheon", "daejeon", "suwon", "ulsan",
    "서울", "부산", "대구", "광주", "인천", "대전", "수원", "울산", "korea",
]

CITY_ADDRESS_CHECKS = [
    (["seoul", "서울"], ["seoul", "서울"]),
    (["busan", "부산"], ["busan", "부산"]),
    (["daegu", "대구"], ["daegu", "대구"]),
    (["gwangju", "광주"], ["gwangju", "광주"]),
    (["incheon", "인천"], ["incheon", "인천"]),
    (["daejeon", "대전"], ["daejeon", "대전"]),
]


def _matched_city_keywords(source_text: str) -> list[str]:
    lower = source_text.lower()
    matched = [kw for kw in KOREA_CITY_KEYWORDS if kw in lower or kw in source_text]
    return matched


def pick_related_guides(item: dict, item_type: str, lang: str, limit: int = 4) -> list[dict]:
    guides = load_guides(lang)
    if item_type == "guide":
        source_text = f"{item.get('title', '')} {item.get('description', '')}"
    else:
        basic = item.get("basic_info", {}) or {}
        source_text = f"{basic.get('name_en', '')} {basic.get('address', '')}"

    matched = _matched_city_keywords(source_text)
    related = []
    for guide in guides:
        guide_text = f"{guide.get('title', '')} {guide.get('description', '')}"
        if any(kw in guide_text.lower() or kw in guide_text for kw in matched):
            related.append(guide)
    if len(related) < limit:
        existing_links = {g.get("link") for g in related}
        for guide in guides:
            if guide.get("link") not in existing_links:
                related.append(guide)
            if len(related) >= limit:
                break
    return related[:limit]


def pick_compare_guides(selected: list[dict], lang: str, limit: int = 4) -> list[dict]:
    if not selected:
        return []
    related: list[dict] = []
    seen: set[str] = set()
    for item in selected:
        item_type = "university" if item.get("category") == "university" else "school"
        for guide in pick_related_guides(item, item_type, lang, limit=2):
            link = guide.get("link")
            if link and link not in seen:
                seen.add(link)
                related.append(guide)
            if len(related) >= limit:
                return related[:limit]
    for guide in load_guides(lang):
        link = guide.get("link")
        if link and link not in seen:
            seen.add(link)
            related.append(guide)
        if len(related) >= limit:
            break
    return related[:limit]


def pick_related_schools(item: dict, lang: str, limit: int = 4) -> list[dict]:
    schools, _ = load_school_data(lang)
    source_text = f"{item.get('title', '')} {item.get('description', '')}"
    lower = source_text.lower()
    wants_university = "university" in lower or "topik" in lower or "degree" in lower
    wants_school = "language school" in lower or "language institute" in lower or "topik" in lower

    related = []
    for school in schools:
        basic = school.get("basic_info", {}) or {}
        address = basic.get("address", "")
        address_lower = address.lower()
        category = school.get("category")

        if wants_university and category != "university":
            continue
        if wants_school and category == "university":
            continue

        skip = False
        for source_kws, address_kws in CITY_ADDRESS_CHECKS:
            if any(kw in lower or kw in source_text for kw in source_kws):
                if not any(kw in address_lower or kw in address for kw in address_kws):
                    skip = True
                    break
        if skip:
            continue

        if _matched_city_keywords(source_text):
            related.append(school)
        if len(related) >= limit:
            break

    if len(related) < limit:
        for school in schools:
            if school not in related:
                related.append(school)
            if len(related) >= limit:
                break

    return assign_thumbnails(related[:limit], "university" if wants_university else "school")
