# scripts/build_data.py

import os
import json
import frontmatter
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_DIR = os.path.join(BASE_DIR, "app", "content")
OUTPUT_DIR = os.path.join(BASE_DIR, "app", "static", "json")
GCS_IMAGE_BASE = os.environ.get(
    "GCS_IMAGE_BASE",
    "https://storage.googleapis.com/ok-project-assets/krcampus",
)


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

                school_id = meta.get("id", "").replace("_ja", "") if meta.get("id") else ""
                basic = meta.get("basic_info", {}) or {}

                schools_list.append(
                    {
                        "id": school_id,
                        "category": meta.get("category", "school"),
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

    final_data = {
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "schools": schools_list,
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False)

    print(f"Saved {len(schools_list)} items to {output_filename}")


def main():
    build_json("en", "schools_data.json")
    build_json("ja", "schools_data_ja.json")


if __name__ == "__main__":
    main()
