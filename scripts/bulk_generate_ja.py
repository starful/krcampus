#!/usr/bin/env python3
"""DEPRECATED — use scripts/3.create_japanese_content.py or expand_all_content.py --ja instead."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import frontmatter
import google.generativeai as genai
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

BASE = Path(__file__).resolve().parent.parent
CONTENT = BASE / "app" / "content"
MAX_WORKERS = int(os.getenv("JA_MAX_WORKERS", "10"))
JA_LIMIT = int(os.getenv("JAPANESE_LIMIT", "0") or "0")  # 0 = all pending
MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
BODY_CHARS = int(os.getenv("JA_BODY_CHARS", "1200"))

FEATURE_JA = {
    "topik": "TOPIK対策",
    "dormitory": "寮あり",
    "dorm": "寮あり",
    "on-campus dormitory": "キャンパス内寮",
    "university prep": "大学進学",
    "university pathway": "大学進学支援",
    "cultural": "文化体験",
    "scholarship": "奨学金",
    "english": "英語履修",
    "gks": "GKS対象",
}


def clean_json(text: str) -> str:
    text = text.replace("```json", "").replace("```", "").strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    return text[start:end] if start >= 0 and end > start else text


def pending_sources() -> list[Path]:
    files = []
    for fp in sorted(CONTENT.glob("*.md")):
        name = fp.name
        if name.endswith("_ja.md"):
            continue
        if not (name.startswith("school_") or name.startswith("univ_") or name.startswith("guide_")):
            continue
        if not fp.with_name(fp.stem + "_ja.md").is_file():
            files.append(fp)
    if JA_LIMIT > 0:
        files = files[:JA_LIMIT]
    return files


def fallback_features(features: list[str]) -> list[str]:
    out = []
    for feat in features or []:
        low = str(feat).lower()
        translated = next((ja for key, ja in FEATURE_JA.items() if key in low), None)
        out.append(translated or str(feat)[:48])
    return out[:6]


def fallback_body(title: str, description: str, category: str) -> str:
    label = "大学" if category == "university" else "語学堂" if category == "school" else "ガイド"
    desc = description or f"{title}の基本情報です。"
    return f"""## 概要

{desc}

## {label}のポイント

- 留学生向けプログラムとサポート体制を確認しましょう
- 授業料・寮・ビザ要件は公式サイトで最新情報を確認してください
- KR Campusの地図から近隣の語学堂・大学も比較できます
"""


def apply_ja_stub(src: Path) -> str:
    post = frontmatter.load(src)
    meta = dict(post.metadata)
    basic = dict(meta.get("basic_info") or {})
    category = meta.get("category") or ("university" if src.name.startswith("univ_") else "school")
    title_en = meta.get("title") or basic.get("name_en") or src.stem
    name_ko = basic.get("name_ko") or ""

    if category == "university":
        title_ja = f"{name_ko or title_en} — 留学生入学ガイド"
    elif category == "school":
        title_ja = f"{name_ko or title_en} — 韓国語プログラム"
    else:
        title_ja = title_en

    meta["lang"] = "ja"
    meta["title"] = title_ja
    features = meta.get("features") or meta.get("tags") or []
    meta["features"] = fallback_features(features if isinstance(features, list) else [features])
    if basic:
        basic["name_ja"] = name_ko or basic.get("name_en") or title_ja.split(" — ")[0]
        meta["basic_info"] = basic

    body = fallback_body(title_ja, str(meta.get("description") or ""), category)
    out = src.with_name(src.stem + "_ja.md")
    out.write_text(frontmatter.dumps(frontmatter.Post(body, **meta)), encoding="utf-8")
    return out.name


def translate_one(model, src: Path) -> dict:
    post = frontmatter.load(src)
    prompt = f"""
Translate this KR Campus page to Japanese (です・ます). Return JSON only:
{{"updated_frontmatter": {{...}}, "updated_body": "..."}}

Keep unchanged: id, location, tuition, stats, courses, basic_info.name_ko, basic_info.name_en.
Add lang:"ja", set basic_info.name_ja, translate title/description/features/body.

Input:
{json.dumps({"frontmatter": post.metadata, "body": post.content[:BODY_CHARS]}, ensure_ascii=False, default=str)}
"""
    response = model.generate_content(prompt)
    result = json.loads(clean_json(response.text))
    meta = result.get("updated_frontmatter") or {}
    meta["lang"] = "ja"
    body = result.get("updated_body") or ""
    out = src.with_name(src.stem + "_ja.md")
    out.write_text(frontmatter.dumps(frontmatter.Post(body, **meta)), encoding="utf-8")
    return {"status": "ok", "file": out.name}


def main() -> None:
    print(
        "DEPRECATED: bulk_generate_ja.py uses short-body stubs.\n"
        "Use: python3 scripts/3.create_japanese_content.py\n"
        "  or: python3 scripts/expand_all_content.py --ja --failed-only"
    )
    script = BASE / "scripts" / "3.create_japanese_content.py"
    if script.is_file() and os.getenv("BULK_JA_LEGACY", "").strip() != "1":
        raise SystemExit(subprocess.call([sys.executable, str(script)]))

    pending = pending_sources()
    print(f"Pending JA: {len(pending)} | workers={MAX_WORKERS} | model={MODEL}")
    if not pending:
        return

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        for fp in pending:
            print(f"stub {apply_ja_stub(fp)}")
        return

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(translate_one, model, fp): fp for fp in pending}
        for fut in tqdm(as_completed(futures), total=len(futures)):
            fp = futures[fut]
            try:
                res = fut.result()
                tqdm.write(f"OK {res['file']}")
            except Exception as exc:
                name = apply_ja_stub(fp)
                tqdm.write(f"stub {name} ({exc})")


if __name__ == "__main__":
    main()
