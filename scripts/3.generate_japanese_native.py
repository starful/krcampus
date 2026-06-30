"""Write native Japanese MD for EN sources missing *_ja.md (no translation pass)."""
from __future__ import annotations

import json
import os
import sys

import frontmatter
from tqdm import tqdm

from batch_limits import japanese_limit
from common import CONTENT_DIR, setup_logging
from content_generator import generate_japanese_body, localize_meta_for_ja
from content_specs import kind_from_filename, validate_body

setup_logging("ja_native.log")


def _pending_by_prefix(prefix: str, limit: int) -> list[str]:
    pending: list[str] = []
    if not os.path.isdir(CONTENT_DIR):
        return pending
    for name in sorted(os.listdir(CONTENT_DIR)):
        if not name.startswith(prefix) or not name.endswith(".md"):
            continue
        if name.endswith("_ja.md"):
            continue
        en_path = os.path.join(CONTENT_DIR, name)
        ja_path = os.path.join(CONTENT_DIR, name.replace(".md", "_ja.md"))
        if os.path.isfile(ja_path):
            continue
        pending.append(en_path)
        if len(pending) >= limit:
            break
    return pending


def _write_ja(en_path: str) -> str:
    post = frontmatter.load(en_path)
    meta = dict(post.metadata)
    kind = kind_from_filename(os.path.basename(en_path), meta)
    if not kind:
        return f"skip: {os.path.basename(en_path)}"

    guide_extra = ""
    if kind == "guide":
        guide_extra = f"Topic context from English page: {meta.get('description', '')}"

    body = generate_japanese_body(kind, meta, guide_extra=guide_extra)
    if not body:
        return f"❌ Failed body: {os.path.basename(en_path)}"

    ok, reason = validate_body(kind, body)
    if not ok:
        return f"❌ Failed validation ({os.path.basename(en_path)}): {reason}"

    ja_meta = localize_meta_for_ja(meta)
    ja_path = en_path.replace(".md", "_ja.md")
    with open(ja_path, "w", encoding="utf-8") as f:
        f.write("---\n")
        f.write(json.dumps(ja_meta, ensure_ascii=False, indent=2))
        f.write("\n---\n\n")
        f.write(body)
    return f"✅ Saved: {os.path.basename(ja_path)}"


def main() -> None:
    if not os.path.isdir(CONTENT_DIR):
        os.makedirs(CONTENT_DIR, exist_ok=True)

    cap = japanese_limit()
    guides = _pending_by_prefix("guide_", cap)
    schools = _pending_by_prefix("school_", cap)
    univs = _pending_by_prefix("univ_", cap)
    targets = guides + schools + univs

    print(
        f"🇯🇵 Native JA (new only): guides {len(guides)} · schools {len(schools)} · "
        f"universities {len(univs)} (limit {cap} each, JAPANESE_LIMIT={cap})"
    )
    if not targets:
        print("✅ No pending Japanese native articles (all have *_ja.md).")
        return

    failures = 0
    for path in tqdm(targets, desc="JA native"):
        try:
            result = _write_ja(path)
            if result.startswith("❌"):
                failures += 1
                print(result)
        except Exception as exc:
            failures += 1
            print(f"❌ {os.path.basename(path)}: {exc}")

    if failures:
        print(f"❌ {failures} Japanese native article(s) failed")
        sys.exit(1)
    print("🎉 Japanese native generation finished.")


if __name__ == "__main__":
    main()
