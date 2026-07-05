import csv
import json
import os
import sys
import requests
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from batch_limits import school_limit
from common import (
    setup_logging,
    maps_api_key,
    DATA_DIR,
    CONTENT_DIR,
    LOG_DIR,
)
from content_generator import generate_school_en_unified
from topic_queue_csv import resolve as resolve_queue_csv

setup_logging("school_gen.log")

LIMIT = school_limit()
MAX_WORKERS = 5
INPUT_CSV = os.path.join(DATA_DIR, "language_schools.csv")


def _schools_csv() -> str:
    return resolve_queue_csv("language_schools", INPUT_CSV)


OUTPUT_DIR = CONTENT_DIR
HISTORY_FILE = os.path.join(LOG_DIR, "school_processed_history.txt")
MAPS_API_KEY = maps_api_key()

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)


def append_history(name):
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"{name}\n")


def get_google_coordinates(city, region):
    query = f"{city}, {region}, South Korea"
    if not MAPS_API_KEY:
        return {"lat": 37.5665, "lng": 126.9780}
    try:
        res = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": query, "key": MAPS_API_KEY, "language": "en"},
            timeout=5,
        )
        data = res.json()
        if data["status"] == "OK":
            loc = data["results"][0]["geometry"]["location"]
            return {"lat": loc["lat"], "lng": loc["lng"]}
    except Exception:
        pass
    return {"lat": 37.5665, "lng": 126.9780}


def process_school(row):
    name_ko = row["name_ko"]
    name_en = row["name_en"]
    region = row.get("region", "Seoul")
    city = row.get("city", region)

    unified = generate_school_en_unified(name_ko, name_en, region, city)
    if not unified:
        return f"Failed: {name_ko}"

    data, body = unified
    coords = get_google_coordinates(city, region)
    raw_slug = data.get("english_slug", name_en.replace(" ", "-").lower())
    slug = f"school_{raw_slug}" if not raw_slug.startswith("school_") else raw_slug
    filepath = os.path.join(OUTPUT_DIR, f"{slug}.md")

    if os.path.isfile(filepath):
        return f"Skip exists: {slug}.md"

    basic = data.get("basic_info") or {}
    if not basic.get("name_ko"):
        basic["name_ko"] = name_ko
    if not basic.get("name_en"):
        basic["name_en"] = name_en

    frontmatter_data = {
        "layout": "school",
        "id": slug,
        "title": basic.get("name_en") or name_en,
        "category": "school",
        "tags": data.get("features", []),
        "thumbnail": f"/static/images/{slug}.jpg",
        "location": coords,
        "basic_info": basic,
        "courses": data.get("courses", []),
        "features": data.get("features", []),
        "faculties": [],
        "stats": {"capacity": basic.get("capacity")},
        "tuition": data.get("tuition") or {},
        "lang": "en",
    }

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("---\n")
        f.write(json.dumps(frontmatter_data, ensure_ascii=False, indent=2))
        f.write("\n---\n\n")
        f.write(body)

    append_history(name_ko)
    return f"Saved: {slug}.md"


def main():
    csv_path = _schools_csv()
    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        sys.exit(1)

    rows = []
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            name_ko = (row.get("name_ko") or "").strip()
            if name_ko:
                rows.append(row)

    rows = rows[:LIMIT]
    print(
        f"🚀 Language schools in queue: {len(rows)} (limit {LIMIT}) | Workers: {MAX_WORKERS} | 1 Gemini call/item"
    )
    if not rows:
        print("✅ No pending language schools in queue.")
        return

    failures = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_school, r): r for r in rows}
        for future in tqdm(as_completed(futures), total=len(rows)):
            row = futures[future]
            name_ko = row.get("name_ko", "?")
            try:
                result = future.result()
                if result and str(result).startswith("Failed"):
                    failures += 1
                    print(result, flush=True)
                elif result and str(result).startswith("Skip"):
                    print(result, flush=True)
            except Exception as e:
                failures += 1
                print(f"⚠️ {name_ko} generated an exception: {e}")

    if failures:
        print(f"❌ {failures} language school(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
