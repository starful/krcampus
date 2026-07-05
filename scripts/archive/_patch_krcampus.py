#!/usr/bin/env python3
"""One-time KR Campus localization patches."""
from pathlib import Path

ROOT = Path("/opt/work/krcampus")


def patch_file(rel: str, replacements: list[tuple[str, str]]):
    path = ROOT / rel
    if not path.is_file():
        print(f"skip missing {rel}")
        return
    text = path.read_text(encoding="utf-8")
    for old, new in replacements:
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")
    print(f"patched {rel}")


COMMON_MAIN = [
    ("https://jpcampus.net", "https://krcampus.net"),
    ('suffix: str = "JP Campus"', 'suffix: str = "KR Campus"'),
    ('lang == "kr"', 'lang == "ja"'),
    ('lang != "kr"', 'lang != "ja"'),
    ('?lang=kr', '?lang=ja'),
    ('_kr.md', '_ja.md'),
    ('hreflang="ko"', 'hreflang="ja"'),
    ('"ko": build_canonical_url(path, "ja")', '"ja": build_canonical_url(path, "ja")'),
    ("Study in Japan", "Study in Korea"),
    ("study in Japan", "study in Korea"),
    ("study-abroad guides for life in Japan", "study-abroad guides for life in Korea"),
    ("life in Japan", "life in Korea"),
    ("Japanese language schools", "Korean language institutes"),
    ("language schools across Japan", "language institutes across Korea"),
    ("Language Schools in Japan", "Language Institutes in Korea"),
    ("All Language Schools", "All Language Institutes"),
    ("Universities in Japan", "Universities in Korea"),
    ("universities in Japan", "universities in Korea"),
    ("Schools in Japan", "Schools in Korea"),
    ("About JP Campus", "About KR Campus"),
    ("Contact JP Campus", "Contact KR Campus"),
    ("JP Campus helps", "KR Campus helps"),
    ("JP Campus handles", "KR Campus handles"),
    ("JP Campus:", "KR Campus:"),
    ("JP Campus ", "KR Campus "),
    ("JP Campus.", "KR Campus."),
    ("JP Campus,", "KR Campus,"),
    ("JP Campus 공식", "KR Campus 公式"),
    ("일본 어학원·대학", "韓国語学堂・大学"),
    ("일본어학교", "韓国語学堂"),
    ("일본 전국", "韓国全国"),
    ("일본 대학교", "韓国大学"),
    ("일본 유학", "韓国留学"),
    ("일본 생활", "韓国生活"),
    ('"name_ja"', '"name_ko"'),
    (".get('name_ja')", ".get('name_ko')"),
    (".get(\"name_ja\")", ".get(\"name_ko\")"),
    ("Japan & the World", "TOPIK"),
    ("Japan Ramen Guide", "JP Campus (Japan)"),
    ("Onsen & Ryokan Guide", "Study in Japan — JP Campus"),
    ("Japan Golf Course Map", "OK Series Japan"),
    ("Explore More of Japan", "Explore JP Campus"),
    ("international students planning to study in Japan", "international students planning to study in Korea"),
    ("'Study in Japan' platform", "'Study in Korea' platform"),
]

patch_file("app/main.py", COMMON_MAIN + [
    ('build_meta_title(\n            "JP Campus (Official) — Japan Language Schools, Universities & Map"',
     'build_meta_title(\n            "KR Campus — Korean Language Institutes, Universities & Guides"'),
    ('else "JP Campus 공식 — 일본 어학원·대학 비교 지도와 유학 가이드"',
     'else "KR Campus 公式 — 韓国語学堂・大学ガイド"'),
    ('"Official JP Campus: compare Japanese language schools and universities on an interactive map, "',
     '"KR Campus: compare Korean language institutes and universities on an interactive map, "'),
    ('else "JP Campus 공식 사이트: 일본 어학원·대학을 지도에서 비교하고, 비자·주거·입학·생활 "',
     'else "KR Campus: 韓国語学堂・大学を地図で比較。ビザ・住居・入学・生活ガイド。"'),
    ('"Browse Japanese language schools across Japan: compare areas, typical costs, and student-life notes, "',
     '"Browse Korean language institutes across Korea: compare areas, typical costs, and student-life notes, "'),
    ('else "일본 전국 일본어학교를 지역·학비 등으로 살펴보고, 각 학교 상세 페이지로 이어지는 "',
     'else "韓国全国の語学堂を地域・学費で比較し、各学校ページへ。"'),
    ('"Find university options in Japan with practical comparisons and prep guidance."',
     '"Find university options in Korea with practical comparisons and prep guidance."'),
    ('"Read practical guides on costs, housing, visas, and student life in Japan."',
     '"Read practical guides on costs, housing, visas, and student life in Korea."'),
    ('"Learn how JP Campus helps international students choose schools in Japan."',
     '"Learn how KR Campus helps international students choose schools in Korea."'),
    ('"Contact JP Campus for corrections, feedback, or collaboration."',
     '"Contact KR Campus for corrections, feedback, or collaboration."'),
    ('"Read how JP Campus handles privacy, cookies, and data usage."',
     '"Read how KR Campus handles privacy, cookies, and data usage."'),
    ('"일본 전역의 일본어학교를 확인하세요."', '"韓国全国の韓国語学堂一覧。"'),
    ('"유학생을 위한 일본 대학교 정보를 확인하세요."', '"留学生向け韓国大学情報。"'),
    ('"일본 유학 생활 실전 가이드를 확인하세요."', '"韓国留学の実用ガイド。"'),
])

# utils.py
utils_path = ROOT / "app/utils.py"
if utils_path.is_file():
    u = utils_path.read_text(encoding="utf-8")
    u = u.replace('filename = "schools_data_kr.json" if lang == "kr"', 'filename = "schools_data_ja.json" if lang == "ja"')
    u = u.replace('pattern = os.path.join(CONTENT_DIR, "guide_*_kr.md") if lang == "kr"', 'pattern = os.path.join(CONTENT_DIR, "guide_*_ja.md") if lang == "ja"')
    u = u.replace('if lang != "kr":\n        guide_files =[f for f in guide_files if not f.endswith("_kr.md")]', 'if lang != "ja":\n        guide_files =[f for f in guide_files if not f.endswith("_ja.md")]')
    u = u.replace("guide_id = str(meta.get('id', '')).replace('_kr', '')", "guide_id = str(meta.get('id', '')).replace('_ja', '').replace('guide_', '')")
    u = u.replace('if lang == "kr":', 'if lang == "ja":')
    u = u.replace("MAJOR_CITIES =['福岡', '名古屋', '京都', '神戸', '札幌', '横浜', '仙台']", "MAJOR_CITIES =['부산', '대구', '인천', '광주', '대전', '수원', '창원']")
    u = u.replace("'東京都' in address", "'서울' in address")
    u = u.replace("'大阪府' in address", "'부산' in address")
    u = u.replace("keywords':[\"eju\", \"university\"", "keywords':[\"topik\", \"university\"")
    u = u.replace("'tokyo': {'name': 'Tokyo'", "'seoul': {'name': 'Seoul'")
    u = u.replace("'osaka': {'name': 'Osaka'", "'busan': {'name': 'Busan'")
    u = u.replace("if '東京都' in address: counts['tokyo']", "if '서울' in address: counts['seoul']")
    u = u.replace("elif '大阪府' in address: counts['osaka']", "elif '부산' in address: counts['busan']")
    # Replace get_ui_text kr block start
    old_ui = '''    if lang == "ja":
        return {
            "featured_title": "추천 컬렉션",'''
    new_ui = '''    if lang == "ja":
        return {
            "featured_title": "おすすめコレクション",
            "best_selection": "おすすめ", "view_ranking": "ランキング →",
            "language_schools": "韓国語学堂", "top_universities": "主要大学", "view_all": "すべて見る →",
            "essential_guides": "留学ガイド", "school_badge": "語学堂", "univ_badge": "大学",
            "contact_fee": "学費問合せ", "yearly": "年間", "search_placeholder": "大学を検索...",
            "all_schools": "すべての語学堂", "back_to_map": "地図に戻る", "back_to_list": "一覧に戻る",
            "global_programs": "グローバルプログラム", "national_private": "公式機関",
            "view_all_schools": "語学堂一覧 →", "view_all_univs": "大学一覧 →"
        }
    if lang == "__unused_kr__":
        return {
            "featured_title": "추천 컬렉션",'''
    u = u.replace('    if lang == "kr":\n        return {\n            "featured_title": "추천 컬렉션",', new_ui.replace('if lang == "ja":', 'if lang == "kr":', 1) if 'if lang == "kr":' in u else old_ui)
    # Simpler: direct replace get_ui_text function body for kr->ja
    u = u.replace('if lang == "kr":', 'if lang == "ja":')
    u = u.replace('"language_schools": "일본어 어학원"', '"language_schools": "韓国語学堂"')
    u = u.replace('"top_universities": "주요 대학교"', '"top_universities": "主要大学"')
    u = u.replace('"essential_guides": "유학 가이드"', '"essential_guides": "留学ガイド"')
    u = u.replace('"school_badge": "어학원"', '"school_badge": "語学堂"')
    u = u.replace('"univ_badge": "대학교"', '"univ_badge": "大学"')
    u = u.replace('"back_to_map": "지도로 돌아가기"', '"back_to_map": "地図に戻る"')
    u = u.replace('"view_all_schools": "모든 학교 보기 →"', '"view_all_schools": "語学堂一覧 →"')
    utils_path.write_text(u, encoding="utf-8")
    print("patched app/utils.py")

for tpl in (ROOT / "app/templates").glob("*.html"):
    t = tpl.read_text(encoding="utf-8")
    t = t.replace("current_lang == 'kr'", "current_lang == 'ja'")
    t = t.replace("lang == 'kr'", "lang == 'ja'")
    t = t.replace("?lang=kr", "?lang=ja")
    t = t.replace("hreflang=\"ko\"", "hreflang=\"ja\"")
    t = t.replace("'ko' if current_lang == 'ja'", "'ja' if current_lang == 'ja'")
    t = t.replace("<html lang=\"{{ 'ko' if current_lang == 'ja' else 'en' }}\">", "<html lang=\"{{ 'ja' if current_lang == 'ja' else 'en' }}\">")
    t = t.replace("JP Campus", "KR Campus")
    t = t.replace("name_ja", "name_ko")
    t = t.replace("🇰🇷 KR", "🇯🇵 JA")
    t = t.replace("okramen.net", "jpcampus.net")
    t = t.replace("okonsen.net", "jpcampus.net")
    t = t.replace("okcaddie.net", "jpcampus.net")
    tpl.write_text(t, encoding="utf-8")
    print(f"patched {tpl.name}")

# deploy + cloudbuild
patch_file("deploy.sh", [
    ("https://jpcampus.net", "https://krcampus.net"),
    ("JPCampus", "KRCampus"),
    ("scripts/3.create_korean_content.py", "scripts/3.create_japanese_content.py"),
    ("scripts/1.collect_universities.py", "scripts/1.collect_universities.py\n        python3 scripts/1.collect_language_schools.py"),
])
patch_file("cloudbuild.yaml", [
    ("jpcampus", "krcampus"),
    ("jpcampus.net", "krcampus.net"),
])
patch_file("scripts/2.generate_ai_guides.py", [
    ("study in Japan", "study in Korea"),
    ("Study in Japan", "Study in Korea"),
    ("Japan expert", "Korea study abroad expert"),
])

print("done")
