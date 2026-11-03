import json

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.analytics import client_id_for_request, track_event
from app.compare import build_compare_export, compare_fee_value, prepare_compare_items
from app.content_loader import load_guides, load_school_data, load_stay_data
from app.content_new import enrich_items
from app.content_service import load_guide_post, load_school_post, load_stay_post, render_markdown
from app.a8_affiliate import a8_banners_context, a8_housing_context
from app.amazon_affiliate import amazon_context, kind_for as amazon_kind_for
from app.affiliate import affiliate_context
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
from app.settings import (
    DOMAIN,
    FAMILY_SITE_ID,
    KRCAMPUS_GOOGLE_MAPS_API_KEY,
    SCHOOL_ID_ALIASES,
    SHOW_STAYS_UI,
    SITE_NAME,
)
from app.social_share import share_context
from app.thumbnails import assign_thumbnails, diversify_guide_thumbnails, resolve_guide_detail_thumbnail

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

    try:
        post, _ = load_school_post(school_id, lang)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="School content file not found")

    content_html = render_markdown(post.content)
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
        **affiliate_context(school_id, lang=lang, item_type=item_type),
        **a8_banners_context(slug=school_id, lang=lang, item_type=item_type),
        **amazon_context(kind=amazon_kind_for(school_id, item_type), lang=lang),
        **ctx,
    })


@router.get("/guide/{slug}", response_class=HTMLResponse)
async def guide_detail(request: Request, slug: str, lang: str = Query("en")):
    try:
        post, _ = load_guide_post(slug, lang)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Guide content file not found")

    content_html = render_markdown(post.content)
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
        **affiliate_context(slug, lang=lang),
        **a8_banners_context(slug=slug, lang=lang, item_type="guide"),
        **amazon_context(kind=amazon_kind_for(slug, "guide"), lang=lang),
        **inject_family_context(FAMILY_SITE_ID, lang),
        **ctx,
    })


@router.get("/stay/{stay_id}", response_class=HTMLResponse)
async def stay_detail(request: Request, stay_id: str, lang: str = Query("en")):
    try:
        post, _ = load_stay_post(stay_id, lang)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Stay content file not found")

    content_html = render_markdown(post.content)
    item = dict(post.metadata)
    item.setdefault("id", stay_id)
    assign_thumbnails([item], "stay")

    basic = item.get("basic_info") or {}
    share_title = item.get("title") or basic.get("name_en") or basic.get("name_ko") or "Student Housing"
    ctx = share_context(DOMAIN, "stay", stay_id, share_title, lang)

    stay_type = item.get("stay_type", "guesthouse")
    ui = get_ui_text(lang)
    stay_type_label = ui.get(f"stay_type_{stay_type}", stay_type)

    return templates.TemplateResponse(request, "detail.html", {
        "item": item, "item_type": "stay",
        "stay_type_label": stay_type_label,
        "content_body": content_html, "current_lang": lang, "ui": ui,
        "show_stays_ui": SHOW_STAYS_UI,
        "canonical_url": build_canonical_url(f"/stay/{stay_id}", lang),
        "hreflang_urls": build_hreflang_urls(f"/stay/{stay_id}"),
        "updated_at": default_updated_at(),
        "related_schools": pick_related_schools(item, lang),
        "related_guides": pick_related_guides(item, "stay", lang),
        "meta_title": build_meta_title(item.get("seo_title") or share_title, lang),
        "meta_description": build_meta_description(
            item.get("seo_description") or item.get("description", ""),
            "Foreigner-friendly student housing near Korean language schools and universities.",
        ),
        "faq_json_ld": None,
        "cross_site_links": detail_cross_links(lang, item),
        **inject_family_context(FAMILY_SITE_ID, lang),
        **affiliate_context(stay_id, lang=lang, item_type="stay"),
        **a8_housing_context(page_kind="stay_detail", lang=lang, stay_id=stay_id),
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


@router.get("/stays", response_class=HTMLResponse)
async def stay_list(request: Request, lang: str = Query("en")):
    if not SHOW_STAYS_UI:
        return RedirectResponse(url=f"/guide?lang={lang}", status_code=302)

    stays_data, _ = load_stay_data(lang)
    stays = enrich_items(assign_thumbnails(stays_data, "stay"))
    ui = get_ui_text(lang)
    return templates.TemplateResponse(request, "list.html", {
        "items": stays, "item_type": "stay",
        "title": ui["stays_list_title"],
        "description": ui["stays_list_desc"],
        "current_lang": lang, "ui": ui,
        "show_stays_ui": True,
        "canonical_url": build_canonical_url("/stays", lang),
        "hreflang_urls": build_hreflang_urls("/stays"),
        "updated_at": default_updated_at(),
        "meta_title": build_meta_title(ui["meta_stays_title"], lang),
        "meta_description": build_meta_description(
            ui["meta_stays_desc"],
            "Browse student housing options across Korea.",
        ),
        **a8_housing_context(page_kind="stays_list", lang=lang),
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

    await track_event(
        client_id_for_request(request),
        "compare_view",
        {"ids": ",".join(item.get("id", "") for item in selected), "count": len(selected)},
    )

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
    ui = get_ui_text(lang)
    return templates.TemplateResponse(request, "about.html", {
        "canonical_url": build_canonical_url("/about", lang),
        "current_lang": lang,
        "ui": ui,
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
    ui = get_ui_text(lang)
    return templates.TemplateResponse(request, "contact.html", {
        "canonical_url": build_canonical_url("/contact", lang),
        "current_lang": lang,
        "ui": ui,
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
    ui = get_ui_text(lang)
    return templates.TemplateResponse(request, "policy.html", {
        "canonical_url": build_canonical_url("/policy", lang),
        "current_lang": lang,
        "ui": ui,
        "hreflang_urls": build_hreflang_urls("/policy"),
        "updated_at": default_updated_at(),
        "meta_title": build_meta_title("Privacy Policy", lang),
        "meta_description": build_meta_description(
            "Read how KR Campus handles privacy, cookies, and data usage.",
            "Read how KR Campus handles privacy, cookies, and data usage.",
        ),
    })
