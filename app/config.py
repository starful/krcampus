import os

from app.settings import KRCAMPUS_GOOGLE_MAPS_API_KEY

SITE_CONFIG = {
    "project_name": "krcampus",
    "site_name": "KR Campus",
    "site_url": os.getenv("SITE_URL", "https://krcampus.net"),
    "tagline": "Study in Korea — Guides for International Students",
    "data_key": "items",
    "guides_only": True,
    "ga_id": os.getenv("GA_MEASUREMENT_ID", os.getenv("GA_ID", "G-ZTC8BNMCRR")),
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
