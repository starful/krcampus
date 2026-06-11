import os

from dotenv import load_dotenv

load_dotenv()

KRCAMPUS_GOOGLE_MAPS_API_KEY = os.getenv("KRCAMPUS_GOOGLE_MAPS_API_KEY") or ""
