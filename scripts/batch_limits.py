"""Per-run batch caps from okadmin pipeline env (default 3)."""
from __future__ import annotations

import os


def _non_negative_int(raw: str | None, default: int) -> int:
    if raw is None or str(raw).strip() == "":
        return default
    try:
        return max(0, int(str(raw).strip()))
    except ValueError:
        return default


def _positive_int(raw: str | None, default: int) -> int:
    n = _non_negative_int(raw, default)
    return default if n <= 0 else n


def guide_limit() -> int:
    return _non_negative_int(os.getenv("GUIDE_LIMIT"), 3)


def content_limit() -> int:
    """Language schools + universities (EN generation per run)."""
    return _non_negative_int(os.getenv("CONTENT_LIMIT"), 3)


def school_limit() -> int:
    raw = os.getenv("SCHOOL_LIMIT")
    if raw is not None and str(raw).strip() != "":
        return _non_negative_int(raw, 3)
    return content_limit()


def university_limit() -> int:
    raw = os.getenv("UNIVERSITY_LIMIT")
    if raw is not None and str(raw).strip() != "":
        return _non_negative_int(raw, 3)
    return content_limit()


def japanese_limit() -> int:
    """Native JA articles per kind (guide / school / university) per run."""
    return _non_negative_int(os.getenv("JAPANESE_LIMIT"), 3)
