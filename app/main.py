# app/main.py
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, PlainTextResponse, Response, FileResponse, RedirectResponse
import json
import os
import frontmatter
import markdown
from dotenv import load_dotenv
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

# 분리된 유틸 및 API 라우터 임포트
from app.settings import KRCAMPUS_GOOGLE_MAPS_API_KEY
from app.utils import (
    calculate_tag_counts, assign_thumbnails, get_ui_text, get_quick_filters,
    load_school_data, load_guides, resolve_guide_detail_thumbnail, diversify_guide_thumbnails,
    STATIC_DIR, CONTENT_DIR, TEMPLATES_DIR
)
from app.content_new import enrich_items
from app.reactions import router as reactions_router
from app.social_share import (
    card_page_path,
    detail_page_path,
    fetch_social_jpeg,
    load_guide_item,
    load_school_item,
    resolve_thumbnail_url,
    share_context,
)
from app.family_sites import cross_links_for, inject_family_context

FAMILY_SITE_ID = "krcampus"

load_dotenv()
app = FastAPI()

if not os.path.exists(CONTENT_DIR): os.makedirs(CONTENT_DIR)

_LOCAL_IMAGE_NAMES = {"logo.png", "logo.svg", "favicon.ico", "og_image.png", "pin-school.png", "pin-univ.png"}


@app.get("/static/images/{filename:path}")
async def serve_gcs_images(filename: str):
    """School photos live on GCS; local repo only keeps logos/pins."""
    if filename in _LOCAL_IMAGE_NAMES or filename.startswith("pin-"):
        local = os.path.join(STATIC_DIR, "images", filename)
        if os.path.isfile(local):
            return FileResponse(local)
        local = os.path.join(STATIC_DIR, "img", filename)
        if os.path.isfile(local):
            return FileResponse(local)
    return RedirectResponse(f"{GCS_IMAGE_BASE}/{filename}", status_code=302)


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)
templates.env.globals["inject_family_context"] = inject_family_context
templates.env.globals["FAMILY_SITE_ID"] = FAMILY_SITE_ID


def _campus_address(item: dict) -> str | None:
    basic = item.get("basic_info") or {}
    return basic.get("address") or item.get("address")


def _detail_cross_links(lang: str, item: dict | None = None, categories: list | None = None):
    address = _campus_address(item) if item else None
    return cross_links_for(
        FAMILY_SITE_ID,
        lang,
        address=address,
        categories=categories,
    )

DOMAIN = os.getenv("SITE_DOMAIN", "https://krcampus.net").rstrip("/")
GCS_IMAGE_BASE = os.getenv(
    "GCS_IMAGE_BASE",
    "https://storage.googleapis.com/ok-project-assets/krcampus",
)
ADS_TXT_CONTENT = os.getenv(
    "ADS_TXT_CONTENT",
    "google.com, pub-8780435268193938, DIRECT, f08c47fec0942fa0"
)
GA_MEASUREMENT_ID = os.getenv("GA_MEASUREMENT_ID", "G-ZTC8BNMCRR")
ADSENSE_CLIENT_ID = os.getenv("ADSENSE_CLIENT_ID", "ca-pub-8780435268193938")
REDIRECT_MAP_PATH = Path(BASE_DIR := os.path.dirname(os.path.abspath(__file__))) / "redirects.json"


def load_redirect_map() -> dict[str, str]:
    if not REDIRECT_MAP_PATH.exists():
        return {}
    try:
        with open(REDIRECT_MAP_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return {str(k): str(v) for k, v in data.items()}
    except Exception:
        pass
    return {}


REDIRECT_MAP = load_redirect_map()
templates.env.globals["ga_measurement_id"] = GA_MEASUREMENT_ID
templates.env.globals["adsense_client_id"] = ADSENSE_CLIENT_ID
templates.env.globals["site_url"] = DOMAIN


def build_canonical_url(path: str, lang: str | None = None) -> str:
    canonical = f"{DOMAIN}{path}"
    if lang in ("ja", "kr"):
        return f"{canonical}?lang={lang}"
    return canonical


def build_hreflang_urls(path: str) -> dict[str, str]:
    return {
        "en": build_canonical_url(path),
        "ja": build_canonical_url(path, "ja"),
        "x-default": build_canonical_url(path),
    }


def default_updated_at() -> str:
    _, updated_at = load_school_data("en")
    return updated_at or datetime.now(timezone.utc).strftime("%Y-%m-%d")


def site_stats(lang: str = "en") -> dict[str, int | str]:
    schools, updated_at = load_school_data(lang)
    return {
        "total_schools": len(schools),
        "updated_at": updated_at or default_updated_at(),
    }


templates.env.globals["site_stats"] = site_stats


def content_lastmod(*filenames: str) -> str:
    timestamps: list[float] = []
    for filename in filenames:
        filepath = os.path.join(CONTENT_DIR, filename)
        if os.path.exists(filepath):
            timestamps.append(os.path.getmtime(filepath))
    if not timestamps:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return datetime.fromtimestamp(max(timestamps), timezone.utc).strftime("%Y-%m-%d")


def _redirect_target(path: str) -> str | None:
    normalized = path.rstrip("/") or "/"
    target = REDIRECT_MAP.get(normalized) or REDIRECT_MAP.get(f"{normalized}/")
    if not target:
        return None
    if not target.startswith("/"):
        return f"/{target}"
    if target == normalized:
        return None
    return target


def build_meta_title(raw_title: str, lang: str = "en", suffix: str = "KR Campus") -> str:
    year = datetime.now(timezone.utc).strftime("%Y")
    base = f"[{year}] {raw_title}"
    title = f"{base} | {suffix}"
    return title[:68]


def build_meta_description(raw_description: str, fallback: str) -> str:
    text = (raw_description or "").strip() or fallback
    if len(text) <= 155:
        return text
    return f"{text[:152].rstrip()}..."


# GSC에서 CTR이 이미 강한 가이드는 메타/구조화 데이터를 건드리지 않음.
_HIGH_CTR_GUIDE_SLUGS = frozenset({"coe-denial", "university-clubs"})

# 저CTR·고노출 위주 SERP 메타만 덮어씀 (slug, "en"|"kr").
_GUIDE_SERP_OVERRIDES: dict[tuple[str, str], dict[str, str]] = {
    ("amazon-prime-student", "en"): {
        "title": "Amazon Prime Student Japan: Price, Benefits & Eligibility (2026)",
        "description": (
            "Prime Student Japan pricing vs regular Prime, shipping benefits, Prime Video, "
            "student eligibility, and whether it saves money for international students."
        ),
    },
    ("amazon-prime-student", "kr"): {
        "title": "일본 아마존 프라임 스튜던트: 가격·혜택·가입 조건 (2026)",
        "description": (
            "일반 프라임 대비 학생 요금, 배송·영상 혜택, 유학생 가입 시 확인할 조건을 "
            "짧게 비교합니다."
        ),
    },
    ("sim-card-guide", "kr"): {
        "title": "韓国留学생 SIM·휴대폰: 통신사·알뜰폰(MVNO) 비교와 개통 절차",
        "description": (
            "docomo/Softbank/KDDI와 MVNO 특징, 유학생에게 맞는 요금제 고르는 기준, "
            "개통 시 준비물을 정리했습니다."
        ),
    },
    ("eju-subjects", "en"): {
        "title": "EJU Subject Tests: Japan & World, Math, Science — How to Choose (2026)",
        "description": (
            "Pick EJU subjects with admissions in mind: syllabus scope, study order, and how "
            "TOPIK, Science, and Math scores fit university requirements."
        ),
    },
}


def _guide_lang_key(lang: str) -> str:
    return "kr" if lang == "ja" else "en"


def _apply_guide_serp_overrides(slug: str, lang: str, item: dict) -> tuple[str, str]:
    if slug in _HIGH_CTR_GUIDE_SLUGS:
        title = item.get("title", "Study in Korea Guide")
        desc = item.get("description", "")
        return title, desc
    lk = _guide_lang_key(lang)
    ov = _GUIDE_SERP_OVERRIDES.get((slug, lk))
    if not ov:
        return item.get("title", "Study in Korea Guide"), item.get("description", "")
    return ov.get("title", item.get("title", "")), ov.get("description", item.get("description", ""))


def _guide_faq_json_ld(slug: str, lang: str) -> str | None:
    if slug in _HIGH_CTR_GUIDE_SLUGS:
        return None
    lk = _guide_lang_key(lang)
    key = (slug, lk)
    faq_map: dict[tuple[str, str], list[tuple[str, str]]] = {
        ("housing", "en"): [
            (
                "What are the main housing options for international students in Japan?",
                "Most students choose between school dormitories (ryo), share houses, or private apartments. "
                "Each differs in upfront costs, flexibility, and commute time.",
            ),
            (
                "Which housing type usually has the lowest move-in cost?",
                "School dormitories often have lower upfront costs than private apartments, but availability and rules vary by school.",
            ),
            (
                "What should I check before signing a rental contract in Japan?",
                "Review key money (reikin), deposit (shikikin), renewal fees, fire insurance, and cancellation terms with your school or agent.",
            ),
        ],
        ("housing", "kr"): [
            (
                "韓国留学생 주거는 어떤 선택지가 있나요?",
                "기숙사(寮), 쉐어하우스, 자취(원룸·아파트)가 대표적이며 초기비용·통학·규칙이 서로 다릅니다.",
            ),
            (
                "초기비용을 줄이려면 어떤 유형이 유리할까요?",
                "학교 기숙사는 원룸 대비 초기비용 부담이 적은 경우가 많지만, 공실과 규칙을 먼저 확인해야 합니다.",
            ),
            (
                "계약 전 꼭 확인해야 할 항목은 무엇인가요?",
                "礼金·敷金·更新料·火災保険·解約条件 등을 서면으로 확인하고, 학교 안내 또는 공인 중개와 절차를 맞추는 것이 안전합니다.",
            ),
        ],
        ("amazon-prime-student", "en"): [
            (
                "How much does Amazon Prime Student cost in Japan?",
                "Pricing is lower than regular Prime; compare monthly and annual student plans against how often you ship and stream.",
            ),
            (
                "Who can sign up for Amazon Prime Student in Japan?",
                "Eligibility depends on Amazon’s student verification rules; confirm your student status and account region requirements before subscribing.",
            ),
        ],
        ("amazon-prime-student", "kr"): [
            (
                "일본에서 아마존 프라임 스튜던트는 얼마인가요?",
                "일반 프라임보다 낮은 월/연 요금이 특징이며, 배송·스트리밍 이용 빈도에 따라 이득이 달라집니다.",
            ),
            (
                "유학생도 가입할 수 있나요?",
                "아마존의 학생 인증·계정 지역 조건을 충족해야 하므로, 가입 전 요건을 확인하는 것이 좋습니다.",
            ),
        ],
        ("sim-card-guide", "kr"): [
            (
                "유학생은 일본에서 어떤 통신 선택지가 있나요?",
                "대형 통신사(MNO)와 저가 알뜰폰(MVNO) 중에서 데이터·통화 필요량과 체류 기간에 맞게 고를 수 있습니다.",
            ),
            (
                "개통할 때 무엇을 준비해야 하나요?",
                "여권·재류카드 등 신분과 주소 확인 서류가 필요한 경우가 많습니다. 절차는 회사·매장마다 다릅니다.",
            ),
        ],
        ("eju-subjects", "en"): [
            (
                "Which EJU subject tests should I take?",
                "Choose subjects based on each university program’s requirements, then align your study plan to the official syllabus scope.",
            ),
            (
                "Is Japan and the World required for every university?",
                "Requirements vary by school and faculty; always verify the latest admissions bulletin for your target programs.",
            ),
        ],
    }
    rows = faq_map.get(key)
    if not rows:
        return None
    entities = []
    for q, a in rows:
        entities.append(
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
        )
    payload = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": entities}
    return json.dumps(payload, ensure_ascii=False)


def pick_related_guides(item: dict, item_type: str, lang: str, limit: int = 4) -> list[dict]:
    guides = load_guides(lang)
    source_text = ""
    if item_type == "guide":
        source_text = f"{item.get('title', '')} {item.get('description', '')}".lower()
    else:
        basic = item.get("basic_info", {}) or {}
        source_text = f"{basic.get('name_en', '')} {basic.get('address', '')}".lower()

    city_keywords = ["tokyo", "osaka", "kyoto", "nagoya", "fukuoka", "hokkaido", "japan"]
    matched = [kw for kw in city_keywords if kw in source_text]
    related = []
    for guide in guides:
        guide_text = f"{guide.get('title', '')} {guide.get('description', '')}".lower()
        if any(kw in guide_text for kw in matched):
            related.append(guide)
    if len(related) < limit:
        existing_links = {g.get("link") for g in related}
        for guide in guides:
            if guide.get("link") not in existing_links:
                related.append(guide)
            if len(related) >= limit:
                break
    return related[:limit]


def pick_related_schools(item: dict, lang: str, limit: int = 4) -> list[dict]:
    schools, _ = load_school_data(lang)
    source_text = f"{item.get('title', '')} {item.get('description', '')}".lower()
    wants_university = "university" in source_text or "eju" in source_text
    wants_school = "language school" in source_text or "jlpt" in source_text
    city_keywords = ["東京", "大阪", "京都", "名古屋", "福岡", "tokyo", "osaka", "kyoto", "nagoya", "fukuoka"]

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
        if any(kw in source_text for kw in ["tokyo", "東京"]) and not ("tokyo" in address_lower or "東京都" in address):
            continue
        if any(kw in source_text for kw in ["osaka", "大阪"]) and not ("osaka" in address_lower or "大阪府" in address):
            continue

        if any(kw in source_text for kw in city_keywords):
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


@app.middleware("http")
async def legacy_redirect_middleware(request: Request, call_next):
    response = await call_next(request)
    if response.status_code != 404:
        return response
    if request.url.path.startswith("/api") or request.url.path.startswith("/static"):
        return response

    target = _redirect_target(request.url.path)
    if not target:
        return response

    query = request.url.query
    redirect_url = f"{target}?{query}" if query and "?" not in target else target
    return RedirectResponse(url=redirect_url, status_code=301)

# 좋아요/싫어요 API 연결
app.include_router(reactions_router, prefix="/api")

# ==========================================
# 기본 웹 페이지 라우터 (HTML 렌더링)
# ==========================================
@app.get("/ads.txt", response_class=PlainTextResponse)
async def ads_txt(): return ADS_TXT_CONTENT

@app.get("/sitemap.xml", response_class=PlainTextResponse)
async def sitemap():
    entries: list[dict[str, str]] = []

    def add_entry(path: str, lastmod: str, changefreq: str, priority: str):
        alternates = build_hreflang_urls(path)
        entries.append({
            "loc": alternates["en"],
            "lastmod": lastmod,
            "changefreq": changefreq,
            "priority": priority,
            "alt_en": alternates["en"],
            "alt_ja": alternates["ja"],
            "alt_default": alternates["x-default"],
        })
        entries.append({
            "loc": alternates["ja"],
            "lastmod": lastmod,
            "changefreq": changefreq,
            "priority": priority,
            "alt_en": alternates["en"],
            "alt_ja": alternates["ja"],
            "alt_default": alternates["x-default"],
        })

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    add_entry("/", today, "daily", "1.0")
    for page in ["/about", "/guide", "/schools", "/universities", "/contact", "/policy"]:
        add_entry(page, today, "weekly", "0.8")

    schools_en, _ = load_school_data("en")
    for school in schools_en:
        school_id = school.get("id")
        if not school_id:
            continue
        add_entry(
            f"/school/{school_id}",
            content_lastmod(f"{school_id}.md", f"{school_id}_ja.md"),
            "weekly",
            "0.8",
        )

    guides_en = load_guides("en")
    for guide in guides_en:
        slug = guide["link"].split("/")[-1].split("?")[0]
        add_entry(
            f"/guide/{slug}",
            content_lastmod(f"guide_{slug}.md", f"guide_{slug}_ja.md"),
            "weekly",
            "0.7",
        )

    unique_entries = {(e["loc"], e["lastmod"], e["changefreq"], e["priority"]): e for e in entries}
    xml_items = []
    for entry in sorted(unique_entries.values(), key=lambda x: x["loc"]):
        xml_items.append(
            f"""
        <url>
            <loc>{xml_escape(entry["loc"])}</loc>
            <lastmod>{entry["lastmod"]}</lastmod>
            <changefreq>{entry["changefreq"]}</changefreq>
            <priority>{entry["priority"]}</priority>
            <xhtml:link rel="alternate" hreflang="en" href="{xml_escape(entry["alt_en"])}" />
            <xhtml:link rel="alternate" hreflang="ja" href="{xml_escape(entry["alt_ja"])}" />
            <xhtml:link rel="alternate" hreflang="x-default" href="{xml_escape(entry["alt_default"])}" />
        </url>"""
        )

    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
            xmlns:xhtml="http://www.w3.org/1999/xhtml">
        {''.join(xml_items)}
    </urlset>"""
    return Response(content=xml_content, media_type="application/xml")

@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots():
    return f"User-agent: *\nAllow: /\nSitemap: {DOMAIN}/sitemap.xml"

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, lang: str = Query("en")):
    schools_data, updated_at = load_school_data(lang)
    all_guides = load_guides(lang)
    ui = get_ui_text(lang)

    featured_candidates = [g for g in all_guides if g.get('is_featured')]
    if not featured_candidates:
        featured_candidates = all_guides[:3]
    else:
        featured_candidates = featured_candidates[:3]
    featured_guides = enrich_items(diversify_guide_thumbnails(featured_candidates))
    featured_links = {g["link"] for g in featured_guides}

    latest_schools = enrich_items(assign_thumbnails([s for s in schools_data if s.get('category') != 'university'][:6], "school"))
    latest_universities = enrich_items(assign_thumbnails([s for s in schools_data if s.get('category') == 'university'][:6], "university"))
    tags_with_counts = calculate_tag_counts(schools_data)
    
    # [방어 로직] basic_info가 없는 불량 데이터를 완벽하게 커버
    university_list =[]
    for s in schools_data:
        if s.get('category') == 'university':
            b_info = s.get('basic_info') or {}
            university_list.append({
                "name_ko": b_info.get('name_ja', ''),
                "name_en": b_info.get('name_display') or b_info.get('name_en') or ''
            })

    # [수정] 최신 문법: request 객체를 첫 번째 인자로 전달
    return templates.TemplateResponse(request, "index.html", {
        "schools_json": json.dumps({"schools": schools_data}, ensure_ascii=False),
        "maps_api_key": KRCAMPUS_GOOGLE_MAPS_API_KEY, 
        "updated_at": updated_at,
        "total_schools": len(schools_data),
        "featured_guides": featured_guides, 
        "latest_schools": latest_schools, 
        "latest_universities": latest_universities, 
        "latest_guides": enrich_items(diversify_guide_thumbnails([g for g in all_guides if g["link"] not in featured_links][:6])),
        "tags_with_counts": tags_with_counts, 
        "university_list_json": university_list,
        "current_lang": lang,
        "ui": ui,
        "quick_filters": get_quick_filters(lang),
        "canonical_url": build_canonical_url("/", lang),
        "hreflang_urls": build_hreflang_urls("/"),
        "meta_title": build_meta_title(ui["meta_home_title"], lang),
        "meta_description": build_meta_description(ui["meta_home_desc"], ui["meta_home_desc"]),
    })

@app.get("/school/{school_id}", response_class=HTMLResponse)
async def read_school_detail(request: Request, school_id: str, lang: str = Query("en")):
    filename = f"{school_id}_ja.md" if lang == "ja" else f"{school_id}.md"
    md_path = os.path.join(CONTENT_DIR, filename)
    if not os.path.exists(md_path) and lang == "ja":
        md_path = os.path.join(CONTENT_DIR, f"{school_id}.md")
    
    if not os.path.exists(md_path):
        raise HTTPException(status_code=404, detail="School content file not found")
    
    post = frontmatter.load(md_path)
    content_html = markdown.markdown(post.content, extensions=['tables', 'fenced_code', 'nl2br'])
    item = post.metadata
    item_type = 'university' if item.get('category') == 'university' else 'school'
    share_title = (
        item.get("title")
        or item.get("basic_info", {}).get("name_en")
        or item.get("basic_info", {}).get("name_ko")
        or item.get("basic_info", {}).get("name_ja")
        or "School Guide"
    )
    ctx = share_context(DOMAIN, "school", school_id, share_title, lang)

    # [수정] 최신 문법 적용
    return templates.TemplateResponse(request, "detail.html", { 
        "item": item, "item_type": item_type, 
        "content_body": content_html, "current_lang": lang, "ui": get_ui_text(lang),
        "canonical_url": build_canonical_url(f"/school/{school_id}", lang),
        "hreflang_urls": build_hreflang_urls(f"/school/{school_id}"),
        "updated_at": default_updated_at(),
        "related_guides": pick_related_guides(item, item_type, lang),
        "meta_title": build_meta_title(share_title, lang),
        "meta_description": build_meta_description(
            item.get("description", ""),
            "Compare school details, tuition clues, and student-ready preparation tips."
        ),
        "faq_json_ld": None,
        "cross_site_links": _detail_cross_links(lang, item),
        **inject_family_context(FAMILY_SITE_ID, lang),
        **ctx,
    })

@app.get("/guide/{slug}", response_class=HTMLResponse)
async def guide_detail(request: Request, slug: str, lang: str = Query("en")):
    filename = f"guide_{slug}_ja.md" if lang == "ja" else f"guide_{slug}.md"
    md_path = os.path.join(CONTENT_DIR, filename)
    if not os.path.exists(md_path) and lang == "ja":
        md_path = os.path.join(CONTENT_DIR, f"guide_{slug}.md")

    if not os.path.exists(md_path):
        raise HTTPException(status_code=404, detail="Guide content file not found")

    post = frontmatter.load(md_path)
    content_html = markdown.markdown(post.content, extensions=['tables', 'fenced_code', 'nl2br'])
    item = dict(post.metadata)
    item["thumbnail"] = resolve_guide_detail_thumbnail(item)

    title_raw, desc_raw = _apply_guide_serp_overrides(slug, lang, item)

    share_title = title_raw or item.get("title", "Study in Korea Guide")
    ctx = share_context(DOMAIN, "guide", slug, share_title, lang)

    # [수정] 최신 문법 적용
    return templates.TemplateResponse(request, "detail.html", { 
        "item": item, "item_type": "guide", 
        "content_body": content_html, "current_lang": lang, "ui": get_ui_text(lang),
        "canonical_url": build_canonical_url(f"/guide/{slug}", lang),
        "hreflang_urls": build_hreflang_urls(f"/guide/{slug}"),
        "updated_at": default_updated_at(),
        "related_schools": pick_related_schools(item, lang),
        "related_guides": pick_related_guides(item, "guide", lang),
        "meta_title": build_meta_title(share_title, lang),
        "meta_description": build_meta_description(
            desc_raw,
            "Actionable study-in-Korea guide with practical decisions and student checklists."
        ),
        "faq_json_ld": _guide_faq_json_ld(slug, lang),
        "cross_site_links": _detail_cross_links(lang, item),
        **inject_family_context(FAMILY_SITE_ID, lang),
        **ctx,
    })

@app.get("/schools", response_class=HTMLResponse)
async def school_list(request: Request, lang: str = Query("en")):
    schools_data, _ = load_school_data(lang)
    schools = assign_thumbnails([s for s in schools_data if s.get('category') != 'university'], "school")
    
    # [수정] 최신 문법 적용
    ui = get_ui_text(lang)
    return templates.TemplateResponse(request, "list.html", {
        "items": schools, "item_type": "school", 
        "title": ui["schools_list_title"],
        "description": ui["schools_list_desc"],
        "current_lang": lang, "ui": ui,
        "canonical_url": build_canonical_url("/schools", lang),
        "hreflang_urls": build_hreflang_urls("/schools"),
        "updated_at": default_updated_at(),
        "meta_title": build_meta_title(ui["meta_schools_title"], lang),
        "meta_description": build_meta_description(
            ui["meta_schools_desc"],
            "Compare language schools by city, tuition, and student lifestyle fit.",
        ),
    })

@app.get("/universities", response_class=HTMLResponse)
async def university_list(request: Request, lang: str = Query("en")):
    schools_data, _ = load_school_data(lang)
    universities = assign_thumbnails([s for s in schools_data if s.get('category') == 'university'], "university")
    
    # [수정] 최신 문법 적용
    ui = get_ui_text(lang)
    return templates.TemplateResponse(request, "list.html", {
        "items": universities, "item_type": "university", 
        "title": ui["universities_list_title"],
        "description": ui["universities_list_desc"],
        "current_lang": lang, "ui": ui,
        "canonical_url": build_canonical_url("/universities", lang),
        "hreflang_urls": build_hreflang_urls("/universities"),
        "updated_at": default_updated_at(),
        "meta_title": build_meta_title("Universities in Korea for International Students", lang),
        "meta_description": build_meta_description(
            "Find university options in Korea with practical comparisons and prep guidance.",
            "Find university options in Korea with practical comparisons and prep guidance."
        ),
    })

@app.get("/guide", response_class=HTMLResponse)
async def guide_list_page(request: Request, lang: str = Query("en")):
    guides = load_guides(lang)
    
    # [수정] 최신 문법 적용
    ui = get_ui_text(lang)
    return templates.TemplateResponse(request, "list.html", {
        "items": guides, "item_type": "guide", 
        "title": ui["guides_list_title"],
        "description": ui["guides_list_desc"],
        "current_lang": lang, "ui": ui,
        "canonical_url": build_canonical_url("/guide", lang),
        "hreflang_urls": build_hreflang_urls("/guide"),
        "updated_at": default_updated_at(),
        "meta_title": build_meta_title(ui["meta_guides_title"], lang),
        "meta_description": build_meta_description(
            ui["meta_guides_desc"],
            "Read practical guides on costs, housing, visas, and student life in Korea.",
        ),
    })

@app.get("/about", response_class=HTMLResponse)
async def about(request: Request, lang: str = Query("en")):
    return templates.TemplateResponse(request, "about.html", {
        "canonical_url": build_canonical_url("/about", lang),
        "current_lang": lang,
        "hreflang_urls": build_hreflang_urls("/about"),
        "updated_at": default_updated_at(),
        "meta_title": build_meta_title("About KR Campus", lang),
        "meta_description": build_meta_description(
            "Learn how KR Campus helps international students choose schools in Korea.",
            "Learn how KR Campus helps international students choose schools in Korea."
        ),
    })

@app.get("/contact", response_class=HTMLResponse)
async def contact(request: Request, lang: str = Query("en")):
    return templates.TemplateResponse(request, "contact.html", {
        "canonical_url": build_canonical_url("/contact", lang),
        "current_lang": lang,
        "hreflang_urls": build_hreflang_urls("/contact"),
        "updated_at": default_updated_at(),
        "meta_title": build_meta_title("Contact KR Campus", lang),
        "meta_description": build_meta_description(
            "Contact KR Campus for corrections, feedback, or collaboration.",
            "Contact KR Campus for corrections, feedback, or collaboration."
        ),
    })

@app.get("/policy", response_class=HTMLResponse)
async def policy(request: Request, lang: str = Query("en")):
    return templates.TemplateResponse(request, "policy.html", {
        "canonical_url": build_canonical_url("/policy", lang),
        "current_lang": lang,
        "hreflang_urls": build_hreflang_urls("/policy"),
        "updated_at": default_updated_at(),
        "meta_title": build_meta_title("Privacy Policy", lang),
        "meta_description": build_meta_description(
            "Read how KR Campus handles privacy, cookies, and data usage.",
            "Read how KR Campus handles privacy, cookies, and data usage."
        ),
    })

@app.api_route("/favicon.ico", methods=["GET", "HEAD"], include_in_schema=False)
async def favicon():
    return FileResponse(os.path.join(STATIC_DIR, "img", "favicon.ico"))


@app.api_route("/favicon-32x32.png", methods=["GET", "HEAD"], include_in_schema=False)
async def favicon_32():
    return FileResponse(os.path.join(STATIC_DIR, "img", "favicon-32x32.png"))


@app.api_route("/favicon-48x48.png", methods=["GET", "HEAD"], include_in_schema=False)
async def favicon_48():
    return FileResponse(os.path.join(STATIC_DIR, "img", "favicon-48x48.png"))


@app.api_route("/apple-touch-icon.png", methods=["GET", "HEAD"], include_in_schema=False)
async def apple_touch_icon():
    return FileResponse(os.path.join(STATIC_DIR, "img", "apple-touch-icon.png"))


@app.api_route("/android-chrome-192x192.png", methods=["GET", "HEAD"], include_in_schema=False)
async def android_chrome_192():
    return FileResponse(os.path.join(STATIC_DIR, "img", "android-chrome-192x192.png"))


@app.api_route("/android-chrome-512x512.png", methods=["GET", "HEAD"], include_in_schema=False)
async def android_chrome_512():
    return FileResponse(os.path.join(STATIC_DIR, "img", "android-chrome-512x512.png"))


@app.api_route("/site.webmanifest", methods=["GET", "HEAD"], include_in_schema=False)
async def site_webmanifest():
    return FileResponse(os.path.join(STATIC_DIR, "site.webmanifest"), media_type="application/manifest+json")


def _static_social_path(image_key: str) -> str | None:
    path = os.path.join(STATIC_DIR, "social", f"{image_key}.jpg")
    return path if os.path.isfile(path) else None


def _social_image_headers() -> dict[str, str]:
    return {"Cache-Control": "public, max-age=604800"}


def _render_social_image(kind: str, identifier: str, lang: str) -> Response:
    if kind == "school":
        item, item_type = load_school_item(identifier, lang)
        source = resolve_thumbnail_url(DOMAIN, item, item_type, gcs_base=GCS_IMAGE_BASE)
    else:
        item = load_guide_item(identifier, lang)
        source = resolve_thumbnail_url(
            DOMAIN, item, "guide", guide_slug=identifier, gcs_base=GCS_IMAGE_BASE
        )
    data = fetch_social_jpeg(source)
    return Response(content=data, media_type="image/jpeg", headers=_social_image_headers())


@app.api_route("/social/{image_key}.jpg", methods=["GET", "HEAD"])
async def social_image(image_key: str, lang: str = Query("en")):
    static_path = _static_social_path(image_key)
    if static_path:
        return FileResponse(static_path, media_type="image/jpeg", headers=_social_image_headers())
    if image_key.startswith("guide-"):
        return _render_social_image("guide", image_key[6:], lang)
    return _render_social_image("school", image_key, lang)


@app.api_route("/card/school/{school_id}", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def school_social_card(request: Request, school_id: str, lang: str = Query("en")):
    item, item_type = load_school_item(school_id, lang)
    title = (
        item.get("title")
        or item.get("basic_info", {}).get("name_en")
        or item.get("basic_info", {}).get("name_ko")
        or item.get("basic_info", {}).get("name_ja")
        or "KR Campus"
    )
    ctx = share_context(DOMAIN, "school", school_id, title, lang)
    page = f"{DOMAIN}{detail_page_path('school', school_id, lang)}"
    card = f"{DOMAIN}{card_page_path('school', school_id, lang)}"
    return templates.TemplateResponse(request, "social_card.html", {
        "lang": lang,
        "title": title,
        "seo_title": build_meta_title(title, lang),
        "seo_desc": build_meta_description(
            item.get("description", ""),
            "Compare school details, tuition clues, and student-ready preparation tips.",
        ),
        "page_url": page,
        "card_url": card,
        **ctx,
    })


@app.api_route("/card/guide/{slug}", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def guide_social_card(request: Request, slug: str, lang: str = Query("en")):
    item = load_guide_item(slug, lang)
    title_raw, desc_raw = _apply_guide_serp_overrides(slug, lang, item)
    title = title_raw or item.get("title", "Study in Korea Guide")
    ctx = share_context(DOMAIN, "guide", slug, title, lang)
    page = f"{DOMAIN}{detail_page_path('guide', slug, lang)}"
    card = f"{DOMAIN}{card_page_path('guide', slug, lang)}"
    return templates.TemplateResponse(request, "social_card.html", {
        "lang": lang,
        "title": title,
        "seo_title": build_meta_title(title, lang),
        "seo_desc": build_meta_description(
            desc_raw,
            "Actionable study-in-Korea guide with practical decisions and student checklists.",
        ),
        "page_url": page,
        "card_url": card,
        **ctx,
    })