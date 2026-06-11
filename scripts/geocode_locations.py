#!/usr/bin/env python3
"""Backfill lat/lng for school/university markdown (Google Geocoding + OSM fallback)."""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

import frontmatter
import requests
from dotenv import load_dotenv

from common import maps_api_key

load_dotenv()

BASE = Path(__file__).resolve().parent.parent
CONTENT = BASE / "app" / "content"
CACHE_PATH = BASE / "scripts" / "logs" / "geocode_cache.json"
DEFAULT = (37.5665, 126.978)
API_KEY = maps_api_key()
SLEEP_NOMINATIM = float(os.getenv("GEOCODE_SLEEP", "1.05"))
USER_AGENT = "KR Campus Geocoder/1.0 (https://krcampus.net; contact@krcampus.net)"


def is_default(loc: dict | None) -> bool:
    if not loc or loc.get("lat") is None or loc.get("lng") is None:
        return True
    return abs(float(loc["lat"]) - DEFAULT[0]) < 0.0001 and abs(float(loc["lng"]) - DEFAULT[1]) < 0.0001


def load_cache() -> dict[str, dict]:
    if CACHE_PATH.is_file():
        try:
            return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_cache(cache: dict[str, dict]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def extract_city(address: str) -> str:
    if not address:
        return ""
    for token in ("Seoul", "Busan", "Daegu", "Incheon", "Gwangju", "Daejeon", "Ulsan", "Jeju", "Suwon", "Yongin", "Cheonan", "Pohang", "Chuncheon", "Jeonju"):
        if token.lower() in address.lower():
            return token
    m = re.search(r",\s*([^,]+),\s*(?:South Korea|Republic of Korea|Korea)", address)
    return m.group(1).strip() if m else ""


def build_queries(meta: dict) -> list[str]:
    basic = meta.get("basic_info") or {}
    name = (basic.get("name_en") or meta.get("title") or "").strip()
    address = (basic.get("address") or meta.get("address") or "").strip()
    city = extract_city(address)
    queries = []
    if address:
        queries.append(re.sub(r"\([^)]*\)", "", address).strip())
    if name:
        queries.append(f"{name}, South Korea")
        if city:
            queries.append(f"{name}, {city}, South Korea")
    seen = set()
    out = []
    for q in queries:
        q = q.strip(" ,")
        if q and q not in seen:
            seen.add(q)
            out.append(q)
    return out


def geocode_google(query: str) -> dict | None:
    if not API_KEY:
        return None
    try:
        res = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": query, "key": API_KEY, "region": "kr"},
            timeout=10,
        )
        data = res.json()
        if data.get("status") == "OK" and data.get("results"):
            loc = data["results"][0]["geometry"]["location"]
            return {"lat": loc["lat"], "lng": loc["lng"]}
    except Exception:
        pass
    return None


def geocode_nominatim(query: str) -> dict | None:
    try:
        res = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": query, "format": "json", "limit": 1, "countrycodes": "kr"},
            headers={"User-Agent": USER_AGENT},
            timeout=15,
        )
        rows = res.json()
        if rows:
            return {"lat": float(rows[0]["lat"]), "lng": float(rows[0]["lon"])}
    except Exception:
        pass
    return None


def geocode(meta: dict, cache: dict[str, dict]) -> dict | None:
    for query in build_queries(meta):
        if query in cache:
            return cache[query]
        coords = geocode_google(query)
        if coords:
            cache[query] = coords
            return coords
        coords = geocode_nominatim(query)
        time.sleep(SLEEP_NOMINATIM)
        if coords:
            cache[query] = coords
            return coords
    return None


def school_files() -> list[Path]:
    return sorted(
        p for p in CONTENT.glob("*.md")
        if (p.name.startswith("school_") or p.name.startswith("univ_")) and not p.name.endswith("_ja.md")
    )


def update_file(path: Path, coords: dict) -> None:
    post = frontmatter.load(path)
    meta = dict(post.metadata)
    meta["location"] = coords
    path.write_text(frontmatter.dumps(frontmatter.Post(post.content, **meta)), encoding="utf-8")


def main() -> None:
    if not API_KEY:
        print("WARN: KRCAMPUS_GOOGLE_MAPS_API_KEY missing — using slow OSM Nominatim (~1 req/s)")
    elif geocode_google("Seoul, South Korea") is None:
        print("WARN: Google Geocoding key invalid/expired — using slow OSM Nominatim (~1 req/s)")

    cache = load_cache()
    updated = skipped = failed = 0

    for en_path in school_files():
        post = frontmatter.load(en_path)
        meta = post.metadata or {}
        if not is_default(meta.get("location")):
            skipped += 1
            continue

        coords = geocode(meta, cache)
        if not coords:
            print(f"FAIL {en_path.name}")
            failed += 1
            continue

        update_file(en_path, coords)
        ja_path = en_path.with_name(en_path.stem + "_ja.md")
        if ja_path.is_file():
            update_file(ja_path, coords)

        print(f"OK   {en_path.name} -> {coords['lat']:.5f}, {coords['lng']:.5f}")
        updated += 1

    save_cache(cache)
    print(f"\nDone: updated={updated}, skipped={skipped}, failed={failed}")


if __name__ == "__main__":
    main()
