"""SNS share bar + X/OG card helpers (same-domain social images)."""
from __future__ import annotations

import io
import os
import re
import urllib.request
from urllib.parse import quote

import frontmatter

from app.utils import CONTENT_DIR, assign_thumbnails, resolve_guide_detail_thumbnail

SOCIAL_CARD_VERSION = "1"
_FETCH_UA = "KRCampus/1.0 (+https://krcampus.net)"


def social_image_path(kind: str, identifier: str) -> str:
    if kind == "guide":
        safe = "guide-" + re.sub(r"[^a-z0-9_-]", "", identifier.lower())
    else:
        safe = re.sub(r"[^a-z0-9_-]", "", identifier.lower())
    return f"/social/{safe}.jpg"


def social_image_url(domain: str, kind: str, identifier: str) -> str:
    return f"{domain.rstrip('/')}{social_image_path(kind, identifier)}"


def detail_page_path(kind: str, identifier: str, lang: str) -> str:
    segment = "school" if kind == "school" else "guide"
    path = f"/{segment}/{identifier}"
    return f"{path}?lang=ja" if lang == "ja" else path


def card_page_path(kind: str, identifier: str, lang: str) -> str:
    params = {"sc": SOCIAL_CARD_VERSION}
    if lang == "ja":
        params["lang"] = "ja"
    query = "&".join(f"{key}={value}" for key, value in params.items())
    return f"/card/{kind}/{identifier}?{query}"


def share_context(domain: str, kind: str, identifier: str, title: str, lang: str) -> dict:
    page = detail_page_path(kind, identifier, lang)
    share_url = f"{domain.rstrip('/')}{page}"
    if lang == "ja":
        share_tweet = f"{title} — KR Campus"
    else:
        share_tweet = f"{title} — Study in Korea on KR Campus"
    return {
        "share_id": identifier,
        "share_url": share_url,
        "share_url_x": f"{domain.rstrip('/')}{card_page_path(kind, identifier, lang)}",
        "share_tweet": share_tweet,
        "share_lang": lang,
        "og_page_url": share_url,
        "og_image_abs": social_image_url(domain, kind, identifier),
        "og_image_width": 1200,
        "og_image_height": 630,
        "linkedin_inspector_url": (
            f"https://www.linkedin.com/post-inspector/inspect/{quote(share_url, safe='')}"
        ),
    }


def resolve_thumbnail_url(
    domain: str,
    item: dict,
    item_type: str,
    *,
    guide_slug: str | None = None,
    gcs_base: str = "",
) -> str:
    thumb = (item.get("thumbnail") or "").strip()
    if thumb.startswith("http"):
        return thumb
    if thumb.startswith("/static/images/") and gcs_base:
        return f"{gcs_base.rstrip('/')}/{thumb.rsplit('/', 1)[-1]}"
    if thumb.startswith("/"):
        return f"{domain.rstrip('/')}{thumb}"
    if item_type == "guide":
        return resolve_guide_detail_thumbnail(item)
    category = "university" if item_type == "university" else "school"
    row = {"id": item.get("id") or "default_id"}
    assign_thumbnails([row], category)
    return row["thumbnail"]


def load_school_item(school_id: str, lang: str) -> tuple[dict, str]:
    filename = f"{school_id}_ja.md" if lang == "ja" else f"{school_id}.md"
    md_path = os.path.join(CONTENT_DIR, filename)
    if not os.path.exists(md_path) and lang == "ja":
        md_path = os.path.join(CONTENT_DIR, f"{school_id}.md")
    if not os.path.exists(md_path):
        raise FileNotFoundError(school_id)
    post = frontmatter.load(md_path)
    item = dict(post.metadata)
    item["id"] = school_id
    item_type = "university" if item.get("category") == "university" else "school"
    assign_thumbnails([item], item_type)
    return item, item_type


def load_guide_item(slug: str, lang: str) -> dict:
    filename = f"guide_{slug}_ja.md" if lang == "ja" else f"guide_{slug}.md"
    md_path = os.path.join(CONTENT_DIR, filename)
    if not os.path.exists(md_path) and lang == "ja":
        md_path = os.path.join(CONTENT_DIR, f"guide_{slug}.md")
    if not os.path.exists(md_path):
        raise FileNotFoundError(slug)
    post = frontmatter.load(md_path)
    item = dict(post.metadata)
    item.setdefault("id", slug)
    item["thumbnail"] = resolve_guide_detail_thumbnail(item)
    return item


def jpeg_bytes(img) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88, optimize=True)
    return buf.getvalue()


def fetch_social_jpeg(source_url: str) -> bytes:
    req = urllib.request.Request(source_url, headers={"User-Agent": _FETCH_UA})
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read()
        if not raw:
            raise ValueError("empty image")
    try:
        from PIL import Image, ImageOps

        img = Image.open(io.BytesIO(raw)).convert("RGB")
        return jpeg_bytes(ImageOps.fit(img, (1200, 630), Image.Resampling.LANCZOS))
    except Exception:
        return raw


def static_social_image_key(kind: str, identifier: str) -> str:
    if kind == "guide":
        return "guide-" + re.sub(r"[^a-z0-9_-]", "", identifier.lower())
    return re.sub(r"[^a-z0-9_-]", "", identifier.lower())
