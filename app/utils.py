# app/utils.py
import json
import os
import glob
import hashlib
import frontmatter
from fastapi import Request

try:
    from .content_new import enrich_item
except ImportError:
    from content_new import enrich_item

# --- 디렉토리 경로 설정 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
CONTENT_DIR = os.path.join(BASE_DIR, "content") 
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# --- 기존 필터 정의 ---
TAG_DEFINITIONS = {
    'academic': {'name': 'Academic', 'icon': '🎓', 'description': 'Institutes with strong TOPIK and university admission tracks.', 'keywords':["topik", "university prep", "university preparation", "academic", "degree", "진학", "大学進学"]},
    'business': {'name': 'Business', 'icon': '💼', 'description': 'Schools with business Japanese courses or job hunting support.', 'keywords':["business", "job", "취업", "ビジネス"]},
    'culture': {'name': 'Conversation', 'icon': '🗣️', 'description': 'Schools emphasizing conversational skills and cultural activities.', 'keywords':["conversation", "culture", "short-term", "회화", "短期", "문화"]},
    'seoul': {'name': 'Seoul', 'icon': '🏙️', 'description': 'Institutes in the Seoul area.'},
    'busan': {'name': 'Busan', 'icon': '🌊', 'description': 'Institutes in the Busan area.'},
    'major_city': {'name': 'Other Cities', 'icon': '🏘️', 'description': 'Institutes in Daegu, Incheon, Gwangju, Daejeon, and other major cities.'},
    'university': {'name': 'Universities', 'icon': '🏛️', 'description': 'Universities across Korea.'},
    'size_small': {'name': 'Small', 'icon': '🧑‍🏫', 'description': 'Small-sized schools (Capacity: ~150 students).'},
    'size_medium': {'name': 'Medium', 'icon': '👨‍👩‍👧‍👦', 'description': 'Medium-sized schools (Capacity: 151-500 students).'},
    'dormitory': {'name': 'Dormitory', 'icon': '🏠', 'description': 'Schools that offer dormitory options.'},
}

def calculate_tag_counts(schools):
    counts = {key: 0 for key in TAG_DEFINITIONS}
    MAJOR_CITIES =['부산', '대구', '인천', '광주', '대전', '수원', '창원']
    DORM_KEYWORDS =['dormitory', '기숙사', '寮']

    for school in schools:
        if school.get('category') == 'university':
            counts['university'] += 1
            continue

        # [방어 로직] features가 null이거나 문자가 섞여 있어도 절대 에러 나지 않음
        features = school.get('features')
        if not features: features = []
        elif isinstance(features, str): features = [features]
        
        safe_features = [str(f) for f in features if f is not None]
        full_text = " ".join(safe_features).lower()
        
        if any(kw in full_text for kw in TAG_DEFINITIONS['academic']['keywords']): counts['academic'] += 1
        if any(kw in full_text for kw in TAG_DEFINITIONS['business']['keywords']): counts['business'] += 1
        if any(kw in full_text for kw in TAG_DEFINITIONS['culture']['keywords']): counts['culture'] += 1

        b_info = school.get('basic_info') or {}
        address = b_info.get('address') or ''
        if '서울' in address or 'Seoul' in address: counts['seoul'] += 1
        elif '부산' in address or 'Busan' in address: counts['busan'] += 1
        elif any(city in address for city in MAJOR_CITIES): counts['major_city'] += 1
        
        capacity = b_info.get('capacity')
        if isinstance(capacity, int):
            if capacity <= 150: counts['size_small'] += 1
            elif capacity <= 500: counts['size_medium'] += 1
        
        if any(kw in full_text for kw in DORM_KEYWORDS): counts['dormitory'] += 1

    results = [
        {'key': key, 'name': d['name'], 'icon': d['icon'], 'description': d['description'], 'count': counts[key]}
        for key, d in TAG_DEFINITIONS.items()
    ]
    return [tag for tag in results if tag['count'] >= 5]

def get_quick_filters(lang="en"):
    ui = get_ui_text(lang)
    return [
        {"key": "all", "icon": "📍", "label": ui["filter_all"]},
        {"key": "seoul", "icon": "🏙️", "label": ui["filter_seoul"]},
        {"key": "busan", "icon": "🌊", "label": ui["filter_busan"]},
        {"key": "dormitory", "icon": "🏠", "label": ui["filter_dormitory"]},
        {"key": "academic", "icon": "🎓", "label": ui["filter_academic"]},
        {"key": "university", "icon": "🏛️", "label": ui["filter_universities"]},
        {"key": "major_city", "icon": "🏘️", "label": ui["filter_other_cities"]},
        {"key": "size_medium", "icon": "📊", "label": ui["filter_medium"]},
    ]

def get_client_ip(request: Request):
    try:
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for: return x_forwarded_for.split(",")[0].strip()
        if request.client and request.client.host: return request.client.host
    except Exception: pass
    return "unknown_ip"

# =========================================================================
# 🚨 여기에 대표님이 가지고 계신 90개의 썸네일 리스트를 그대로 붙여넣으세요! 🚨
# --- 썸네일 풀 (3종류 - 총 90개) ---
UNIV_THUMBNAILS =[
    "https://images.unsplash.com/photo-1541339907198-e08756dedf3f?w=500", "https://images.unsplash.com/photo-1498243691581-b145c3f54a5a?w=500",
    "https://images.unsplash.com/photo-1592280771190-3e2e4d571952?w=500", "https://images.unsplash.com/photo-1562774053-701939374585?w=500",
    "https://images.unsplash.com/photo-1606092195730-5d7b9af1efc5?w=500", "https://images.unsplash.com/photo-1521587760476-6c12a4b040da?w=500",
    "https://images.unsplash.com/photo-1584697964190-7383cbee8277?w=500", "https://images.unsplash.com/photo-1511629091441-ee46146481b6?w=500",
    "https://images.unsplash.com/photo-1573894998033-c0cef4ed722b?w=500", "https://images.unsplash.com/photo-1485893086445-ed75865251e0?w=500",
    "https://images.unsplash.com/photo-1568038479111-87bf80659645?w=500", "https://images.unsplash.com/photo-1542621334-a254cf47733d?w=500",
    "https://images.unsplash.com/photo-1500088139251-37350df3c1ad?w=500",
    "https://images.unsplash.com/photo-1547699326-3d895d9acd30?w=500", 
    "https://images.unsplash.com/photo-1612310480588-061aad90bb64?w=500",
    "https://images.unsplash.com/photo-1592280771190-3e2e4d571952?w=600", "https://images.unsplash.com/photo-1562774053-701939374585?w=600",
    "https://images.unsplash.com/photo-1606092195730-5d7b9af1efc5?w=600", "https://images.unsplash.com/photo-1521587760476-6c12a4b040da?w=600",
    "https://images.unsplash.com/photo-1541336318489-083c7d277b8e?w=600", 
    "https://images.unsplash.com/photo-1511629091441-ee46146481b6?w=600",
    "https://images.unsplash.com/photo-1464938050520-ef2270bb8ce8?w=600", "https://images.unsplash.com/photo-1519452635265-7b1fbfd1e4e0?w=600",
    "https://images.unsplash.com/photo-1517486808906-6ca8b3f04846?w=600",
    "https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?w=600",
    "https://images.unsplash.com/photo-1527891751199-7225231a68dd?w=600"

]

SCHOOL_THUMBNAILS =[
    "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=500", "https://images.unsplash.com/photo-1509062522246-3755977927d7?w=500",
    "https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=500", "https://images.unsplash.com/photo-1580582932707-520aed937b7b?w=500",
    "https://images.unsplash.com/photo-1544531586-fde5298cdd40?w=500", "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?w=500",
    "https://images.unsplash.com/photo-1528164344705-47542687000d?w=500", "https://images.unsplash.com/photo-1577985051167-0d49eec21977?w=500",
    "https://images.unsplash.com/photo-1581092334978-16972703644f?w=500", "https://images.unsplash.com/photo-1608813607488-0f932c5b71ef?w=500",
    "https://images.unsplash.com/photo-1581276879432-15e50529f34b?w=500", "https://images.unsplash.com/photo-1584697964190-7383cbee8277?w=500",
    "https://images.unsplash.com/photo-1577825294026-50dc375b9119?w=500", "https://images.unsplash.com/photo-1453694595360-51e193e121fc?w=500",
    "https://images.unsplash.com/photo-1573416033034-e42e14b545d2?w=500", "https://images.unsplash.com/photo-1586877644127-e5ee9b4231c3?w=500",
    "https://images.unsplash.com/photo-1550303435-1703d8811aaa?w=500", "https://images.unsplash.com/photo-1505738313577-5357ff512f16?w=500",
    "https://images.unsplash.com/photo-1561535893-bb7a98c7ee45?w=500", "https://images.unsplash.com/photo-1523905330026-b8bd1f5f320e?w=500",
    "https://images.unsplash.com/photo-1613376023733-0a73315d9b06?w=500", "https://images.unsplash.com/photo-1493934558415-9d19f0b2b4d2?w=500",
    "https://images.unsplash.com/photo-1541336318489-083c7d277b8e?w=500", "https://images.unsplash.com/photo-1622589476300-b72799ca4ade?w=500",
    "https://images.unsplash.com/photo-1639621108959-15f9c4257508?w=500", "https://images.unsplash.com/photo-1503387762-592deb58ef4e?w=500",
    "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=500", "https://images.unsplash.com/photo-1526916025899-1a28d20f2a5f?w=500",
    "https://images.unsplash.com/photo-1559077138-3e27e1cdb95a?w=500", "https://images.unsplash.com/photo-1598368195835-91e67f80c9d7?w=500"
]

GUIDE_THUMBNAILS =[
    "https://images.unsplash.com/photo-1491841550275-ad7854e35ca6?w=500", "https://images.unsplash.com/photo-1610312278520-bcc893a3ff1d?w=500",
    "https://images.unsplash.com/photo-1590559899731-a382839e5549?w=500", "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=500",
    "https://images.unsplash.com/photo-1561414927-6d86591d0c4f?w=500", "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=500",
    "https://images.unsplash.com/photo-1556740758-90de374c12ad?w=500", "https://images.unsplash.com/photo-1563986768609-322da13575f3?w=500",
    "https://images.unsplash.com/photo-1505751172876-fa1923c5c528?w=500", "https://images.unsplash.com/photo-1542051841857-5f90071e7989?w=500",
    "https://images.unsplash.com/photo-1580167227251-be70f01b0c51?w=500", "https://images.unsplash.com/photo-1684526688489-b08cbd8e1848?w=500",
    "https://images.unsplash.com/photo-1603491543570-f7df3c9a12c1?w=500", "https://images.unsplash.com/photo-1563089145-599997674d42?w=500",
    "https://images.unsplash.com/photo-1580477667995-2b94f01c9516?w=500", "https://images.unsplash.com/photo-1560972550-aba3456b5564?w=500",
    "https://images.unsplash.com/photo-1548630435-998a2cbbff67?w=500",
    "https://images.unsplash.com/photo-1473496169904-658ba7c44d8a?w=500", "https://images.unsplash.com/photo-1558471250-385a4b04941e?w=500",
    "https://images.unsplash.com/photo-1526127230111-0197afe94d72?w=500", "https://images.unsplash.com/photo-1557409518-691ebcd96038?w=500",
    "https://images.unsplash.com/photo-1516205651411-aef33a44f7c2?w=500", "https://images.unsplash.com/photo-1551322120-c697cf88fbdc?w=500",
    "https://images.unsplash.com/photo-1573655349936-de6bed86f839?w=500", "https://images.unsplash.com/photo-1540569014015-19a7be504e3a?w=500",
    "https://images.unsplash.com/photo-1492571350019-22de08371fd3?w=500",
    "https://images.unsplash.com/photo-1517486808906-6ca8b3f04846?w=500", "https://images.unsplash.com/photo-1522199755839-a2bacb67c546?w=500"
]
# =========================================================================

GUIDE_CATEGORY_THUMBNAILS = {
    "Budget": "https://images.unsplash.com/photo-1561414927-6d86591d0c4f?w=500",
    "Cost": "https://images.unsplash.com/photo-1561414927-6d86591d0c4f?w=500",
    "Selection": "https://images.unsplash.com/photo-1528164344705-47542687000d?w=500",
    "Visa": "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=500",
    "Housing": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=500",
    "Part-time": "https://images.unsplash.com/photo-1556740758-90de374c12ad?w=500",
    "Exam": "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=500",
    "Preparation": "https://images.unsplash.com/photo-1501504905252-473c47e087f8?w=500",
    "Settlement": "https://images.unsplash.com/photo-1563986768609-322da13575f3?w=500",
    "Insurance": "https://images.unsplash.com/photo-1505751172876-fa1923c5c528?w=500",
    "Region": "https://images.unsplash.com/photo-1542051841857-5f90071e7989?w=500",
    "Life": "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=500",
}


def _guide_thumbnail_from_id(guide_id: str) -> str:
    hash_val = int(hashlib.md5(guide_id.encode("utf-8")).hexdigest(), 16)
    return GUIDE_THUMBNAILS[hash_val % len(GUIDE_THUMBNAILS)]


def resolve_guide_list_thumbnail(meta):
    """One unique image per guide for cards/lists (category URLs repeat)."""
    return _guide_thumbnail_from_id(str(meta.get("id") or ""))


def resolve_guide_detail_thumbnail(meta):
    """Detail hero: frontmatter, then category, then per-guide hash."""
    thumb = (meta.get("thumbnail") or "").strip()
    if thumb.startswith("http"):
        return thumb
    category = str(meta.get("category") or "")
    for key, url in GUIDE_CATEGORY_THUMBNAILS.items():
        if key.lower() in category.lower():
            return url
    return _guide_thumbnail_from_id(str(meta.get("id") or ""))


def diversify_guide_thumbnails(guides):
    """Avoid duplicate thumbnails within a visible guide row."""
    used = set()
    diversified = []
    for guide in guides:
        item = dict(guide)
        thumb = item.get("thumbnail") or ""
        guide_id = item.get("link", "").split("/guide/")[-1].split("?")[0]
        if thumb in used:
            base = int(hashlib.md5(guide_id.encode("utf-8")).hexdigest(), 16)
            for offset in range(len(GUIDE_THUMBNAILS)):
                candidate = GUIDE_THUMBNAILS[(base + offset) % len(GUIDE_THUMBNAILS)]
                if candidate not in used:
                    thumb = candidate
                    break
        used.add(thumb)
        item["thumbnail"] = thumb
        diversified.append(item)
    return diversified


def resolve_guide_thumbnail(meta):
    """Backward-compatible alias for list/card thumbnails."""
    return resolve_guide_list_thumbnail(meta)

def assign_thumbnails(items, item_category="school"):
    if item_category == "university": thumb_pool = UNIV_THUMBNAILS
    else: thumb_pool = SCHOOL_THUMBNAILS

    for item in items:
        if not item.get('thumbnail'):
            item_id = str(item.get('id', 'default_id')) 
            hash_val = int(hashlib.md5(item_id.encode('utf-8')).hexdigest(), 16)
            item['thumbnail'] = thumb_pool[hash_val % len(thumb_pool)]
    return items

def get_ui_text(lang):
    if lang == "ja":
        return {
            "featured_title": "おすすめ", "best_selection": "ピックアップ", "view_ranking": "ランキング →",
            "language_schools": "韓国語学堂", "top_universities": "主要大学", "view_all": "すべて見る →",
            "essential_guides": "留学ガイド", "school_badge": "語学堂", "univ_badge": "大学",
            "contact_fee": "学費問合せ", "yearly": "年間", "search_placeholder": "大学を検索...",
            "all_schools": "語学堂一覧", "back_to_map": "地図に戻る", "back_to_list": "一覧に戻る",
            "global_programs": "グローバルプログラム", "national_private": "公式機関",
            "view_all_schools": "語学堂一覧 →", "view_all_univs": "大学一覧 →",
            "find_schools": "語学堂を探す", "find_universities": "大学を探す", "read_guides": "ガイドを見る",
            "filter_all": "すべて", "filter_seoul": "ソウル", "filter_busan": "釜山", "filter_dormitory": "寮",
            "filter_academic": "進学", "filter_universities": "大学",
            "filter_other_cities": "その他", "filter_medium": "中型",
            "schools_listed": "件登録", "last_updated": "最終更新:", "updating_weekly": "毎週更新",
            "see_related_guides": "関連ガイド", "contact_us": "お問い合わせ",
            "related_schools": "関連語学堂", "related_guides": "関連ガイド",
            "reaction_title": "この記事は役に立ちましたか？",
            "reaction_subtitle": "フィードバックはコンテンツ改善に活用します",
            "category": "区分", "capacity": "定員", "yearly_tuition": "年間学費", "view_details": "詳細を見る",
            "students": "留学生数", "language_school": "語学堂", "university": "大学", "country_fallback": "韓国",
            "schools_list_title": "韓国語学堂一覧",
            "schools_list_desc": "韓国全国の韓国語学堂を地域・学費などで比較できます。",
            "universities_list_title": "韓国大学一覧",
            "universities_list_desc": "留学生向けの韓国大学情報を確認できます。",
            "guides_list_title": "留学ガイド",
            "guides_list_desc": "韓国留学の実用ガイド（ビザ・住居・生活）をご覧ください。",
            "meta_home_title": "KR Campus 公式 — 韓国語学堂・大学ガイド",
            "meta_home_desc": "KR Campus: 韓国語学堂・大学を地図で比較。ビザ・住居・入学・生活ガイド。",
            "meta_schools_title": "韓国語学堂一覧 — 地域別比較 | KR Campus",
            "meta_schools_desc": "韓国全国の韓国語学堂を地域・学費などで比較し、各校の詳細ページへ進めます。",
            "meta_guides_title": "韓国留学ガイド | KR Campus",
            "meta_guides_desc": "費用・住居・ビザ・学生生活の実用ガイド。",
            "guide_badge": "ガイド",
            "share_label": "このページを共有",
            "share_copy": "リンクをコピー",
            "share_copied": "コピーしました",
            "share_hint": "X共有は /card/ プレビューURLを使います。画像が表示されない場合は ",
            "share_hint_link": "カードページ",
            "share_hint_tail": "を開いてからXボタンで共有してください。",
        }
    return {
        "featured_title": "Featured Collections", "best_selection": "Best Selection", "view_ranking": "View Ranking →",
        "language_schools": "Language Institutes", "top_universities": "Top Universities", "view_all": "View all →",
        "essential_guides": "Study in Korea Guides", "school_badge": "Institute", "univ_badge": "University",
        "contact_fee": "Contact for Fee", "yearly": "Yearly", "search_placeholder": "Search universities...",
        "all_schools": "All Institutes", "back_to_map": "Back to Map", "back_to_list": "Back to List",
        "global_programs": "Global Programs", "national_private": "Official National/Private Institute",
        "view_all_schools": "View all institutes →", "view_all_univs": "View all universities →",
        "find_schools": "Find Schools", "find_universities": "Find Universities", "read_guides": "Read Guides",
        "filter_all": "All", "filter_seoul": "Seoul", "filter_busan": "Busan", "filter_dormitory": "Dorm",
        "filter_academic": "Prep", "filter_universities": "Univ",
        "filter_other_cities": "Other", "filter_medium": "Mid",
        "schools_listed": "Schools Listed", "last_updated": "Last Updated:", "updating_weekly": "Updating Weekly",
        "see_related_guides": "See Related Guides", "contact_us": "Contact Us",
        "related_schools": "Related Schools", "related_guides": "Related Guides",
        "reaction_title": "Was this page helpful?",
        "reaction_subtitle": "Your feedback helps us improve our guides",
        "category": "Category", "capacity": "Capacity", "yearly_tuition": "Yearly Tuition", "view_details": "View Details",
        "students": "Students", "language_school": "Language School", "university": "University", "country_fallback": "Korea",
        "schools_list_title": "All Language Institutes",
        "schools_list_desc": "Browse all language institutes across Korea.",
        "universities_list_title": "All Universities",
        "universities_list_desc": "Explore universities in Korea for international students.",
        "guides_list_title": "Essential Guides",
        "guides_list_desc": "Read practical study-abroad guides for life in Korea.",
        "meta_home_title": "KR Campus (Official) — Korea Language Schools, Universities & Map",
        "meta_home_desc": (
            "Official KR Campus: compare Korean language institutes and universities on an interactive map, "
            "plus practical visa, housing, admissions, and student-life guides."
        ),
        "meta_schools_title": "Korean Language Institutes — Compare by City | KR Campus",
        "meta_schools_desc": (
            "Browse Korean language institutes across Korea: compare areas, typical costs, and student-life notes, "
            "then open each school page for details."
        ),
        "meta_guides_title": "Essential Korea Study Guides | KR Campus",
        "meta_guides_desc": "Read practical guides on costs, housing, visas, and student life in Korea.",
        "guide_badge": "Guide",
        "share_label": "Share this page",
        "share_copy": "Copy link",
        "share_copied": "Copied!",
        "share_hint": "X shares use the /card/ preview URL. If the image is missing, ",
        "share_hint_link": "open the card page",
        "share_hint_tail": ", then share again via the X button.",
    }

def _read_schools_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("schools", []), data.get("last_updated", "")

def _apply_lang_to_schools(schools, lang):
    for school in schools:
        sid = school.get("id", "")
        school["link"] = f"/school/{sid}?lang={lang}"
    return schools

def load_school_data(lang="en"):
    en_path = os.path.join(STATIC_DIR, "json", "schools_data.json")
    try:
        if lang == "ja":
            ja_path = os.path.join(STATIC_DIR, "json", "schools_data_ja.json")
            if os.path.exists(ja_path):
                schools, updated = _read_schools_json(ja_path)
                if schools:
                    return schools, updated
            schools, updated = _read_schools_json(en_path)
            return _apply_lang_to_schools(schools, "ja"), updated
        return _read_schools_json(en_path)
    except Exception as e:
        print(f"Error loading data: {e}")
        return [], ""

def _load_guide_files(lang):
    guides = []
    pattern = os.path.join(CONTENT_DIR, "guide_*_ja.md") if lang == "ja" else os.path.join(CONTENT_DIR, "guide_*.md")
    guide_files = glob.glob(pattern)
    if lang != "ja":
        guide_files = [f for f in guide_files if not f.endswith("_ja.md")]

    guide_files.sort(key=os.path.getmtime, reverse=True)

    for filepath in guide_files:
        try:
            post = frontmatter.load(filepath)
            meta = post.metadata
            guide_id = str(meta.get("id", "")).replace("_ja", "").replace("guide_", "")
            safe_thumbnail = resolve_guide_list_thumbnail(meta)

            guides.append(enrich_item({
                "title": meta.get("title", "Untitled"),
                "description": meta.get("description", ""),
                "category": meta.get("category", "Guide"),
                "link": f"/guide/{guide_id}?lang={lang}",
                "thumbnail": safe_thumbnail,
                "item_type": "guide",
                "is_featured": meta.get("is_featured", False),
                "published": str(meta.get("date", "")),
            }))
        except Exception:
            pass
    return guides

def load_guides(lang="en"):
    guides = _load_guide_files(lang)
    if lang == "ja" and not guides:
        guides = _load_guide_files("en")
        for guide in guides:
            guide["link"] = guide["link"].replace("lang=en", "lang=ja")
    return guides