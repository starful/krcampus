import glob
import json
import os

import frontmatter

from app.content_new import enrich_item
from app.paths import CONTENT_DIR, STATIC_DIR
from app.thumbnails import resolve_guide_list_thumbnail


def _read_schools_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("schools", []), data.get("last_updated", "")


def _apply_lang_to_schools(schools, lang):
    for school in schools:
        sid = school.get("id", "")
        school["link"] = f"/school/{sid}?lang={lang}"
    return schools


def load_school_data(lang="en"):
    en_path = os.path.join(STATIC_DIR, "json", "schools_data.json")
    try:
        if lang == "ja":
            ja_path = os.path.join(STATIC_DIR, "json", "schools_data_ja.json")
            if os.path.exists(ja_path):
                schools, updated = _read_schools_json(ja_path)
                if schools:
                    return schools, updated
            schools, updated = _read_schools_json(en_path)
            return _apply_lang_to_schools(schools, "ja"), updated
        return _read_schools_json(en_path)
    except Exception as e:
        print(f"Error loading data: {e}")
        return [], ""


def _load_guide_files(lang):
    guides = []
    pattern = os.path.join(CONTENT_DIR, "guide_*_ja.md") if lang == "ja" else os.path.join(CONTENT_DIR, "guide_*.md")
    guide_files = glob.glob(pattern)
    if lang != "ja":
        guide_files = [f for f in guide_files if not f.endswith("_ja.md")]

    guide_files.sort(key=os.path.getmtime, reverse=True)

    for filepath in guide_files:
        try:
            post = frontmatter.load(filepath)
            meta = post.metadata
            guide_id = str(meta.get("id", "")).replace("_ja", "").replace("guide_", "")
            safe_thumbnail = resolve_guide_list_thumbnail(meta)

            guides.append(enrich_item({
                "title": meta.get("title", "Untitled"),
                "description": meta.get("description", ""),
                "category": meta.get("category", "Guide"),
                "link": f"/guide/{guide_id}?lang={lang}",
                "thumbnail": safe_thumbnail,
                "item_type": "guide",
                "is_featured": meta.get("is_featured", False),
                "published": str(meta.get("date", "")),
            }))
        except Exception:
            pass
    return guides


def load_guides(lang="en"):
    guides = _load_guide_files(lang)
    if lang == "ja" and not guides:
        guides = _load_guide_files("en")
        for guide in guides:
            guide["link"] = guide["link"].replace("lang=en", "lang=ja")
    return guides
