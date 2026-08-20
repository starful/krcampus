from datetime import datetime, timezone
from xml.sax.saxutils import escape as xml_escape

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse, Response

from app.content_loader import load_guides, load_school_data
from app.context import content_lastmod
from app.seo.meta import build_hreflang_urls
from app.settings import ADS_TXT_CONTENT, DOMAIN

router = APIRouter()


@router.api_route("/ads.txt", methods=["GET", "HEAD"], response_class=PlainTextResponse)
async def ads_txt():
    return ADS_TXT_CONTENT


@router.get("/sitemap.xml", response_class=PlainTextResponse)
async def sitemap():
    entries: list[dict[str, str]] = []

    def add_entry(path: str, lastmod: str, changefreq: str, priority: str):
        alternates = build_hreflang_urls(path)
        for loc in (alternates["en"], alternates["ja"]):
            entries.append({
                "loc": loc,
                "lastmod": lastmod,
                "changefreq": changefreq,
                "priority": priority,
                "alt_en": alternates["en"],
                "alt_ja": alternates["ja"],
                "alt_default": alternates["x-default"],
            })

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    add_entry("/", today, "daily", "1.0")
    for page in ["/about", "/guide", "/schools", "/universities", "/contact", "/policy", "/compare"]:
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


@router.get("/robots.txt", response_class=PlainTextResponse)
async def robots():
    return f"User-agent: *\nAllow: /\nSitemap: {DOMAIN}/sitemap.xml"
