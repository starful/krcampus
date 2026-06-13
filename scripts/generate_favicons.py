#!/usr/bin/env python3
"""Generate KR Campus logo + favicon assets from source PNG."""
from __future__ import annotations

import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Pillow required: pip install Pillow", file=sys.stderr)
    raise SystemExit(1)

ROOT = Path(__file__).resolve().parent.parent
IMG_DIR = ROOT / "app" / "static" / "img"
DEFAULT_SRC = Path(
    "/Users/starful/.cursor/projects/opt-work-okadmin/assets/"
    "image-966240b0-d2f9-4229-82c1-758c7f66644f.png"
)


def content_bbox(img: Image.Image) -> tuple[int, int, int, int]:
    pixels = img.load()
    w, h = img.size
    minx, miny, maxx, maxy = w, h, 0, 0
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if a > 10 and (r < 250 or g < 250 or b < 250):
                minx = min(minx, x)
                miny = min(miny, y)
                maxx = max(maxx, x)
                maxy = max(maxy, y)
    return minx, miny, maxx, maxy


def crop_icon(img: Image.Image, bbox: tuple[int, int, int, int]) -> Image.Image:
    minx, miny, maxx, maxy = bbox
    height = maxy - miny + 1
    icon_w = int(height * 1.35)
    icon = img.crop((minx, miny, minx + icon_w, maxy + 1))
    side = max(icon.size)
    square = Image.new("RGBA", (side, side), (255, 255, 255, 0))
    ox = (side - icon.size[0]) // 2
    oy = (side - icon.size[1]) // 2
    square.paste(icon, (ox, oy), icon)
    return square


def crop_wordmark(img: Image.Image, bbox: tuple[int, int, int, int], pad: int = 24) -> Image.Image:
    minx, miny, maxx, maxy = bbox
    return img.crop((max(0, minx - pad), max(0, miny - pad), minx + (maxx - minx) + pad, maxy + pad + 1))


def save_ico(icon: Image.Image, path: Path) -> None:
    sizes = [(16, 16), (32, 32), (48, 48)]
    icon.save(path, format="ICO", sizes=sizes)


def main(src: Path = DEFAULT_SRC) -> None:
    if not src.is_file():
        print(f"Source not found: {src}", file=sys.stderr)
        raise SystemExit(1)

    IMG_DIR.mkdir(parents=True, exist_ok=True)
    img = Image.open(src).convert("RGBA")
    bbox = content_bbox(img)
    icon = crop_icon(img, bbox)
    wordmark = crop_wordmark(img, bbox)

    # Header logo (~320px wide)
    logo = wordmark.copy()
    logo.thumbnail((640, 160), Image.Resampling.LANCZOS)
    logo.save(IMG_DIR / "logo.png", optimize=True)

    # Favicon sizes from icon mark only
    base = icon.resize((512, 512), Image.Resampling.LANCZOS)
    save_ico(base, IMG_DIR / "favicon.ico")
    base.resize((16, 16), Image.Resampling.LANCZOS).save(IMG_DIR / "favicon-16x16.png", optimize=True)
    base.resize((32, 32), Image.Resampling.LANCZOS).save(IMG_DIR / "favicon-32x32.png", optimize=True)
    base.resize((48, 48), Image.Resampling.LANCZOS).save(IMG_DIR / "favicon-48x48.png", optimize=True)
    base.resize((180, 180), Image.Resampling.LANCZOS).save(IMG_DIR / "apple-touch-icon.png", optimize=True)
    base.resize((192, 192), Image.Resampling.LANCZOS).save(IMG_DIR / "android-chrome-192x192.png", optimize=True)
    base.resize((512, 512), Image.Resampling.LANCZOS).save(IMG_DIR / "android-chrome-512x512.png", optimize=True)

    # OG / social preview
    og = Image.new("RGBA", (1200, 630), (255, 255, 255, 255))
    mark = wordmark.copy()
    mark.thumbnail((900, 220), Image.Resampling.LANCZOS)
    ox = (1200 - mark.size[0]) // 2
    oy = (630 - mark.size[1]) // 2
    og.paste(mark, (ox, oy), mark)
    og.save(IMG_DIR / "og_image.png", optimize=True)

    print(f"Wrote assets to {IMG_DIR}")


if __name__ == "__main__":
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SRC
    main(src)
