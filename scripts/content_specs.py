"""Target body length and structure rules for KR Campus markdown content."""

from __future__ import annotations

import re
from typing import Literal

ContentKind = Literal["guide", "university", "school"]

SPECS: dict[ContentKind, dict] = {
    "guide": {
        "label": "guide",
        "min_chars": 5500,
        "max_chars": 7500,
        "target": "6000-7000",
        "min_h2": 5,
        "min_tables": 2,
    },
    "university": {
        "label": "university",
        "min_chars": 5500,
        "max_chars": 7500,
        "target": "6000-7000",
        "min_h2": 5,
        "min_tables": 2,
    },
    "school": {
        "label": "language institute",
        "min_chars": 4000,
        "max_chars": 6500,
        "target": "4500-6000",
        "min_h2": 5,
        "min_tables": 2,
    },
}


def kind_from_filename(name: str, meta: dict | None = None) -> ContentKind | None:
    if name.startswith("guide_"):
        return "guide"
    if name.startswith("univ_"):
        return "university"
    if name.startswith("school_"):
        return "school"
    if meta:
        cat = meta.get("category")
        if cat == "university":
            return "university"
        if cat == "school":
            return "school"
        if meta.get("layout") == "guide":
            return "guide"
    return None


def count_h2(body: str) -> int:
    return len(re.findall(r"^##\s+", body, flags=re.MULTILINE))


def count_tables(body: str) -> int:
    lines = body.splitlines()
    tables = 0
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s\-:|]+\|", lines[i + 1].strip()):
            tables += 1
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                i += 1
            continue
        i += 1
    return tables


def validate_body(kind: ContentKind, body: str) -> tuple[bool, str]:
    spec = SPECS[kind]
    n = len(body.strip())
    if n < spec["min_chars"]:
        return False, f"too short ({n} < {spec['min_chars']})"
    if n > spec["max_chars"]:
        return False, f"too long ({n} > {spec['max_chars']})"
    h2 = count_h2(body)
    if h2 < spec["min_h2"]:
        return False, f"need {spec['min_h2']}+ H2 sections (has {h2})"
    tables = count_tables(body)
    if tables < spec["min_tables"]:
        return False, f"need {spec['min_tables']}+ tables (has {tables})"
    return True, "ok"


def length_band(kind: ContentKind) -> str:
    return SPECS[kind]["target"]
