"""Shared Gemini body generation with length validation and retries."""

from __future__ import annotations

import json
import time
from typing import Any

from google.generativeai.types import GenerationConfig

from common import clean_json_response, setup_gemini
from content_specs import ContentKind, SPECS, validate_body

model = setup_gemini()
MAX_ATTEMPTS = 4


def _retry_sleep(exc: Exception, attempt: int) -> None:
    if "429" in str(exc):
        time.sleep(15 * (attempt + 1))
    else:
        time.sleep(3 * (attempt + 1))


def _guide_prompt(title: str, description: str, extra: str = "") -> str:
    target = SPECS["guide"]["target"]
    return f"""
You are an expert author for KR Campus (Study in Korea guides for international students).
Write a long-form article in **ENGLISH** only.

**Total length: {target} characters** (including spaces). Do not go under 6000 or over 7000.

Title: {title}
Brief: {description}
{extra}

Requirements:
- Markdown body ONLY (no frontmatter, no JSON).
- At least 5 sections with ## headings.
- At least 2 Markdown comparison/data tables.
- Bullet lists where helpful.
- Friendly, professional tone for students planning to study in **South Korea** (not Japan).
- Practical facts: visas, costs, timelines, tips.

Generate the full article now.
"""


def _university_prompt(meta: dict) -> str:
    basic = meta.get("basic_info") or {}
    name_ko = basic.get("name_ko", "")
    name_en = basic.get("name_en") or meta.get("title", "")
    address = basic.get("address", "")
    features = meta.get("features") or []
    faculties = meta.get("faculties") or []
    stats = meta.get("stats") or {}
    tuition = meta.get("tuition") or {}
    target = SPECS["university"]["target"]

    return f"""
You are an expert study-abroad consultant. Write an in-depth **ENGLISH** university guide for international students.

University: {name_ko} ({name_en})
Location: {address}
Features: {json.dumps(features, ensure_ascii=False)}
Faculties: {json.dumps(faculties[:20], ensure_ascii=False)}
Stats: {json.dumps(stats, ensure_ascii=False)}
Tuition hints: {json.dumps(tuition, ensure_ascii=False)}

**Length: {target} characters** (6000-7000). Markdown body ONLY.

Required ## sections (expand each substantially):
1. University Overview
2. English-Taught & International Programs
3. Faculties & Academic Strengths
4. Tuition, Fees & Scholarships (include a fee comparison table in KRW)
5. Admissions for International Students
6. Campus Life & Location
7. FAQ (at least 5 Q&A as ### subheadings)

Include at least 2 Markdown tables. Use realistic estimated figures where official data is unknown; label estimates clearly.
"""


def _school_prompt(meta: dict) -> str:
    basic = meta.get("basic_info") or {}
    name_ko = basic.get("name_ko", "")
    name_en = basic.get("name_en") or meta.get("title", "")
    address = basic.get("address", "")
    capacity = basic.get("capacity")
    courses = meta.get("courses") or []
    features = meta.get("features") or []
    target = SPECS["school"]["target"]

    return f"""
You are an expert on Korean language institutes (어학원/한국어학당) for international students.
Write a practical **ENGLISH** guide.

Institute: {name_ko} ({name_en})
Address: {address}
Capacity: {capacity}
Courses (if any): {json.dumps(courses, ensure_ascii=False)}
Features: {json.dumps(features, ensure_ascii=False)}

**Length: {target} characters** (4500-6000). Markdown body ONLY. Focus on actionable facts; avoid generic filler.

Required ## sections:
1. School Overview
2. Programs & Schedule (levels, terms, hours/week)
3. Tuition & Fees (table: registration, quarterly/semester fees, textbooks — use KRW)
4. Admissions & D-4 Visa Steps
5. TOPIK & University Pathway
6. Dormitory & Living in the City
7. FAQ (at least 5 questions as ### subheadings)

Include at least 2 Markdown tables with fee or program data.
"""


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


def _try_condense(kind: ContentKind, body: str, reason: str, *, attempts: int = 3) -> str | None:
    draft = body
    last_reason = reason
    for _ in range(attempts):
        try:
            draft = _condense_body(kind, draft, last_reason)
            ok, last_reason = validate_body(kind, draft)
            if ok:
                return draft.strip()
        except Exception:
            break
    return None


def generate_english_body(kind: ContentKind, meta: dict, *, guide_extra: str = "") -> str | None:
    if kind == "guide":
        prompt = _guide_prompt(
            meta.get("title", "Study in Korea Guide"),
            meta.get("description", ""),
            guide_extra,
        )
    elif kind == "university":
        prompt = _university_prompt(meta)
    else:
        prompt = _school_prompt(meta)

    body = ""
    last_reason = "unknown"
    for attempt in range(MAX_ATTEMPTS):
        try:
            if attempt == 0:
                full_prompt = prompt
            elif last_reason.startswith("too long"):
                full_prompt = (
                    f"{prompt}\n\nYour previous draft was TOO LONG ({len(body)} chars; max {SPECS[kind]['max_chars']}). "
                    f"Rewrite shorter but keep all required ## sections and at least 2 tables. "
                    f"Target {SPECS[kind]['target']} characters."
                )
            else:
                full_prompt = (
                    f"{prompt}\n\nYour previous draft failed validation: {last_reason}. "
                    f"Current length: {len(body)} chars. Rewrite the FULL article to meet all requirements."
                )
            res = model.generate_content(full_prompt)
            body = clean_json_response(res.text)
            if body.startswith("{"):
                # model returned JSON by mistake
                try:
                    parsed = json.loads(body)
                    body = parsed.get("updated_body") or parsed.get("description") or parsed.get("body") or ""
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
        condensed = _try_condense(kind, body, last_reason)
        if condensed:
            return condensed
    if last_reason and last_reason != "unknown":
        print(f"  generate_english_body failed after {MAX_ATTEMPTS} attempts: {last_reason}", flush=True)
    return None


def refresh_school_meta(meta: dict) -> dict:
    """Fill tuition/courses when empty (language institutes)."""
    if meta.get("category") != "school":
        return meta
    if meta.get("tuition") and meta.get("courses"):
        return meta

    basic = meta.get("basic_info") or {}
    name_ko = basic.get("name_ko", "")
    name_en = basic.get("name_en", "")
    prompt = f"""
Return JSON only for Korean language institute "{name_ko}" ({name_en}):
{{
  "courses": [{{"course_name": "...", "admission_month": "...", "total_fees": 1500000}}],
  "tuition": {{"registration_fee": 80000, "quarterly_tuition": 1650000, "textbook_fee": 80000}}
}}
Use realistic KRW estimates (3-4 courses). No markdown.
"""
    for attempt in range(3):
        try:
            res = model.generate_content(prompt, generation_config=GenerationConfig(response_mime_type="application/json"))
            data = json.loads(clean_json_response(res.text))
            if data.get("courses"):
                meta["courses"] = data["courses"]
            if data.get("tuition"):
                meta["tuition"] = data["tuition"]
            return meta
        except Exception as exc:
            _retry_sleep(exc, attempt)
    return meta


def translate_to_japanese(kind: ContentKind, meta: dict, body_en: str) -> tuple[dict, str] | None:
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

Target body length: **{target} characters** (hard max {max_chars}). Do NOT exceed {max_chars} characters.
Keep all ## sections, tables, and FAQ items, but condense wording if needed to stay within the limit.
Keep basic_info.name_ko and basic_info.name_en unchanged. Set lang to "ja". Translate title, description, features to Japanese.
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
            prompt = base_prompt
            if attempt > 0:
                prompt = (
                    f"{base_prompt}\n\nPrevious attempt failed validation: {last_reason}. "
                    f"Draft length was {len(new_body)} chars. Rewrite to fit {target} (max {max_chars})."
                )
            res = model.generate_content(prompt)
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
        condensed = _try_condense(kind, new_body, last_reason)
        if condensed:
            return new_meta, condensed
    return None
