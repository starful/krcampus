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

SITE_CONFIG = {
    "project_name": "krcampus",
    "site_name": SITE_NAME,
    "site_url": DOMAIN,
    "tagline": "Study in Korea — Guides for International Students",
    "data_key": "items",
    "guides_only": True,
    "ga_id": GA_MEASUREMENT_ID,
    "maps_api_key": KRCAMPUS_GOOGLE_MAPS_API_KEY,
    "maps_id": os.getenv("MAPS_ID", ""),
    "emoji": "🇰🇷",
    "accent_color": "#0047a0",
    "bg_dot_color": "#c8102e",
    "filter_buttons": [],
    "category_mapping": {},
    "js_category_map": {},
    "schema_type": "EducationalOrganization",
    "guide_images": [
        "https://images.unsplash.com/photo-1517154428173-9837736a2afc?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1583417319070-4a3bb38baef9?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1493976040374-85c8e912ba4a?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1540959733332-eab4deab981a?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1534274867514-d5c4dacf1695?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1559827260-dc66d52bef19?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1528183429752-a97d0bf99b5a?q=80&w=800&auto=format&fit=crop",
    ],
    "footer_tagline": "Practical guides for studying in Korea.",
    "footer_year": "2026",
    "partner_site": {
        "name": "JP Campus",
        "url": "https://jpcampus.net",
    },
}


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
