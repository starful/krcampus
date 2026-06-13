#!/usr/bin/env python3
"""Pre-generate guide social card JPEGs into app/static/social at build time."""
from __future__ import annotations

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.main import DOMAIN, GCS_IMAGE_BASE
from app.social_share import (
    fetch_social_jpeg,
    load_guide_item,
    resolve_thumbnail_url,
    static_social_image_key,
)

CONTENT_DIR = os.path.join(BASE_DIR, "app", "content")
OUTPUT_DIR = os.path.join(BASE_DIR, "app", "static", "social")


def guide_slugs() -> list[str]:
    slugs: set[str] = set()
    for filename in os.listdir(CONTENT_DIR):
        if not filename.startswith("guide_") or not filename.endswith(".md"):
            continue
        if filename.endswith("_ja.md"):
            continue
        slugs.add(filename[len("guide_") : -3])
    return sorted(slugs)


def build_guide_images() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ok = 0
    failed: list[str] = []
    for slug in guide_slugs():
        image_key = static_social_image_key("guide", slug)
        output_path = os.path.join(OUTPUT_DIR, f"{image_key}.jpg")
        try:
            item = load_guide_item(slug, "en")
            source = resolve_thumbnail_url(
                DOMAIN, item, "guide", guide_slug=slug, gcs_base=GCS_IMAGE_BASE
            )
            data = fetch_social_jpeg(source)
            with open(output_path, "wb") as handle:
                handle.write(data)
            ok += 1
        except Exception as exc:
            failed.append(f"{slug}: {exc}")
    print(f"✅ Built {ok} guide social images in {OUTPUT_DIR}")
    if failed:
        print(f"⚠️  Skipped {len(failed)} guides:")
        for line in failed[:10]:
            print(f"   - {line}")
        if len(failed) > 10:
            print(f"   ... and {len(failed) - 10} more")


if __name__ == "__main__":
    build_guide_images()
