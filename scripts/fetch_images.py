"""Fetch school/university photos from Places API into app/static/images/."""

import os
import re
import shutil
import time

import frontmatter
import requests
from dotenv import load_dotenv

from common import maps_api_key

load_dotenv()

API_KEY = maps_api_key()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_DIR = os.path.join(BASE_DIR, "app", "content")
IMAGES_DIR = os.path.join(BASE_DIR, "app", "static", "images")
MAX_WIDTH = 800
PROTECTED = {"logo.png", "logo.svg", "favicon.ico", "og_image.png", "default.png"}

LANG_SUFFIX_RE = re.compile(
    r"\s+(korean language( institute| center| program| education center)?|language (institute|center|education institute|education center|program)).*$",
    re.I,
)


def search_places(name, lat, lng, *, max_results=8):
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": "places.displayName,places.photos",
    }
    body = {"textQuery": f"{name} South Korea", "languageCode": "en", "maxResultCount": max_results}
    if lat is not None and lng is not None:
        body["locationBias"] = {
            "circle": {
                "center": {"latitude": float(lat), "longitude": float(lng)},
                "radius": 3000.0,
            }
        }
    try:
        res = requests.post(
            "https://places.googleapis.com/v1/places:searchText",
            headers=headers,
            json=body,
            timeout=15,
        )
        res.raise_for_status()
        return res.json().get("places", [])
    except Exception as exc:
        print(f"  search error ({name}): {exc}")
        return []


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def pick_place_with_photo(places, name):
    if not places:
        return None
    needle = _norm(name)
    with_photos = [p for p in places if p.get("photos")]
    if not with_photos:
        return None
    for place in with_photos:
        display = _norm(place.get("displayName", {}).get("text", ""))
        if needle and (needle in display or display in needle):
            return place
    return with_photos[0]


def alternate_queries(name, slug):
    queries = []
    parent = LANG_SUFFIX_RE.sub("", name).strip()
    if parent and parent.lower() != name.lower():
        queries.append(parent)
    if slug.startswith("school_"):
        core = slug[len("school_") :]
        for suffix in (
            "-korean-language-institute",
            "-korean-language-center",
            "-korean-language-program",
            "-language-education-institute",
            "-language-institute",
            "-kli",
            "-lei",
        ):
            if core.endswith(suffix):
                core = core[: -len(suffix)]
                break
        queries.append(core.replace("-", " ").title())
        queries.append(core.replace("-", " "))
    seen = set()
    out = []
    for q in queries:
        key = q.lower()
        if key and key not in seen:
            seen.add(key)
            out.append(q)
    return out


def univ_image_fallback(slug):
    """Language institute → reuse parent university photo if available."""
    if not slug.startswith("school_"):
        return None
    core = slug[len("school_") :]
    candidates = []
    for suffix in (
        "-korean-language-institute",
        "-korean-language-center",
        "-korean-language-program",
        "-language-education-institute",
        "-language-institute",
        "-international-language-institute",
        "-kli",
        "-lei",
    ):
        if core.endswith(suffix):
            candidates.append(f"univ_{core[: -len(suffix)]}.jpg")
            break
    # e.g. school_hufs-korean-language-education-center → univ_hankuk-university-of-foreign-studies (harder)
    for fname in os.listdir(IMAGES_DIR):
        if not fname.startswith("univ_") or not fname.endswith(".jpg"):
            continue
        univ_slug = fname[:-4]
        univ_core = univ_slug[len("univ_") :]
        if core.startswith(univ_core) or univ_core in core:
            candidates.append(fname)
    for name in candidates:
        path = os.path.join(IMAGES_DIR, name)
        if os.path.isfile(path):
            return path
    return None


def download_photo(photo_name, save_path):
    url = f"https://places.googleapis.com/v1/{photo_name}/media"
    params = {"maxWidthPx": MAX_WIDTH, "key": API_KEY, "skipHttpRedirect": "false"}
    try:
        res = requests.get(url, params=params, timeout=20, allow_redirects=True)
        if res.status_code == 200 and res.headers.get("Content-Type", "").startswith("image"):
            with open(save_path, "wb") as f:
                f.write(res.content)
            print(f"  saved ({len(res.content) / 1024:.0f}KB)")
            return True
        print(f"  download failed: HTTP {res.status_code}")
    except Exception as exc:
        print(f"  download error: {exc}")
    return False


def resolve_place(name, lat, lng):
    for query in [name, *alternate_queries(name, "")]:
        place = pick_place_with_photo(search_places(query, lat, lng), query)
        if place:
            return place, query
    return None, None


def resolve_place_for_slug(slug, name, lat, lng):
    place = pick_place_with_photo(search_places(name, lat, lng), name)
    if place:
        return place, name
    for query in alternate_queries(name, slug):
        place = pick_place_with_photo(search_places(query, lat, lng), query)
        if place:
            return place, query
    return None, None


def iter_content_items():
    for filename in sorted(os.listdir(CONTENT_DIR)):
        if filename.endswith("_ja.md"):
            continue
        if not (filename.startswith("school_") or filename.startswith("univ_")):
            continue
        if not filename.endswith(".md"):
            continue
        filepath = os.path.join(CONTENT_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                post = frontmatter.load(f)
        except Exception as exc:
            print(f"skip {filename}: {exc}")
            continue
        meta = post.metadata or {}
        basic = meta.get("basic_info") or {}
        slug = filename[:-3]
        name = (
            meta.get("title")
            or basic.get("name_en")
            or basic.get("name_ko")
            or slug.replace("_", " ")
        )
        loc = meta.get("location") or {}
        yield slug, name, loc.get("lat"), loc.get("lng")


def fetch_item(slug, name, lat, lng, *, force=False):
    save_path = os.path.join(IMAGES_DIR, f"{slug}.jpg")
    if os.path.exists(save_path) and f"{slug}.jpg" not in PROTECTED and not force:
        return "skip"

    place, query = resolve_place_for_slug(slug, name, lat, lng)
    if place:
        place_name = place.get("displayName", {}).get("text", "")
        photos = place.get("photos") or []
        print(f"  place ({query}): {place_name}")
        if download_photo(photos[0].get("name", ""), save_path):
            return "ok"

    fallback = univ_image_fallback(slug)
    if fallback:
        shutil.copy2(fallback, save_path)
        print(f"  copied fallback: {os.path.basename(fallback)}")
        return "ok"

    print("  failed (no photo)")
    return "fail"


def fetch_all_images(*, only_missing=False):
    if not API_KEY:
        print("KRCAMPUS_GOOGLE_MAPS_API_KEY missing in .env")
        return

    os.makedirs(IMAGES_DIR, exist_ok=True)
    items = list(iter_content_items())
    if only_missing:
        items = [
            (slug, name, lat, lng)
            for slug, name, lat, lng in items
            if not os.path.isfile(os.path.join(IMAGES_DIR, f"{slug}.jpg"))
        ]
    print(f"\nFetching Places photos for {len(items)} schools/universities\n")

    success = skipped = failed = 0
    for i, (slug, name, lat, lng) in enumerate(items, 1):
        print(f"[{i:03d}/{len(items)}] {name}")
        result = fetch_item(slug, name, lat, lng, force=only_missing)
        if result == "skip":
            print("  skip (exists)")
            skipped += 1
        elif result == "ok":
            success += 1
        else:
            failed += 1
        time.sleep(0.3)

    print("\n" + "─" * 50)
    print(f"done — ok:{success} skip:{skipped} fail:{failed}")


if __name__ == "__main__":
    import sys

    fetch_all_images(only_missing="--missing" in sys.argv)
