from datetime import datetime, timezone

from app.settings import DOMAIN, SITE_NAME


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


def build_meta_title(raw_title: str, lang: str = "en", suffix: str | None = None) -> str:
    year = datetime.now(timezone.utc).strftime("%Y")
    base = f"[{year}] {raw_title}"
    title = f"{base} | {suffix or SITE_NAME}"
    return title[:68]


def build_meta_description(raw_description: str, fallback: str) -> str:
    text = (raw_description or "").strip() or fallback
    if len(text) <= 155:
        return text
    return f"{text[:152].rstrip()}..."
