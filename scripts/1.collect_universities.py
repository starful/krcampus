import csv
import json
import os
import time
import requests
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.generativeai.types import GenerationConfig
from common import setup_logging, setup_gemini, clean_json_response, maps_api_key, DATA_DIR, CONTENT_DIR, LOG_DIR
from content_generator import generate_english_body
from content_specs import validate_body

setup_logging("univ_gen.log")
model = setup_gemini()

LIMIT = 100
MAX_WORKERS = 5
INPUT_CSV = os.path.join(DATA_DIR, "universities.csv")
OUTPUT_DIR = CONTENT_DIR
HISTORY_FILE = os.path.join(LOG_DIR, "univ_processed_history.txt")
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


def get_university_meta(name_ko, name_en, region):
    prompt = f"""
    Return JSON only for university "{name_ko}" ({name_en}) in {region}, South Korea.
    Do NOT write a long markdown article. Provide structured metadata only.

    {{
        "english_slug": "url-friendly-slug-in-english",
        "basic_info": {{
            "name_ko": "{name_ko}",
            "name_en": "{name_en}",
            "address": "Official address in English (city: {region})",
            "capacity": null
        }},
        "stats": {{
            "international_students": 123,
            "acceptance_rate": "Estimated % string"
        }},
        "tuition": {{
            "admission_fee": 123456,
            "yearly_tuition": 123456
        }},
        "faculties": ["List", "of", "faculties"],
        "features": ["Key Feature 1", "Key Feature 2"],
        "summary": "One-sentence English SEO description for international applicants."
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


def process_university(univ):
    name_ko = univ["name_ko"]
    name_en = univ["name_en"]
    region = univ.get("region", "Seoul")

    data = get_university_meta(name_ko, name_en, region)
    if not data:
        return f"Failed meta: {name_ko}"

    addr = data["basic_info"].get("address")
    coords = get_google_coordinates(addr)

    raw_slug = data.get("english_slug", name_en.replace(" ", "-").lower())
    slug = f"univ_{raw_slug}" if not raw_slug.startswith("univ_") else raw_slug

    frontmatter_data = {
        "layout": "school",
        "id": slug,
        "title": data["basic_info"]["name_en"],
        "category": "university",
        "tags": data.get("features", []),
        "thumbnail": f"/static/images/{slug}.jpg",
        "location": coords,
        "basic_info": data["basic_info"],
        "stats": data["stats"],
        "tuition": data["tuition"],
        "faculties": data.get("faculties", []),
        "features": data.get("features", []),
        "lang": "en",
    }

    body = generate_english_body("university", frontmatter_data)
    if not body:
        return f"Failed body: {name_ko}"
    ok, reason = validate_body("university", body)
    if not ok:
        return f"Failed validation ({name_ko}): {reason}"

    filepath = os.path.join(OUTPUT_DIR, f"{slug}.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("---\n")
        f.write(json.dumps(frontmatter_data, ensure_ascii=False, indent=2))
        f.write("\n---\n\n")
        f.write(body)

    append_history(name_ko)
    return f"Saved: {slug}.md"


def main():
    if not os.path.exists(INPUT_CSV):
        print(f"Missing {INPUT_CSV}")
        return

    processed_list = load_history()
    univ_list = []
    with open(INPUT_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["name_ko"] not in processed_list:
                univ_list.append(row)

    univ_list = univ_list[:LIMIT]
    print(f"Universities to process: {len(univ_list)} | Workers: {MAX_WORKERS}")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_university, u): u for u in univ_list}
        for future in tqdm(as_completed(futures), total=len(univ_list)):
            try:
                future.result()
            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    main()
