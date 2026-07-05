import os

from fastapi import APIRouter, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response

from app.context import templates
from app.paths import STATIC_DIR
from app.seo.meta import build_meta_description, build_meta_title
from app.seo.serp_overrides import apply_guide_serp_overrides
from app.settings import DOMAIN, GCS_IMAGE_BASE, _LOCAL_IMAGE_NAMES
from app.social_share import (
    card_page_path,
    detail_page_path,
    fetch_social_jpeg,
    load_guide_item,
    load_school_item,
    resolve_thumbnail_url,
    share_context,
)

router = APIRouter()


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


@router.api_route("/favicon.ico", methods=["GET", "HEAD"], include_in_schema=False)
async def favicon():
    return FileResponse(os.path.join(STATIC_DIR, "img", "favicon.ico"))


@router.api_route("/favicon-32x32.png", methods=["GET", "HEAD"], include_in_schema=False)
async def favicon_32():
    return FileResponse(os.path.join(STATIC_DIR, "img", "favicon-32x32.png"))


@router.api_route("/favicon-48x48.png", methods=["GET", "HEAD"], include_in_schema=False)
async def favicon_48():
    return FileResponse(os.path.join(STATIC_DIR, "img", "favicon-48x48.png"))


@router.api_route("/apple-touch-icon.png", methods=["GET", "HEAD"], include_in_schema=False)
async def apple_touch_icon():
    return FileResponse(os.path.join(STATIC_DIR, "img", "apple-touch-icon.png"))


@router.api_route("/android-chrome-192x192.png", methods=["GET", "HEAD"], include_in_schema=False)
async def android_chrome_192():
    return FileResponse(os.path.join(STATIC_DIR, "img", "android-chrome-192x192.png"))


@router.api_route("/android-chrome-512x512.png", methods=["GET", "HEAD"], include_in_schema=False)
async def android_chrome_512():
    return FileResponse(os.path.join(STATIC_DIR, "img", "android-chrome-512x512.png"))


@router.api_route("/site.webmanifest", methods=["GET", "HEAD"], include_in_schema=False)
async def site_webmanifest():
    return FileResponse(os.path.join(STATIC_DIR, "site.webmanifest"), media_type="application/manifest+json")


@router.api_route("/social/{image_key}.jpg", methods=["GET", "HEAD"])
async def social_image(image_key: str, lang: str = Query("en")):
    static_path = _static_social_path(image_key)
    if static_path:
        return FileResponse(static_path, media_type="image/jpeg", headers=_social_image_headers())
    if image_key.startswith("guide-"):
        return _render_social_image("guide", image_key[6:], lang)
    return _render_social_image("school", image_key, lang)


@router.api_route("/card/school/{school_id}", methods=["GET", "HEAD"], response_class=HTMLResponse)
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


@router.api_route("/card/guide/{slug}", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def guide_social_card(request: Request, slug: str, lang: str = Query("en")):
    item = load_guide_item(slug, lang)
    title_raw, desc_raw = apply_guide_serp_overrides(slug, lang, item)
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


@router.get("/static/images/{filename:path}")
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
