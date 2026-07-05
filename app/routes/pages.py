import json
import os

import frontmatter
import markdown
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.compare import build_compare_export, compare_fee_value, prepare_compare_items
from app.content_loader import load_guides, load_school_data
from app.content_new import enrich_items
from app.context import (
    default_updated_at,
    detail_cross_links,
    templates,
)
from app.family_sites import inject_family_context
from app.filters import (
    calculate_tag_counts,
    get_category_filters,
    get_region_filters,
    get_school_feature_filters,
)
from app.i18n import get_ui_text
from app.related import pick_compare_guides, pick_related_guides, pick_related_schools
from app.seo.faq_schema import guide_faq_json_ld
from app.seo.meta import build_canonical_url, build_hreflang_urls, build_meta_description, build_meta_title
from app.seo.serp_overrides import apply_guide_serp_overrides
from app.settings import DOMAIN, FAMILY_SITE_ID, KRCAMPUS_GOOGLE_MAPS_API_KEY, SCHOOL_ID_ALIASES, SITE_NAME
from app.social_share import share_context
from app.thumbnails import assign_thumbnails, diversify_guide_thumbnails, resolve_guide_detail_thumbnail
from app.paths import CONTENT_DIR

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request, lang: str = Query("en"), view: str = Query("all")):
    if view not in ("all", "school", "university"):
        view = "all"
    schools_data, updated_at = load_school_data(lang)
    all_guides = load_guides(lang)
    ui = get_ui_text(lang)

    featured_candidates = [g for g in all_guides if g.get("is_featured")]
    if not featured_candidates:
        featured_candidates = all_guides[:3]
    else:
        featured_candidates = featured_candidates[:3]
    featured_guides = enrich_items(diversify_guide_thumbnails(featured_candidates))
    featured_links = {g["link"] for g in featured_guides}

    latest_schools = enrich_items(assign_thumbnails([s for s in schools_data if s.get("category") != "university"][:6], "school"))
    latest_universities = enrich_items(assign_thumbnails([s for s in schools_data if s.get("category") == "university"][:6], "university"))
    tags_with_counts = calculate_tag_counts(schools_data)

    university_list = []
    for s in schools_data:
        if s.get("category") == "university":
            b_info = s.get("basic_info") or {}
            university_list.append({
                "name_ko": b_info.get("name_ja", ""),
                "name_en": b_info.get("name_display") or b_info.get("name_en") or "",
            })

    return templates.TemplateResponse(request, "index.html", {
        "schools_json": json.dumps({"schools": schools_data}, ensure_ascii=False),
        "maps_api_key": KRCAMPUS_GOOGLE_MAPS_API_KEY,
        "updated_at": updated_at,
        "total_schools": len(schools_data),
        "total_language_schools": len([s for s in schools_data if s.get("category") == "school"]),
        "total_universities": len([s for s in schools_data if s.get("category") == "university"]),
        "initial_view": view,
        "featured_guides": featured_guides,
        "latest_schools": latest_schools,
        "latest_universities": latest_universities,
        "latest_guides": enrich_items(diversify_guide_thumbnails([g for g in all_guides if g["link"] not in featured_links][:6])),
        "tags_with_counts": tags_with_counts,
        "university_list_json": university_list,
        "current_lang": lang,
        "ui": ui,
        "type_filters": get_category_filters(lang),
        "school_feature_filters": get_school_feature_filters(lang),
        "region_filters": get_region_filters(lang),
        "canonical_url": build_canonical_url("/", lang),
        "hreflang_urls": build_hreflang_urls("/"),
        "meta_title": build_meta_title(ui["meta_home_title"], lang),
        "meta_description": build_meta_description(ui["meta_home_desc"], ui["meta_home_desc"]),
    })


@router.get("/school/{school_id}", response_class=HTMLResponse)
async def read_school_detail(request: Request, school_id: str, lang: str = Query("en")):
    canonical_id = SCHOOL_ID_ALIASES.get(school_id, school_id)
    if canonical_id != school_id:
        return RedirectResponse(url=f"/school/{canonical_id}?lang={lang}", status_code=301)

    filename = f"{school_id}_ja.md" if lang == "ja" else f"{school_id}.md"
    md_path = os.path.join(CONTENT_DIR, filename)
    if not os.path.exists(md_path) and lang == "ja":
        md_path = os.path.join(CONTENT_DIR, f"{school_id}.md")

    if not os.path.exists(md_path):
        raise HTTPException(status_code=404, detail="School content file not found")

    post = frontmatter.load(md_path)
    content_html = markdown.markdown(post.content, extensions=["tables", "fenced_code", "nl2br"])
    item = post.metadata
    item_type = "university" if item.get("category") == "university" else "school"
    share_title = (
        item.get("title")
        or item.get("basic_info", {}).get("name_en")
        or item.get("basic_info", {}).get("name_ko")
        or item.get("basic_info", {}).get("name_ja")
        or "School Guide"
    )
    ctx = share_context(DOMAIN, "school", school_id, share_title, lang)

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
            "Compare school details, tuition clues, and student-ready preparation tips.",
        ),
        "faq_json_ld": None,
        "cross_site_links": detail_cross_links(lang, item),
        **inject_family_context(FAMILY_SITE_ID, lang),
        **ctx,
    })


@router.get("/guide/{slug}", response_class=HTMLResponse)
async def guide_detail(request: Request, slug: str, lang: str = Query("en")):
    filename = f"guide_{slug}_ja.md" if lang == "ja" else f"guide_{slug}.md"
    md_path = os.path.join(CONTENT_DIR, filename)
    if not os.path.exists(md_path) and lang == "ja":
        md_path = os.path.join(CONTENT_DIR, f"guide_{slug}.md")

    if not os.path.exists(md_path):
        raise HTTPException(status_code=404, detail="Guide content file not found")

    post = frontmatter.load(md_path)
    content_html = markdown.markdown(post.content, extensions=["tables", "fenced_code", "nl2br"])
    item = dict(post.metadata)
    item["thumbnail"] = resolve_guide_detail_thumbnail(item)

    title_raw, desc_raw = apply_guide_serp_overrides(slug, lang, item)
    share_title = title_raw or item.get("title", "Study in Korea Guide")
    ctx = share_context(DOMAIN, "guide", slug, share_title, lang)

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
            "Actionable study-in-Korea guide with practical decisions and student checklists.",
        ),
        "faq_json_ld": guide_faq_json_ld(slug, lang),
        "cross_site_links": detail_cross_links(lang, item),
        **inject_family_context(FAMILY_SITE_ID, lang),
        **ctx,
    })


@router.get("/schools", response_class=HTMLResponse)
async def school_list(request: Request, lang: str = Query("en")):
    schools_data, _ = load_school_data(lang)
    schools = enrich_items(assign_thumbnails([s for s in schools_data if s.get("category") != "university"], "school"))
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


@router.get("/universities", response_class=HTMLResponse)
async def university_list(request: Request, lang: str = Query("en")):
    schools_data, _ = load_school_data(lang)
    universities = enrich_items(assign_thumbnails([s for s in schools_data if s.get("category") == "university"], "university"))
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
            "Find university options in Korea with practical comparisons and prep guidance.",
        ),
    })


@router.get("/guide", response_class=HTMLResponse)
async def guide_list_page(request: Request, lang: str = Query("en")):
    guides = load_guides(lang)
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


@router.get("/compare", response_class=HTMLResponse)
async def compare_page(request: Request, ids: str = "", lang: str = Query("en")):
    schools_data, _ = load_school_data(lang)
    school_by_id = {s["id"]: s for s in schools_data if s.get("id")}
    id_list = [value.strip() for value in ids.split(",") if value.strip()][:3]

    selected = []
    for school_id in id_list:
        item = school_by_id.get(school_id)
        if not item:
            continue
        if selected and selected[0].get("category") != item.get("category"):
            continue
        item_type = "university" if item.get("category") == "university" else "school"
        assign_thumbnails([item], item_type)
        selected.append(item)

    fee_values = [compare_fee_value(item) for item in selected]
    fee_values = [value for value in fee_values if value is not None]
    min_fee = min(fee_values) if fee_values else None

    ui = get_ui_text(lang)
    prepared = prepare_compare_items(selected, lang)
    return templates.TemplateResponse(request, "compare.html", {
        "selected": prepared,
        "min_fee": min_fee,
        "related_guides": pick_compare_guides(prepared, lang),
        "compare_export": build_compare_export(prepared, lang, SITE_NAME),
        "current_lang": lang,
        "ui": ui,
        "canonical_url": build_canonical_url("/compare", lang),
        "hreflang_urls": build_hreflang_urls("/compare"),
        "updated_at": default_updated_at(),
        "meta_title": build_meta_title(ui["meta_compare_title"], lang),
        "meta_description": build_meta_description(
            ui["meta_compare_desc"],
            "Compare Korean language institutes and universities side by side on KR Campus.",
        ),
    })


@router.get("/about", response_class=HTMLResponse)
async def about(request: Request, lang: str = Query("en")):
    return templates.TemplateResponse(request, "about.html", {
        "canonical_url": build_canonical_url("/about", lang),
        "current_lang": lang,
        "hreflang_urls": build_hreflang_urls("/about"),
        "updated_at": default_updated_at(),
        "meta_title": build_meta_title("About KR Campus", lang),
        "meta_description": build_meta_description(
            "Learn how KR Campus helps international students choose schools in Korea.",
            "Learn how KR Campus helps international students choose schools in Korea.",
        ),
    })


@router.get("/contact", response_class=HTMLResponse)
async def contact(request: Request, lang: str = Query("en")):
    return templates.TemplateResponse(request, "contact.html", {
        "canonical_url": build_canonical_url("/contact", lang),
        "current_lang": lang,
        "hreflang_urls": build_hreflang_urls("/contact"),
        "updated_at": default_updated_at(),
        "meta_title": build_meta_title("Contact KR Campus", lang),
        "meta_description": build_meta_description(
            "Contact KR Campus for corrections, feedback, or collaboration.",
            "Contact KR Campus for corrections, feedback, or collaboration.",
        ),
    })


@router.get("/policy", response_class=HTMLResponse)
async def policy(request: Request, lang: str = Query("en")):
    return templates.TemplateResponse(request, "policy.html", {
        "canonical_url": build_canonical_url("/policy", lang),
        "current_lang": lang,
        "hreflang_urls": build_hreflang_urls("/policy"),
        "updated_at": default_updated_at(),
        "meta_title": build_meta_title("Privacy Policy", lang),
        "meta_description": build_meta_description(
            "Read how KR Campus handles privacy, cookies, and data usage.",
            "Read how KR Campus handles privacy, cookies, and data usage.",
        ),
    })
