import os
import json
import glob
import frontmatter
import google.generativeai as genai
from dotenv import load_dotenv
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_DIR = os.path.join(BASE_DIR, "app", "content")
MAX_WORKERS = 10


def _japanese_batch_limit() -> int:
    raw = os.getenv("JAPANESE_LIMIT", "0").strip().lower()
    if raw in ("0", "all", "none", ""):
        return 99999
    try:
        n = int(raw)
    except ValueError:
        n = 99999
    return n if n > 0 else 99999


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing in .env")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-flash-latest")


def clean_json_response(text):
    text = text.replace("```json", "").replace("```", "").strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end != -1:
        text = text[start:end]
    return text


def translate_file(filepath):
    filename = os.path.basename(filepath)
    name_root, ext = os.path.splitext(filename)
    target_filename = f"{name_root}_ja{ext}"
    target_path = os.path.join(CONTENT_DIR, target_filename)

    if os.path.exists(target_path):
        return {"status": "skipped", "file": target_filename}

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            post = frontmatter.load(f)

        input_data = {
            "filename": filename,
            "frontmatter": post.metadata,
            "content_body": post.content,
        }

        prompt = f"""
        You are a professional editor for 'KR Campus' — a Study in Korea platform for Japanese and English readers.
        Translate the provided English Markdown into **natural Japanese** (です・ます調).

        Instructions:
        1. Translate title, description, features list to Japanese where appropriate.
        2. Keep basic_info.name_en and basic_info.name_ko unchanged.
        3. Add "lang": "ja" to frontmatter.
        4. Do NOT change id, layout, category, location, stats, tuition, courses structure.
        5. Translate the Markdown body to Japanese with H2 sections.

        Output JSON only:
        {{
            "updated_frontmatter": {{ ... }},
            "updated_body": "..."
        }}

        Input:
        {json.dumps(input_data, ensure_ascii=False, default=str)}
        """

        response = model.generate_content(prompt)
        result = json.loads(clean_json_response(response.text))
        new_meta = result.get("updated_frontmatter") or {}
        new_body = result.get("updated_body", "")
        new_meta["lang"] = "ja"

        with open(target_path, "w", encoding="utf-8") as f:
            f.write("---\n")
            f.write(json.dumps(new_meta, ensure_ascii=False, indent=2))
            f.write("\n---\n\n")
            f.write(new_body)

        return {"status": "success", "file": target_filename}
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

    print(f"Found {len(source_files)} English source files.")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(translate_file, fp): fp for fp in source_files}
        for future in tqdm(as_completed(futures), total=len(source_files)):
            result = future.result()
            if result["status"] == "error":
                tqdm.write(f"Error: {result['file']} - {result['msg']}")

    print("Japanese content generation completed.")


if __name__ == "__main__":
    main()
