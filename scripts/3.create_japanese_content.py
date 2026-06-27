import os
import json
import glob
import frontmatter
from dotenv import load_dotenv
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from common import CONTENT_DIR
from content_generator import translate_to_japanese
from content_specs import kind_from_filename, validate_body

BASE_DIR = SCRIPT_DIR.parent
MAX_WORKERS = int(os.getenv("JA_MAX_WORKERS", "5"))
REGENERATE = os.getenv("REGENERATE_JA", "").lower() in ("1", "true", "yes")


def _japanese_batch_limit() -> int:
    raw = os.getenv("JAPANESE_LIMIT", "0").strip().lower()
    if raw in ("0", "all", "none", ""):
        return 99999
    try:
        n = int(raw)
    except ValueError:
        n = 99999
    return n if n > 0 else 99999


def translate_file(filepath):
    filename = os.path.basename(filepath)
    name_root, ext = os.path.splitext(filename)
    target_filename = f"{name_root}_ja{ext}"
    target_path = os.path.join(CONTENT_DIR, target_filename)

    if os.path.exists(target_path) and not REGENERATE:
        return {"status": "skipped", "file": target_filename}

    try:
        post = frontmatter.load(filepath)
        meta = dict(post.metadata)
        kind = kind_from_filename(filename, meta)
        if not kind:
            return {"status": "skip", "file": filename}

        result = translate_to_japanese(kind, meta, post.content or "")
        if not result:
            return {"status": "error", "file": filename, "msg": "translation failed"}

        new_meta, new_body = result
        ok, reason = validate_body(kind, new_body)

        with open(target_path, "w", encoding="utf-8") as f:
            f.write("---\n")
            f.write(json.dumps(new_meta, ensure_ascii=False, indent=2))
            f.write("\n---\n\n")
            f.write(new_body)

        status = "success" if ok else "warn"
        return {"status": status, "file": target_filename, "msg": reason}
    except Exception as e:
        return {"status": "error", "file": filename, "msg": str(e)}


def main():
    if not os.path.exists(CONTENT_DIR):
        print(f"Content directory not found: {CONTENT_DIR}")
        return

    all_files = glob.glob(os.path.join(CONTENT_DIR, "*.md"))
    source_files = [
        f
        for f in all_files
        if os.path.basename(f).startswith(("school_", "univ_", "guide_"))
        and not f.endswith("_ja.md")
    ]

    batch_limit = _japanese_batch_limit()
    pending = len(source_files)
    if pending > batch_limit:
        source_files = source_files[:batch_limit]
        print(f"Processing {batch_limit} of {pending} files (JAPANESE_LIMIT={batch_limit})")

    print(f"Found {len(source_files)} English source files (REGENERATE_JA={REGENERATE}).")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(translate_file, fp): fp for fp in source_files}
        for future in tqdm(as_completed(futures), total=len(source_files)):
            result = future.result()
            if result["status"] == "error":
                tqdm.write(f"Error: {result['file']} - {result.get('msg')}")
            elif result["status"] == "warn":
                tqdm.write(f"Warn: {result['file']} - {result.get('msg')}")

    print("Japanese content generation completed.")


if __name__ == "__main__":
    main()
