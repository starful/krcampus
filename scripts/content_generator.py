"""Shared Claude body generation with length validation (1 call per EN/JA target)."""

from __future__ import annotations

import json
import os
import time
from typing import Any

from common import clean_json_response, setup_gemini
from content_quality import ENTITY_QUALITY_PROMPT_RULES, GUIDE_QUALITY_PROMPT_RULES
from content_specs import ContentKind, SPECS, validate_body

model = setup_gemini()

MAX_ATTEMPTS = max(1, int(os.getenv("KRCAMPUS_MAX_ATTEMPTS", "1")))
META_ATTEMPTS = max(1, int(os.getenv("KRCAMPUS_META_ATTEMPTS", "1")))
# Default on: try one Claude shorten pass before soft-accepting oversized drafts.
ENABLE_CONDENSE = os.getenv("KRCAMPUS_CONDENSE", "1").strip().lower() not in (
    "0",
    "false",
    "no",
)
CONDENSE_ATTEMPTS = 1 if ENABLE_CONDENSE else 0
# Soft-keep oversized drafts when structure is otherwise OK (do not discard).
SOFT_ACCEPT_TOO_LONG = os.getenv("KRCAMPUS_SOFT_TOO_LONG", "1").strip().lower() not in (
    "0",
    "false",
    "no",
)

# Kept for call-site compatibility; Claude shim ignores generation_config.
_JSON_CONFIG = None


def _retry_sleep(exc: Exception, attempt: int) -> None:
    if "429" in str(exc):
        time.sleep(15 * (attempt + 1))
    else:
        time.sleep(3 * (attempt + 1))


def _length_rules(kind: ContentKind) -> str:
    spec = SPECS[kind]
    return (
        f"Target {spec['target']} characters (spaces included). "
        f"Minimum {spec['min_chars']}. Hard maximum {spec['max_chars']} — never exceed. "
        f"At least {spec['min_h2']} ## sections and {spec['min_tables']} Markdown tables."
    )


def _guide_prompt(title: str, description: str, extra: str = "") -> str:
    return f"""
You are an expert author for KR Campus (Study in Korea guides for international students).
Write a long-form article in **ENGLISH** only.

Title: {title}
Brief: {description}
{extra}

{_length_rules("guide")}

{GUIDE_QUALITY_PROMPT_RULES}

Requirements:
- Markdown body ONLY (no frontmatter, no JSON).
- Friendly, professional tone for students planning to study in **South Korea** (not Japan).
- Practical facts: visas, costs, timelines, tips.
- Cover themes with UNIQUE ## titles: overview, programs/pathways, costs, admissions/visa, campus life, FAQ.

Generate the full article now.
"""


def _university_body_prompt(meta: dict) -> str:
    basic = meta.get("basic_info") or {}
    name_ko = basic.get("name_ko", "")
    name_en = basic.get("name_en") or meta.get("title", "")
    address = basic.get("address", "")
    features = meta.get("features") or []
    faculties = meta.get("faculties") or []
    stats = meta.get("stats") or {}
    tuition = meta.get("tuition") or {}

    return f"""
You are an expert study-abroad consultant. Write an in-depth **ENGLISH** university guide for international students.

University: {name_ko} ({name_en})
Location: {address}
Features: {json.dumps(features, ensure_ascii=False)}
Faculties: {json.dumps(faculties[:20], ensure_ascii=False)}
Stats: {json.dumps(stats, ensure_ascii=False)}
Tuition hints: {json.dumps(tuition, ensure_ascii=False)}

{_length_rules("university")}

{ENTITY_QUALITY_PROMPT_RULES}

Cover these themes with UNIQUE ## titles tailored to THIS university (do not copy numbered generic labels):
- overview of the university and city fit
- English-taught / international pathways
- faculties and academic strengths
- tuition, fees, scholarships (include a KRW comparison table)
- admissions for international students
- campus life and location
- FAQ (at least 5 ### Q&A)

Markdown body ONLY.
"""


def _school_body_prompt(meta: dict) -> str:
    basic = meta.get("basic_info") or {}
    name_ko = basic.get("name_ko", "")
    name_en = basic.get("name_en") or meta.get("title", "")
    address = basic.get("address", "")
    capacity = basic.get("capacity")
    courses = meta.get("courses") or []
    features = meta.get("features") or []

    return f"""
You are an expert on Korean language institutes for international students.
Write a practical **ENGLISH** guide.

Institute: {name_ko} ({name_en})
Address: {address}
Capacity: {capacity}
Courses: {json.dumps(courses, ensure_ascii=False)}
Features: {json.dumps(features, ensure_ascii=False)}

{_length_rules("school")}

{ENTITY_QUALITY_PROMPT_RULES}

Cover these themes with UNIQUE ## titles tailored to THIS institute (do not copy numbered generic labels):
- school overview and who it fits
- programs and schedule
- tuition and fees (KRW table)
- admissions and D-4 visa steps
- TOPIK and university pathway
- dormitory and living in the city
- FAQ (at least 5 ### subheadings)

Markdown body ONLY.
"""


def _school_unified_prompt(name_ko: str, name_en: str, region: str, city: str) -> str:
    spec = SPECS["school"]
    return f"""
Return JSON only. Create a KR Campus language institute page for "{name_ko}" ({name_en}) in {city}, {region}, South Korea.

Schema:
{{
  "english_slug": "url-friendly-slug-without-school_-prefix",
  "basic_info": {{
    "name_ko": "{name_ko}",
    "name_en": "{name_en}",
    "address": "Address in English",
    "capacity": 300
  }},
  "courses": [{{"course_name": "Regular Program", "admission_month": "3", "total_fees": 1500000}}],
  "tuition": {{"registration_fee": 80000, "quarterly_tuition": 1650000, "textbook_fee": 80000}},
  "features": ["TOPIK prep", "Dormitory"],
  "body": "Markdown ENGLISH article. {_length_rules('school')}"
}}

{ENTITY_QUALITY_PROMPT_RULES}

body must satisfy: {spec['min_chars']}-{spec['max_chars']} chars, {spec['min_h2']}+ ## headings, {spec['min_tables']}+ tables.
Use unique ## titles for THIS institute (no numbered generic "School Overview" skeleton).
Do NOT include frontmatter outside JSON. Realistic KRW estimates.
"""


def _university_unified_prompt(name_ko: str, name_en: str, region: str) -> str:
    spec = SPECS["university"]
    return f"""
Return JSON only. Create a KR Campus university page for "{name_ko}" ({name_en}) in {region}, South Korea.

Schema:
{{
  "english_slug": "url-friendly-slug-without-univ_-prefix",
  "basic_info": {{
    "name_ko": "{name_ko}",
    "name_en": "{name_en}",
    "address": "Official address in English",
    "capacity": null
  }},
  "stats": {{"international_students": 123, "acceptance_rate": "Estimated %"}},
  "tuition": {{"admission_fee": 123456, "yearly_tuition": 123456}},
  "faculties": ["Faculty names"],
  "features": ["Key features"],
  "body": "Markdown ENGLISH article. {_length_rules('university')}"
}}

{ENTITY_QUALITY_PROMPT_RULES}

body must satisfy: {spec['min_chars']}-{spec['max_chars']} chars, {spec['min_h2']}+ ## headings, {spec['min_tables']}+ tables.
Use unique ## titles for THIS university (no numbered generic "University Overview" skeleton).
Label estimates clearly. No markdown outside the body string.
"""


def _extract_body_from_parsed(parsed: dict[str, Any]) -> str:
    body = parsed.get("body") or parsed.get("updated_body") or parsed.get("content_body") or ""
    return str(body).strip()


def _condense_body(kind: ContentKind, body: str, reason: str) -> str:
    spec = SPECS[kind]
    prompt = f"""
Shorten this Markdown article to meet KR Campus limits while keeping ALL ## sections, both tables, and FAQ items.

Target: {spec["target"]} characters. Hard maximum: {spec["max_chars"]} characters (including spaces).
Validation issue: {reason}
Current length: {len(body)} characters.

Rules:
- Do NOT remove any ## section or table.
- Tighten sentences and remove redundancy only.
- Output Markdown body ONLY (no frontmatter, no JSON).

Article:
{body}
"""
    res = model.generate_content(prompt)
    return clean_json_response(res.text).strip()


def _try_condense(kind: ContentKind, body: str, reason: str, *, attempts: int | None = None) -> str | None:
    if not ENABLE_CONDENSE:
        return None
    n = attempts if attempts is not None else CONDENSE_ATTEMPTS
    if n <= 0:
        return None
    draft = body
    last_reason = reason
    for _ in range(n):
        try:
            draft = _condense_body(kind, draft, last_reason)
            ok, last_reason = validate_body(kind, draft)
            if ok:
                return draft.strip()
        except Exception:
            break
    return None


def _resolve_oversized(kind: ContentKind, body: str, reason: str) -> str | None:
    """Condense if possible; otherwise soft-accept when structure is OK."""
    condensed = _try_condense(kind, body, reason)
    if condensed:
        return condensed
    if not SOFT_ACCEPT_TOO_LONG:
        return None
    ok, soft_reason = validate_body(kind, body, allow_too_long=True)
    if not ok:
        return None
    print(
        f"  soft-accept oversized {kind}: {soft_reason} "
        f"({len(body.strip())} chars)",
        flush=True,
    )
    return body.strip()


def _generate_body(kind: ContentKind, meta: dict, *, guide_extra: str = "", lang: str = "en") -> str | None:
    if lang != "en":
        return None

    if kind == "guide":
        prompt = _guide_prompt(
            meta.get("title", "Study in Korea Guide"),
            meta.get("description", ""),
            guide_extra,
        )
    elif kind == "university":
        prompt = _university_body_prompt(meta)
    else:
        prompt = _school_body_prompt(meta)

    body = ""
    last_reason = "unknown"
    for attempt in range(MAX_ATTEMPTS):
        try:
            full_prompt = prompt if attempt == 0 else (
                f"{prompt}\n\nPrevious draft failed: {last_reason}. "
                f"Length was {len(body)} chars. Rewrite to meet all requirements."
            )
            res = model.generate_content(full_prompt)
            body = clean_json_response(res.text)
            if body.startswith("{"):
                try:
                    parsed = json.loads(body)
                    body = _extract_body_from_parsed(parsed)
                except json.JSONDecodeError:
                    pass
            ok, reason = validate_body(kind, body)
            if ok:
                return body.strip()
            last_reason = reason
        except Exception as exc:
            last_reason = str(exc)
            _retry_sleep(exc, attempt)

    if body.strip() and last_reason.startswith("too long"):
        kept = _resolve_oversized(kind, body, last_reason)
        if kept:
            return kept
    if last_reason and last_reason != "unknown":
        print(f"  generate_english_body failed: {last_reason}", flush=True)
    return None


def _parse_unified_response(kind: ContentKind, data: dict[str, Any]) -> tuple[dict[str, Any], str] | None:
    body = _extract_body_from_parsed(data)
    if not body:
        return None
    ok, reason = validate_body(kind, body)
    if not ok:
        print(f"  unified {kind} validation failed: {reason} ({len(body)} chars)", flush=True)
        if reason.startswith("too long"):
            kept = _resolve_oversized(kind, body, reason)
            if kept:
                body = kept
            else:
                return None
        else:
            return None
    meta_fields = {k: v for k, v in data.items() if k not in ("body", "updated_body", "content_body")}
    return meta_fields, body


def generate_school_en_unified(
    name_ko: str, name_en: str, region: str, city: str
) -> tuple[dict[str, Any], str] | None:
    """One Claude call: metadata + EN markdown body for a language institute."""
    prompt = _school_unified_prompt(name_ko, name_en, region, city)
    last_err = "unknown"
    for attempt in range(MAX_ATTEMPTS):
        try:
            res = model.generate_content(prompt, generation_config=_JSON_CONFIG)
            data = json.loads(clean_json_response(res.text))
            parsed = _parse_unified_response("school", data)
            if parsed:
                return parsed
            last_err = "validation failed"
        except Exception as exc:
            last_err = str(exc)
            _retry_sleep(exc, attempt)
    print(f"  generate_school_en_unified failed ({name_ko}): {last_err}", flush=True)
    return None


def generate_university_en_unified(
    name_ko: str, name_en: str, region: str
) -> tuple[dict[str, Any], str] | None:
    """One Claude call: metadata + EN markdown body for a university."""
    prompt = _university_unified_prompt(name_ko, name_en, region)
    last_err = "unknown"
    for attempt in range(MAX_ATTEMPTS):
        try:
            res = model.generate_content(prompt, generation_config=_JSON_CONFIG)
            data = json.loads(clean_json_response(res.text))
            parsed = _parse_unified_response("university", data)
            if parsed:
                return parsed
            last_err = "validation failed"
        except Exception as exc:
            last_err = str(exc)
            _retry_sleep(exc, attempt)
    print(f"  generate_university_en_unified failed ({name_ko}): {last_err}", flush=True)
    return None


def generate_english_body(kind: ContentKind, meta: dict, *, guide_extra: str = "") -> str | None:
    return _generate_body(kind, meta, guide_extra=guide_extra, lang="en")


def generate_japanese_body(kind: ContentKind, meta: dict, *, guide_extra: str = "") -> str | None:
    """Deprecated: use translate_to_japanese."""
    return None


def localize_meta_for_ja(meta: dict) -> dict:
    """Deprecated: translate_to_japanese updates frontmatter in one pass."""
    ja_meta = json.loads(json.dumps(meta, ensure_ascii=False))
    ja_meta["lang"] = "ja"
    return ja_meta


def refresh_school_meta(meta: dict) -> dict:
    """No-op: unified school generation includes courses/tuition."""
    return meta


def translate_to_japanese(kind: ContentKind, meta: dict, body_en: str) -> tuple[dict, str] | None:
    """One Claude call: EN meta+body → JA meta+body."""
    spec = SPECS[kind]
    target = spec["target"]
    max_chars = spec["max_chars"]
    input_data = {
        "frontmatter": meta,
        "content_body": body_en,
        "target_length": target,
        "max_characters": max_chars,
    }
    base_prompt = f"""
You are the JP editor for KR Campus (韓国留学). Translate/adapt the English Markdown into **natural Japanese** (です・ます調).

{_length_rules(kind)}
Keep all ## sections, tables, and FAQ items; condense wording only if needed to stay within the limit.
Keep basic_info.name_ko and basic_info.name_en unchanged. Set lang to "ja". Translate title, description, features/tags to Japanese.
Add basic_info.name_ja if missing.

Output JSON only:
{{"updated_frontmatter": {{...}}, "updated_body": "..."}}

Input:
{json.dumps(input_data, ensure_ascii=False, default=str)}
"""
    last_reason = "unknown"
    new_meta: dict = {}
    new_body = ""
    for attempt in range(MAX_ATTEMPTS):
        try:
            prompt = base_prompt if attempt == 0 else (
                f"{base_prompt}\n\nPrevious attempt failed: {last_reason}. "
                f"Draft length was {len(new_body)} chars. Fit within {max_chars} chars."
            )
            res = model.generate_content(prompt, generation_config=_JSON_CONFIG)
            result = json.loads(clean_json_response(res.text))
            new_meta = result.get("updated_frontmatter") or {}
            new_body = (result.get("updated_body") or "").strip()
            new_meta["lang"] = "ja"
            ok, reason = validate_body(kind, new_body)
            if ok:
                return new_meta, new_body
            last_reason = reason
        except Exception as exc:
            last_reason = str(exc)
            _retry_sleep(exc, attempt)

    if new_body.strip() and last_reason.startswith("too long"):
        kept = _resolve_oversized(kind, new_body, last_reason)
        if kept:
            return new_meta, kept
    if last_reason != "unknown":
        print(f"  translate_to_japanese failed: {last_reason}", flush=True)
    return None
