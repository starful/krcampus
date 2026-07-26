import os
import json
import re
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 경로 상수 정의
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CONTENT_DIR = os.path.join(BASE_DIR, "app", "content")
LOG_DIR = os.path.join(BASE_DIR, "logs")

# 로깅 설정 함수
def setup_logging(filename):
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    logging.basicConfig(
        filename=os.path.join(LOG_DIR, filename),
        level=logging.INFO,
        format='%(asctime)s - %(message)s',
        encoding='utf-8'
    )

def maps_api_key() -> str | None:
    return os.getenv("KRCAMPUS_GOOGLE_MAPS_API_KEY") or None


def remove_content_artifacts(md_path: str | os.PathLike[str]) -> bool:
    """Remove EN/JA markdown for a content slug (no-op if missing)."""
    base = str(md_path)
    removed = False
    paths = [base]
    if base.endswith(".md") and not base.endswith("_ja.md"):
        paths.append(base[:-3] + "_ja.md")
    for path in paths:
        if os.path.isfile(path):
            os.remove(path)
            removed = True
    return removed


def setup_gemini():
    """Claude CLI subscription (name kept for call-site compatibility)."""
    _shared = Path(__file__).resolve().parents[2] / "shared"
    if str(_shared) not in sys.path:
        sys.path.insert(0, str(_shared))
    from site_llm import setup_claude_model

    return setup_claude_model()

# JSON/Markdown 정제 함수
def clean_json_response(text):
    # 마크다운 코드 블록 제거
    text = text.replace("```json", "").replace("```markdown", "").replace("```", "").strip()
    
    # JSON 객체 부분만 추출 시도
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end != -1:
        text = text[start:end]
        
    # 제어 문자 제거 (줄바꿈 제외)
    return re.sub(r'[\x00-\x09\x0b-\x1f\x7f]', '', text)