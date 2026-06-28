import csv
import os
import json
import time
import logging
import glob
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from common import setup_logging, DATA_DIR, CONTENT_DIR, LOG_DIR
from content_generator import generate_english_body
from content_specs import validate_body

# --- 설정 ---
setup_logging("guide_gen.log")

INPUT_CSV = os.path.join(DATA_DIR, "guide_topics.csv")
OUTPUT_DIR = CONTENT_DIR
HISTORY_FILE = os.path.join(LOG_DIR, "guide_processed_history.txt")

def _guide_batch_limit() -> int:
    raw = os.getenv("GUIDE_LIMIT", "3").strip()
    try:
        n = int(raw)
    except ValueError:
        n = 3
    return 3 if n <= 0 else n
MAX_WORKERS = 3    # 동시에 작성할 가이드 수 (긴 텍스트 생성이므로 2~4 권장)

THUMBNAILS = {
    "Cost": "https://images.unsplash.com/photo-1561414927-6d86591d0c4f?w=500",
    "Budget": "https://images.unsplash.com/photo-1561414927-6d86591d0c4f?w=500",
    "Selection": "https://images.unsplash.com/photo-1528164344705-47542687000d?w=500",
    "Visa": "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=500",
    "Housing": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=500",
    "Part-time": "https://images.unsplash.com/photo-1556740758-90de374c12ad?w=500",
    "Exam": "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=500",
    "Preparation": "https://images.unsplash.com/photo-1501504905252-473c47e087f8?w=500",
    "Settlement": "https://images.unsplash.com/photo-1563986768609-322da13575f3?w=500",
    "Insurance": "https://images.unsplash.com/photo-1505751172876-fa1923c5c528?w=500",
    "Region": "https://images.unsplash.com/photo-1542051841857-5f90071e7989?w=500",
    "default": "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=500"
}

def load_history():
    if not os.path.exists(HISTORY_FILE): return set()
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f)

def append_history(slug):
    # 멀티스레드 환경에서 파일 쓰기 시 안전을 위해 간단한 에러 방지
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"{slug}\n")

def get_thumbnail(category):
    if not category: return THUMBNAILS["default"]
    for key, url in THUMBNAILS.items():
        if key in category: return url
    return THUMBNAILS["default"]

def generate_content(row):
    meta = {
        "title": row["title"],
        "description": row.get("description", ""),
        "category": row.get("category", "Guide"),
    }
    extra = f"Core prompt: {row.get('prompt', '')}"
    return generate_english_body("guide", meta, guide_extra=extra)

def process_topic(row):
    """한 개의 주제를 생성하고 파일로 저장하는 단위 작업"""
    slug = row['slug']
    filename = f"guide_{slug}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)

    content_body = generate_content(row)

    if not content_body:
        return f"❌ Failed: {slug}"

    ok, reason = validate_body("guide", content_body)
    if not ok:
        logging.warning(f"guide {slug}: {reason}")
        return f"❌ Failed validation: {slug} — {reason}"

    thumbnail_url = get_thumbnail(row['category'])
    frontmatter_data = {
        "layout": "guide",
        "id": slug,
        "title": row['title'],
        "category": row['category'],
        "tags": [row['category']],
        "description": row['description'],
        "thumbnail": thumbnail_url,
        "date": time.strftime("%Y-%m-%d"),
    }
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("---\n")
        f.write(json.dumps(frontmatter_data, ensure_ascii=False, indent=2))
        f.write("\n---\n\n")
        f.write(content_body)

    append_history(slug)
    return f"✅ Success: {filename}"

def main():
    if not os.path.exists(INPUT_CSV):
        print(f"❌ CSV file not found: {INPUT_CSV}")
        return
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)

    with open(INPUT_CSV, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        all_topics = list(reader)

    processed_slugs = load_history()
    topics_to_process = [row for row in all_topics if row['slug'] not in processed_slugs]
    topics_to_process = topics_to_process[: _guide_batch_limit()]
    
    print(f"🚀 Total: {len(all_topics)} | Processed: {len(processed_slugs)} | Pending: {len(topics_to_process)}")
    print(f"⚡ Running with {MAX_WORKERS} workers...")

    # --- 멀티스레딩 적용 ---
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_topic = {executor.submit(process_topic, row): row for row in topics_to_process}
        
        for future in tqdm(as_completed(future_to_topic), total=len(topics_to_process)):
            row = future_to_topic[future]
            try:
                result = future.result()
                # 로깅 시스템 활용
                logging.info(result)
            except Exception as e:
                logging.error(f"Error in {row['slug']}: {e}")

    print("\n🎉 Generation finished.")

if __name__ == "__main__":
    main()