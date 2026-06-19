import csv
import json
import os
import time
import requests
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.generativeai.types import GenerationConfig
from common import setup_logging, setup_gemini, clean_json_response, maps_api_key, DATA_DIR, CONTENT_DIR, LOG_DIR

setup_logging("school_gen.log")
model = setup_gemini()

LIMIT = 100
MAX_WORKERS = 5
INPUT_CSV = os.path.join(DATA_DIR, "language_schools.csv")
OUTPUT_DIR = CONTENT_DIR
HISTORY_FILE = os.path.join(LOG_DIR, "school_processed_history.txt")
MAPS_API_KEY = maps_api_key()

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return set()
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f)


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


def get_language_school_info(name_ko, name_en, region, city):
    prompt = f"""
    You are an expert on Korean language institutes for international students.
    Write a comprehensive English guide for "{name_ko}" ({name_en}) in {city}, {region}, South Korea.

    Required JSON Structure:
    {{
        "english_slug": "url-friendly-slug",
        "basic_info": {{
            "name_ko": "{name_ko}",
            "name_en": "{name_en}",
            "address": "Address in English",
            "capacity": 300
        }},
        "courses": [
            {{"course_name": "Regular Program", "admission_month": "3", "total_fees": 1500000}}
        ],
        "features": ["TOPIK prep", "Dormitory", "University prep"],
        "description": "## School Overview\\n...markdown body..."
    }}
    """
    for i in range(3):
        try:
            res = model.generate_content(
                prompt, generation_config=GenerationConfig(response_mime_type="application/json")
            )
            return json.loads(clean_json_response(res.text))
        except Exception as e:
            if "429" in str(e):
                time.sleep(10 * (i + 1))
            else:
                time.sleep(2)
    return None


def process_school(row):
    name_ko = row["name_ko"]
    name_en = row["name_en"]
    region = row.get("region", "Seoul")
    city = row.get("city", region)

    data = get_language_school_info(name_ko, name_en, region, city)
    if not data:
        return f"Failed: {name_ko}"

    coords = get_google_coordinates(city, region)
    raw_slug = data.get("english_slug", name_en.replace(" ", "-").lower())
    slug = f"school_{raw_slug}" if not raw_slug.startswith("school_") else raw_slug

    frontmatter_data = {
        "layout": "school",
        "id": slug,
        "title": data["basic_info"]["name_en"],
        "category": "school",
        "tags": data.get("features", []),
        "thumbnail": f"/static/images/{slug}.jpg",
        "location": coords,
        "basic_info": data["basic_info"],
        "courses": data.get("courses", []),
        "features": data.get("features", []),
        "faculties": [],
        "stats": {"capacity": data["basic_info"].get("capacity")},
        "tuition": {},
        "lang": "en",
    }

    filepath = os.path.join(OUTPUT_DIR, f"{slug}.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("---\n")
        f.write(json.dumps(frontmatter_data, ensure_ascii=False, indent=2))
        f.write("\n---\n\n")
        f.write(data.get("description", "No content available."))

    append_history(name_ko)
    return f"Saved: {slug}.md"


def main():
    if not os.path.exists(INPUT_CSV):
        print(f"Missing {INPUT_CSV}")
        return

    processed = load_history()
    rows = []
    with open(INPUT_CSV, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row["name_ko"] not in processed:
                rows.append(row)

    rows = rows[:LIMIT]
    print(f"Language schools to process: {len(rows)}")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_school, r): r for r in rows}
        for future in tqdm(as_completed(futures), total=len(rows)):
            try:
                future.result()
            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    main()
