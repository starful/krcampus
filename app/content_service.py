"""Shared markdown path resolution, loading, and HTML rendering."""

from __future__ import annotations

import os

import frontmatter
import markdown

from app.paths import CONTENT_DIR

MARKDOWN_EXTENSIONS = ["tables", "fenced_code", "nl2br"]


def resolve_content_path(base_name: str, lang: str, *, fallback_en: bool = True) -> str | None:
    """Resolve `{base_name}.md` or `{base_name}_ja.md`, with optional EN fallback for JA."""
    if lang == "ja":
        ja_path = os.path.join(CONTENT_DIR, f"{base_name}_ja.md")
        if os.path.exists(ja_path):
            return ja_path
        if fallback_en:
            en_path = os.path.join(CONTENT_DIR, f"{base_name}.md")
            if os.path.exists(en_path):
                return en_path
        return None

    path = os.path.join(CONTENT_DIR, f"{base_name}.md")
    return path if os.path.exists(path) else None


def resolve_school_path(school_id: str, lang: str) -> str | None:
    return resolve_content_path(school_id, lang)


def resolve_guide_path(slug: str, lang: str) -> str | None:
    return resolve_content_path(f"guide_{slug}", lang)


def load_post(md_path: str):
    return frontmatter.load(md_path)


def render_markdown(content: str) -> str:
    return markdown.markdown(content, extensions=MARKDOWN_EXTENSIONS)


def load_school_post(school_id: str, lang: str):
    md_path = resolve_school_path(school_id, lang)
    if not md_path:
        raise FileNotFoundError(school_id)
    return load_post(md_path), md_path


def load_guide_post(slug: str, lang: str):
    md_path = resolve_guide_path(slug, lang)
    if not md_path:
        raise FileNotFoundError(slug)
    return load_post(md_path), md_path
