from app.i18n import get_ui_text

TAG_DEFINITIONS = {
    "academic": {
        "name": "Academic",
        "icon": "🎓",
        "description": "Institutes with strong TOPIK and university admission tracks.",
        "keywords": ["topik", "university prep", "university preparation", "academic", "degree", "진학", "大学進学"],
    },
    "business": {
        "name": "Business",
        "icon": "💼",
        "description": "Schools with business Korean courses or job hunting support.",
        "keywords": ["business", "job", "취업", "ビジネス"],
    },
    "culture": {
        "name": "Conversation",
        "icon": "🗣️",
        "description": "Schools emphasizing conversational skills and cultural activities.",
        "keywords": ["conversation", "culture", "short-term", "회화", "短期", "문화"],
    },
    "seoul": {"name": "Seoul", "icon": "🏙️", "description": "Institutes in the Seoul area."},
    "busan": {"name": "Busan", "icon": "🌊", "description": "Institutes in the Busan area."},
    "daegu": {"name": "Daegu", "icon": "🏔️", "description": "Institutes in the Daegu area."},
    "gwangju": {"name": "Gwangju", "icon": "🌿", "description": "Institutes in the Gwangju area."},
    "major_city": {
        "name": "Other Cities",
        "icon": "🏘️",
        "description": "Institutes in Incheon, Daejeon, and other major cities.",
    },
    "university": {"name": "Universities", "icon": "🏛️", "description": "Universities across Korea."},
    "size_small": {"name": "Small", "icon": "🧑‍🏫", "description": "Small-sized schools (Capacity: ~150 students)."},
    "size_medium": {"name": "Medium", "icon": "👨‍👩‍👧‍👦", "description": "Medium-sized schools (Capacity: 151-500 students)."},
    "dormitory": {"name": "Dormitory", "icon": "🏠", "description": "Schools that offer dormitory options."},
}

MAJOR_CITIES = ["인천", "대전", "수원", "창원", "Incheon", "Daejeon"]
DORM_KEYWORDS = ["dormitory", "기숙사", "寮"]


def calculate_tag_counts(schools):
    counts = {key: 0 for key in TAG_DEFINITIONS}

    for school in schools:
        if school.get("category") == "university":
            counts["university"] += 1
            continue

        features = school.get("features")
        if not features:
            features = []
        elif isinstance(features, str):
            features = [features]

        safe_features = [str(f) for f in features if f is not None]
        full_text = " ".join(safe_features).lower()

        if any(kw in full_text for kw in TAG_DEFINITIONS["academic"]["keywords"]):
            counts["academic"] += 1
        if any(kw in full_text for kw in TAG_DEFINITIONS["business"]["keywords"]):
            counts["business"] += 1
        if any(kw in full_text for kw in TAG_DEFINITIONS["culture"]["keywords"]):
            counts["culture"] += 1

        b_info = school.get("basic_info") or {}
        address = b_info.get("address") or ""
        if "서울" in address or "Seoul" in address:
            counts["seoul"] += 1
        elif "부산" in address or "Busan" in address:
            counts["busan"] += 1
        elif "대구" in address or "Daegu" in address:
            counts["daegu"] += 1
        elif "광주" in address or "Gwangju" in address:
            counts["gwangju"] += 1
        elif any(city in address for city in MAJOR_CITIES):
            counts["major_city"] += 1

        capacity = b_info.get("capacity")
        if isinstance(capacity, int):
            if capacity <= 150:
                counts["size_small"] += 1
            elif capacity <= 500:
                counts["size_medium"] += 1

        if any(kw in full_text for kw in DORM_KEYWORDS):
            counts["dormitory"] += 1

    results = [
        {"key": key, "name": d["name"], "icon": d["icon"], "description": d["description"], "count": counts[key]}
        for key, d in TAG_DEFINITIONS.items()
    ]
    return [tag for tag in results if tag["count"] >= 5]


def get_category_filters(lang="en"):
    ui = get_ui_text(lang)
    return [
        {"key": "all", "icon": "🌏", "label": ui["filter_all_types"]},
        {"key": "school", "icon": "🏫", "label": ui["filter_language_schools"]},
        {"key": "university", "icon": "🏛️", "label": ui["filter_universities"]},
    ]


def get_school_feature_filters(lang="en"):
    ui = get_ui_text(lang)
    return [
        {"key": "dormitory", "icon": "🏠", "label": ui["filter_dormitory"]},
        {"key": "academic", "icon": "🎓", "label": ui["filter_academic"]},
        {"key": "size_medium", "icon": "📊", "label": ui["filter_medium"]},
    ]


def get_type_filters(lang="en"):
    return get_category_filters(lang)


def get_region_filters(lang="en"):
    ui = get_ui_text(lang)
    return [
        {"key": "all", "icon": "🌏", "label": ui["filter_all_regions"]},
        {"key": "seoul", "icon": "🏙️", "label": ui["filter_seoul"]},
        {"key": "busan", "icon": "🌊", "label": ui["filter_busan"]},
        {"key": "daegu", "icon": "🏔️", "label": ui["filter_daegu"]},
        {"key": "gwangju", "icon": "🌿", "label": ui["filter_gwangju"]},
        {"key": "major_city", "icon": "🏘️", "label": ui["filter_other_cities"]},
    ]


def get_quick_filters(lang="en"):
    return get_type_filters(lang) + get_region_filters(lang)[1:]
