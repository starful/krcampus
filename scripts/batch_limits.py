"""Per-run batch caps from okadmin pipeline env (default 3)."""
from __future__ import annotations

import os


def _positive_int(raw: str | None, default: int) -> int:
    try:
        n = int((raw or "").strip())
    except ValueError:
        n = default
    return default if n <= 0 else n


def guide_limit() -> int:
    return _positive_int(os.getenv("GUIDE_LIMIT"), 3)


def content_limit() -> int:
    """Language schools + universities (EN generation per run)."""
    return _positive_int(os.getenv("CONTENT_LIMIT"), 3)


def japanese_limit() -> int:
    """Native JA articles per kind (guide / school / university) per run."""
    return _positive_int(os.getenv("JAPANESE_LIMIT"), 3)
