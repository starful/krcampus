#!/usr/bin/env python3
"""
Batch-optimize guide frontmatter title/description for CTR.

Usage:
  python scripts/optimize_meta_copy.py --dry-run
  python scripts/optimize_meta_copy.py --apply
"""

from __future__ import annotations

import argparse
import glob
from datetime import datetime, timezone
from pathlib import Path

import frontmatter

ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "app" / "content"


def optimize_title(title: str) -> str:
    year = datetime.now(timezone.utc).strftime("%Y")
    clean = (title or "").strip()
    if not clean:
        clean = "Study in Japan Guide"
    if clean.startswith(f"[{year}]"):
        return clean
    optimized = f"[{year}] {clean}"
    return optimized[:68].rstrip()


def optimize_description(description: str, title: str) -> str:
    text = (description or "").strip()
    if not text:
        text = f"Practical guide for {title.lower()} with clear decision points for international students."
    if len(text) > 155:
        text = f"{text[:152].rstrip()}..."
    return text


def process_file(path: Path, apply: bool) -> tuple[bool, str]:
    post = frontmatter.load(path)
    original_title = post.get("title", "")
    original_desc = post.get("description", "")

    new_title = optimize_title(original_title)
    new_desc = optimize_description(original_desc, original_title or "studying in Japan")

    changed = (new_title != original_title) or (new_desc != original_desc)
    if changed:
        post["title"] = new_title
        post["description"] = new_desc
        if apply:
            path.write_text(frontmatter.dumps(post), encoding="utf-8")
        return True, f"updated: {path.name}"
    return False, f"skip: {path.name}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Write changes to files")
    parser.add_argument("--dry-run", action="store_true", help="Only show planned changes")
    args = parser.parse_args()

    apply = args.apply and not args.dry_run
    files = sorted(glob.glob(str(CONTENT_DIR / "guide_*.md")))
    files = [Path(f) for f in files if not f.endswith("_kr.md")]

    changed_count = 0
    for file in files:
        changed, message = process_file(file, apply)
        if changed:
            changed_count += 1
        print(message)

    mode = "APPLY" if apply else "DRY-RUN"
    print(f"[{mode}] total={len(files)} changed={changed_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
