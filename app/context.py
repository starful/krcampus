import os
from datetime import datetime, timezone

from fastapi.templating import Jinja2Templates

from app.content_loader import load_school_data
from app.family_sites import cross_links_for, inject_family_context
from app.paths import CONTENT_DIR, TEMPLATES_DIR
from app.settings import (
    ADSENSE_CLIENT_ID,
    DOMAIN,
    FAMILY_SITE_ID,
    GA_MEASUREMENT_ID,
)

templates = Jinja2Templates(directory=TEMPLATES_DIR)


def default_updated_at() -> str:
    _, updated_at = load_school_data("en")
    return updated_at or datetime.now(timezone.utc).strftime("%Y-%m-%d")


def site_stats(lang: str = "en") -> dict[str, int | str]:
    schools, updated_at = load_school_data(lang)
    language_schools = [s for s in schools if s.get("category") == "school"]
    universities = [s for s in schools if s.get("category") == "university"]
    return {
        "total_language_schools": len(language_schools),
        "total_universities": len(universities),
        "total_schools": len(schools),
        "updated_at": updated_at or default_updated_at(),
    }


def content_lastmod(*filenames: str) -> str:
    timestamps: list[float] = []
    for filename in filenames:
        filepath = os.path.join(CONTENT_DIR, filename)
        if os.path.exists(filepath):
            timestamps.append(os.path.getmtime(filepath))
    if not timestamps:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return datetime.fromtimestamp(max(timestamps), timezone.utc).strftime("%Y-%m-%d")


def campus_address(item: dict) -> str | None:
    basic = item.get("basic_info") or {}
    return basic.get("address") or item.get("address")


def detail_cross_links(lang: str, item: dict | None = None, categories: list | None = None):
    address = campus_address(item) if item else None
    return cross_links_for(
        FAMILY_SITE_ID,
        lang,
        address=address,
        categories=categories,
    )


def configure_templates() -> None:
    templates.env.globals["inject_family_context"] = inject_family_context
    templates.env.globals["FAMILY_SITE_ID"] = FAMILY_SITE_ID
    templates.env.globals["ga_measurement_id"] = GA_MEASUREMENT_ID
    templates.env.globals["adsense_client_id"] = ADSENSE_CLIENT_ID
    templates.env.globals["site_url"] = DOMAIN
    templates.env.globals["site_stats"] = site_stats
