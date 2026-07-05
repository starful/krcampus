import json
import os
from pathlib import Path

from dotenv import load_dotenv

from app.paths import BASE_DIR

load_dotenv()

KRCAMPUS_GOOGLE_MAPS_API_KEY = os.getenv("KRCAMPUS_GOOGLE_MAPS_API_KEY") or ""

DOMAIN = (
    os.getenv("SITE_DOMAIN")
    or os.getenv("SITE_URL", "https://krcampus.net")
).rstrip("/")

GCS_IMAGE_BASE = os.getenv(
    "GCS_IMAGE_BASE",
    "https://storage.googleapis.com/ok-project-assets/krcampus",
)

ADS_TXT_CONTENT = os.getenv(
    "ADS_TXT_CONTENT",
    "google.com, pub-8780435268193938, DIRECT, f08c47fec0942fa0",
)

GA_MEASUREMENT_ID = os.getenv("GA_MEASUREMENT_ID", "G-ZTC8BNMCRR")
ADSENSE_CLIENT_ID = os.getenv("ADSENSE_CLIENT_ID", "ca-pub-8780435268193938")

REDIRECT_MAP_PATH = Path(BASE_DIR) / "redirects.json"

FAMILY_SITE_ID = "krcampus"
SITE_NAME = "KR Campus"

SCHOOL_ID_ALIASES = {
    "univ_ulsan-national-institute-of-science-and-technology": "univ_unist-ulsan-national-institute-of-science-and-technology",
    "univ_ulsan-national-institute-of-science-and-technology-unist": "univ_unist-ulsan-national-institute-of-science-and-technology",
    "school_yonsei-kli": "school_yonsei-university-korean-language-institute",
    "school_snu-lei": "school_seoul-national-university-language-education-institute",
}

_LOCAL_IMAGE_NAMES = frozenset({
    "logo.png", "logo.svg", "favicon.ico", "og_image.png",
    "pin-school.png", "pin-univ.png",
})


def load_redirect_map() -> dict[str, str]:
    if not REDIRECT_MAP_PATH.exists():
        return {}
    try:
        with open(REDIRECT_MAP_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return {str(k): str(v) for k, v in data.items()}
    except Exception:
        pass
    return {}


REDIRECT_MAP = load_redirect_map()
