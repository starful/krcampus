#!/usr/bin/env python3
"""
Regenerate EN and/or JA markdown bodies to meet KR Campus length targets.

  guide / university: 6000-7000 characters
  language school:    4500-6000 characters

Usage:
  python3 scripts/expand_all_content.py --en --ja
  python3 scripts/expand_all_content.py --en --limit 5
  EXPAND_WORKERS=8 python3 scripts/expand_all_content.py --en --ja
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import frontmatter
from tqdm import tqdm

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from content_generator import (  # noqa: E402
    generate_english_body,
    refresh_school_meta,
    translate_to_japanese,
)
from content_specs import SPECS, kind_from_filename, validate_body  # noqa: E402

BASE = SCRIPT_DIR.parent
CONTENT = BASE / "app" / "content"
DATA = BASE / "data"
WORKERS = int(os.getenv("EXPAND_WORKERS", "8"))


def load_guide_topics() -> dict[str, dict]:
    path = DATA / "guide_topics.csv"
    if not path.is_file():
        return {}
    out = {}
    with path.open(encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            slug = (row.get("slug") or "").strip()
            if slug:
                out[slug] = row
    return out


def list_en_sources(*, failed_only: bool = False) -> list[Path]:
    files = []
    for fp in sorted(CONTENT.glob("*.md")):
        if fp.name.endswith("_ja.md"):
            continue
        if fp.name.startswith(("school_", "univ_", "guide_")):
            files.append(fp)
    if not failed_only:
        return files

    out: list[Path] = []
    for fp in files:
        post = frontmatter.load(fp)
        kind = kind_from_filename(fp.name, post.metadata)
        if not kind:
            continue
        ok, _ = validate_body(kind, post.content or "")
        if not ok:
            out.append(fp)
    return out


def list_ja_sources(*, failed_only: bool = False) -> list[Path]:
    en_files = list_en_sources(failed_only=False)
    if not failed_only:
        return en_files

    out: list[Path] = []
    for fp in en_files:
        post = frontmatter.load(fp)
        kind = kind_from_filename(fp.name, post.metadata)
        if not kind:
            continue
        en_ok, _ = validate_body(kind, post.content or "")
        if not en_ok:
            continue
        ja_path = fp.with_name(fp.stem + "_ja.md")
        if not ja_path.is_file():
            out.append(fp)
            continue
        ja_post = frontmatter.load(ja_path)
        ja_ok, _ = validate_body(kind, ja_post.content or "")
        if not ja_ok:
            out.append(fp)
    return out


def write_md(path: Path, meta: dict, body: str) -> None:
    path.write_text(
        "---\n"
        + json.dumps(meta, ensure_ascii=False, indent=2)
        + "\n---\n\n"
        + body.strip()
        + "\n",
        encoding="utf-8",
    )


def expand_en_file(fp: Path, guide_topics: dict[str, dict]) -> dict:
    post = frontmatter.load(fp)
    meta = dict(post.metadata)
    kind = kind_from_filename(fp.name, meta)
    if not kind:
        return {"file": fp.name, "status": "skip", "msg": "unknown kind"}

    if kind == "school":
        meta = refresh_school_meta(meta)

    guide_extra = ""
    if kind == "guide":
        slug = meta.get("id") or fp.stem.replace("guide_", "")
        row = guide_topics.get(slug)
        if row:
            guide_extra = f"Core prompt from editorial: {row.get('prompt', '')}"

    body = generate_english_body(kind, meta, guide_extra=guide_extra)
    if not body:
        return {"file": fp.name, "status": "fail", "msg": "generation failed"}

    ok, reason = validate_body(kind, body)
    write_md(fp, meta, body)
    return {
        "file": fp.name,
        "status": "ok" if ok else "warn",
        "msg": f"{len(body)} chars — {reason}",
    }


def expand_ja_file(en_fp: Path) -> dict:
    post = frontmatter.load(en_fp)
    meta = dict(post.metadata)
    kind = kind_from_filename(en_fp.name, meta)
    if not kind:
        return {"file": en_fp.name, "status": "skip", "msg": "unknown kind"}

    body_en = post.content or ""
    en_ok, en_reason = validate_body(kind, body_en)
    if not en_ok:
        return {"file": en_fp.name, "status": "fail", "msg": f"EN not ready: {en_reason}"}

    result = translate_to_japanese(kind, meta, body_en)
    if not result:
        return {"file": en_fp.name, "status": "fail", "msg": "JA translation failed"}

    new_meta, new_body = result
    ja_path = en_fp.with_name(en_fp.stem + "_ja.md")
    write_md(ja_path, new_meta, new_body)
    ok, reason = validate_body(kind, new_body)
    return {
        "file": ja_path.name,
        "status": "ok" if ok else "warn",
        "msg": f"{len(new_body)} chars — {reason}",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Expand KR Campus content to target lengths")
    parser.add_argument("--en", action="store_true", help="Regenerate English bodies")
    parser.add_argument("--ja", action="store_true", help="Regenerate Japanese bodies from EN")
    parser.add_argument("--limit", type=int, default=0, help="Max files per phase (0=all)")
    parser.add_argument(
        "--failed-only",
        action="store_true",
        help="Only process EN sources that fail length/structure validation",
    )
    args = parser.parse_args()

    if not args.en and not args.ja:
        args.en = True
        args.ja = True

    sources = list_en_sources(failed_only=args.failed_only)
    if args.limit > 0:
        sources = sources[: args.limit]

    ja_sources = list_ja_sources(failed_only=args.failed_only)
    if args.limit > 0:
        ja_sources = ja_sources[: args.limit]

    guide_topics = load_guide_topics()
    failures = 0

    if args.en:
        print(f"EN expansion: {len(sources)} files, workers={WORKERS}")
        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            futures = {pool.submit(expand_en_file, fp, guide_topics): fp for fp in sources}
            for fut in tqdm(as_completed(futures), total=len(futures), desc="EN"):
                res = fut.result()
                if res["status"] == "fail":
                    failures += 1
                    tqdm.write(f"FAIL {res['file']}: {res['msg']}")
                elif res["status"] == "warn":
                    tqdm.write(f"WARN {res['file']}: {res['msg']}")

    if args.ja:
        print(f"JA translation: {len(ja_sources)} files, workers={WORKERS}")
        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            futures = {pool.submit(expand_ja_file, fp): fp for fp in ja_sources}
            for fut in tqdm(as_completed(futures), total=len(futures), desc="JA"):
                res = fut.result()
                if res["status"] == "fail":
                    failures += 1
                    tqdm.write(f"FAIL {res['file']}: {res['msg']}")
                elif res["status"] == "warn":
                    tqdm.write(f"WARN {res['file']}: {res['msg']}")

    print(f"Done. failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
