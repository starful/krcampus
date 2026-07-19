"""Content-quality guards for KR Campus generation scripts.

Mirrors jpcampus policy: reject interchangeable template headings and
block regenerating diet-deleted slugs. Length/table floors stay in content_specs.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
PLAN_PATH = ROOT / "data" / "content_diet" / "plan.json"

# Mass-produced longtail / interchangeable skeletons.
FORBIDDEN_HEADINGS = frozenset(
    {
        "who this guide is for",
        "how to compare your options",
        "recommended decision process",
        "common mistakes to avoid",
        "final checklist",
        "1. university overview",
        "2. english-taught & international programs",
        "3. faculties & academic strengths",
        "4. tuition, fees & scholarships",
        "5. admissions for international students",
        "6. campus life & location",
        "7. faq",
        "1. school overview",
        "2. programs & schedule",
        "3. tuition & fees",
        "4. admissions & d-4 visa steps",
        "5. topik & university pathway",
        "6. dormitory & living in the city",
        "university overview",
        "english-taught & international programs",
        "faculties & academic strengths",
        "school overview",
        "programs & schedule",
        "admissions & d-4 visa steps",
    }
)

GUIDE_QUALITY_PROMPT_RULES = """
Quality rules (mandatory):
- Answer search intent early. No fluff-only intro.
- Do NOT use interchangeable template section titles such as
  "Who This Guide Is For", "University Overview", "Programs & Schedule",
  "Admissions & D-4 Visa Steps", "Final Checklist".
- Use unique ## headings tailored to THIS institution or topic.
- Include concrete Korea-specific facts (visa, costs, city, TOPIK) when relevant.
- Prefer Markdown tables for fees/programs when data exists.
- Generate ONLY Markdown body (no frontmatter) unless asked for JSON.
""".strip()

ENTITY_QUALITY_PROMPT_RULES = GUIDE_QUALITY_PROMPT_RULES


@lru_cache(maxsize=1)
def load_diet_plan() -> dict:
    if not PLAN_PATH.exists():
        return {}
    try:
        return json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def deleted_guide_slugs() -> set[str]:
    plan = load_diet_plan()
    return {str(s).strip() for s in plan.get("delete_guides", []) if str(s).strip()}


def deleted_univ_ids() -> set[str]:
    plan = load_diet_plan()
    return {str(s).strip() for s in plan.get("delete_univs", []) if str(s).strip()}


def deleted_school_ids() -> set[str]:
    plan = load_diet_plan()
    return {str(s).strip() for s in plan.get("delete_schools", []) if str(s).strip()}


def is_deleted_guide(slug: str) -> bool:
    return slug.strip() in deleted_guide_slugs()


def is_deleted_univ(school_id: str) -> bool:
    sid = school_id.strip()
    if not sid.startswith("univ_"):
        sid = f"univ_{sid}"
    return sid in deleted_univ_ids()


def is_deleted_school(school_id: str) -> bool:
    sid = school_id.strip()
    if not sid.startswith("school_"):
        sid = f"school_{sid}"
    return sid in deleted_school_ids()


def extract_h2_headings(body: str) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(r"^##\s+(.+)$", body or "", re.M)]


def template_heading_issues(body: str, *, threshold: int = 3) -> list[str]:
    headings = [h.lower() for h in extract_h2_headings(body)]
    hits = [h for h in headings if h in FORBIDDEN_HEADINGS]
    if len(hits) >= threshold:
        return [f"template headings detected: {hits[:5]}"]
    return []


def assert_no_template_headings(body: str, *, threshold: int = 3) -> None:
    issues = template_heading_issues(body, threshold=threshold)
    if issues:
        raise ValueError("; ".join(issues))
