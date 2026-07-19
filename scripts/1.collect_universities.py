import csv
import json
import os
import sys
import requests
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from batch_limits import university_limit
from common import (
    setup_logging,
    maps_api_key,
    DATA_DIR,
    CONTENT_DIR,
    LOG_DIR,
)
from content_generator import generate_university_en_unified
from content_quality import is_deleted_univ
from topic_queue_csv import resolve as resolve_queue_csv

setup_logging("univ_gen.log")

LIMIT = university_limit()
MAX_WORKERS = 5
INPUT_CSV = os.path.join(DATA_DIR, "universities.csv")


def _universities_csv() -> str:
    return resolve_queue_csv("universities", INPUT_CSV)


OUTPUT_DIR = CONTENT_DIR
HISTORY_FILE = os.path.join(LOG_DIR, "univ_processed_history.txt")
MAPS_API_KEY = maps_api_key()

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)


def append_history(name):
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"{name}\n")


def get_google_coordinates(address):
    if not address:
        return {"lat": 37.5665, "lng": 126.9780}
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": MAPS_API_KEY, "language": "en"}
    try:
        res = requests.get(base_url, params=params, timeout=5)
        data = res.json()
        if data["status"] == "OK":
            loc = data["results"][0]["geometry"]["location"]
            return {"lat": loc["lat"], "lng": loc["lng"]}
    except Exception:
        pass
    return {"lat": 37.5665, "lng": 126.9780}


def process_university(univ):
    name_ko = univ["name_ko"]
    name_en = univ["name_en"]
    region = univ.get("region", "Seoul")

    unified = generate_university_en_unified(name_ko, name_en, region)
    if not unified:
        return f"Failed: {name_ko}"

    data, body = unified
    basic = data.get("basic_info") or {}
    addr = basic.get("address")
    coords = get_google_coordinates(addr)

    raw_slug = data.get("english_slug", name_en.replace(" ", "-").lower())
    slug = f"univ_{raw_slug}" if not raw_slug.startswith("univ_") else raw_slug
    if is_deleted_univ(slug):
        return f"⏭️ Blocked deleted univ: {slug}"
    filepath = os.path.join(OUTPUT_DIR, f"{slug}.md")

    if os.path.isfile(filepath):
        return f"Skip exists: {slug}.md"

    if not basic.get("name_ko"):
        basic["name_ko"] = name_ko
    if not basic.get("name_en"):
        basic["name_en"] = name_en

    frontmatter_data = {
        "layout": "school",
        "id": slug,
        "title": basic.get("name_en") or name_en,
        "category": "university",
        "tags": data.get("features", []),
        "thumbnail": f"/static/images/{slug}.jpg",
        "location": coords,
        "basic_info": basic,
        "stats": data.get("stats") or {},
        "tuition": data.get("tuition") or {},
        "faculties": data.get("faculties", []),
        "features": data.get("features", []),
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
    csv_path = _universities_csv()
    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        sys.exit(1)

    univ_list = []
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name_ko = (row.get("name_ko") or "").strip()
            if name_ko:
                univ_list.append(row)

    univ_list = univ_list[:LIMIT]
    print(
        f"🚀 Universities in queue: {len(univ_list)} (limit {LIMIT}) | Workers: {MAX_WORKERS} | 1 Gemini call/item"
    )
    if not univ_list:
        print("✅ No pending universities in queue.")
        return

    failures = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_university, u): u for u in univ_list}
        for future in tqdm(as_completed(futures), total=len(univ_list)):
            univ = futures[future]
            name_ko = univ.get("name_ko", "?")
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
        print(f"❌ {failures} universit(y/ies) failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
