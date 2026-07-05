"""Write JA MD from EN sources (1 Gemini call per item via translate_to_japanese)."""
from __future__ import annotations

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

import frontmatter
from tqdm import tqdm

from batch_limits import guide_limit, japanese_limit, school_limit, university_limit
from common import CONTENT_DIR, remove_content_artifacts, setup_logging
from content_generator import translate_to_japanese
from content_specs import kind_from_filename

setup_logging("ja_native.log")

MAX_WORKERS = max(1, int(os.getenv("JA_MAX_WORKERS", "3")))


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
    body_en = post.content or ""
    kind = kind_from_filename(os.path.basename(en_path), meta)
    if not kind:
        return f"skip: {os.path.basename(en_path)}"

    ja_path = en_path.replace(".md", "_ja.md")
    result = translate_to_japanese(kind, meta, body_en)
    if not result:
        remove_content_artifacts(ja_path)
        return f"❌ Failed: {os.path.basename(en_path)}"

    ja_meta, body_ja = result
    with open(ja_path, "w", encoding="utf-8") as f:
        f.write("---\n")
        f.write(json.dumps(ja_meta, ensure_ascii=False, indent=2))
        f.write("\n---\n\n")
        f.write(body_ja)
    return f"✅ Saved: {os.path.basename(ja_path)}"


def main() -> None:
    if not os.path.isdir(CONTENT_DIR):
        os.makedirs(CONTENT_DIR, exist_ok=True)

    ja_cap = japanese_limit()
    g_cap = min(guide_limit(), ja_cap) if ja_cap > 0 else 0
    s_cap = min(school_limit(), ja_cap) if ja_cap > 0 else 0
    u_cap = min(university_limit(), ja_cap) if ja_cap > 0 else 0
    guides = _pending_by_prefix("guide_", g_cap) if g_cap > 0 else []
    schools = _pending_by_prefix("school_", s_cap) if s_cap > 0 else []
    univs = _pending_by_prefix("univ_", u_cap) if u_cap > 0 else []
    targets = guides + schools + univs

    print(
        f"🇯🇵 JA translate (1 call/item): guides {len(guides)} · schools {len(schools)} · "
        f"universities {len(univs)} (limits g={g_cap} s={s_cap} u={u_cap}, workers={MAX_WORKERS})"
    )
    if not targets:
        print("✅ No pending Japanese articles (all have *_ja.md).")
        return

    failures = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(_write_ja, path): path for path in targets}
        for future in tqdm(as_completed(futures), total=len(targets), desc="JA translate"):
            path = futures[future]
            try:
                result = future.result()
                if result.startswith("❌"):
                    failures += 1
                    print(result)
            except Exception as exc:
                failures += 1
                print(f"❌ {os.path.basename(path)}: {exc}")

    if failures:
        print(f"❌ {failures} Japanese article(s) failed")
        sys.exit(1)
    print("🎉 Japanese translation finished.")


if __name__ == "__main__":
    main()
