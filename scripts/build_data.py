# scripts/build_data.py

import os
import json
import sys
import frontmatter
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from md_dates import ensure_post_date, save_post  # noqa: E402

CONTENT_DIR = os.path.join(BASE_DIR, "app", "content")
OUTPUT_DIR = os.path.join(BASE_DIR, "app", "static", "json")
GCS_IMAGE_BASE = os.environ.get(
    "GCS_IMAGE_BASE",
    "https://storage.googleapis.com/ok-project-assets/krcampus",
)


def dedupe_key(entry):
    basic = entry.get("basic_info") or {}
    name_ko = (basic.get("name_ko") or "").strip()
    if name_ko:
        return ("name_ko", entry.get("category"), name_ko)

    loc = entry.get("location") or {}
    lat, lng = loc.get("lat"), loc.get("lng")
    if lat is not None and lng is not None:
        return ("loc", entry.get("category"), round(float(lat), 4), round(float(lng), 4))

    name = (basic.get("name_en") or basic.get("name_ko") or "").lower()
    for token in (" (unist)", "unist", " national institute of science and technology"):
        name = name.replace(token, "")
    name = "".join(ch for ch in name if ch.isalnum())
    return ("name", entry.get("category"), name)


def dedupe_schools(schools_list):
    seen = {}
    for entry in schools_list:
        key = dedupe_key(entry)
        if key in seen:
            print(f"Skipping duplicate: {entry['id']} (same as {seen[key]['id']})")
            continue
        seen[key] = entry
    return list(seen.values())


def resolve_thumbnail(meta, slug):
    raw = meta.get("thumbnail") or ""
    if raw.startswith("http"):
        return raw
    if raw.startswith("/static/images/"):
        return f"{GCS_IMAGE_BASE}/{os.path.basename(raw)}"
    return f"{GCS_IMAGE_BASE}/{slug}.jpg"


def build_json(lang_suffix, output_filename):
    print(f"Building {output_filename} ...")
    schools_list = []
    backfilled = 0
    all_files = os.listdir(CONTENT_DIR)
    all_files.sort(key=lambda x: os.path.getmtime(os.path.join(CONTENT_DIR, x)), reverse=True)

    for filename in all_files:
        if not (filename.startswith("univ_") or filename.startswith("school_")):
            continue

        is_ja_file = filename.endswith("_ja.md")
        if lang_suffix == "ja" and not is_ja_file:
            continue
        if lang_suffix == "en" and is_ja_file:
            continue

        filepath = os.path.join(CONTENT_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                post = frontmatter.load(f)
                meta = post.metadata

                published_date, changed = ensure_post_date(post, filepath)
                if changed:
                    save_post(filepath, post)
                    backfilled += 1

                school_id = meta.get("id", "").replace("_ja", "") if meta.get("id") else ""
                basic = meta.get("basic_info", {}) or {}

                schools_list.append(
                    {
                        "id": school_id,
                        "category": meta.get("category", "school"),
                        "published": published_date,
                        "thumbnail": resolve_thumbnail(meta, school_id),
                        "basic_info": {
                            "name_ko": basic.get("name_ko") or basic.get("name_ja"),
                            "name_en": basic.get("name_en"),
                            "name_ja": basic.get("name_ja"),
                            "name_display": meta.get("title"),
                            "address": basic.get("address"),
                            "capacity": basic.get("capacity"),
                        },
                        "location": meta.get("location"),
                        "features": meta.get("features", []),
                        "tuition": meta.get("tuition"),
                        "stats": meta.get("stats"),
                        "link": f"/school/{school_id}?lang={lang_suffix}",
                    }
                )
        except Exception as e:
            print(f"Error ({filename}): {e}")

    schools_list = dedupe_schools(schools_list)
    schools_list.sort(key=lambda x: (x.get('published', ''), x.get('id', '')), reverse=True)

    final_data = {
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "schools": schools_list,
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False)

    print(f"Saved {len(schools_list)} items to {output_filename}")
    if backfilled:
        print(f"date backfill: {backfilled} MD")


def main():
    build_json("en", "schools_data.json")
    build_json("ja", "schools_data_ja.json")


if __name__ == "__main__":
    main()
