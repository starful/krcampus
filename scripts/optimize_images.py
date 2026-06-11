"""Resize/compress Places photos before GCS upload."""

import os

from PIL import Image

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIR = os.path.join(BASE_DIR, "app", "static", "images")
EXCLUDE = {"logo.png", "logo.svg", "favicon.ico", "og_image.png", "default.png"}
MAX_WIDTH = 800
QUALITY = 75


def optimize_images():
    if not os.path.isdir(IMAGES_DIR):
        print(f"images dir missing: {IMAGES_DIR}")
        return

    ok = skip = 0
    for filename in os.listdir(IMAGES_DIR):
        if filename in EXCLUDE:
            continue
        ext = os.path.splitext(filename)[1].lower()
        if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
            continue

        filepath = os.path.join(IMAGES_DIR, filename)
        try:
            with Image.open(filepath) as img:
                if img.width <= MAX_WIDTH and ext == ".jpg":
                    skip += 1
                    continue
                rgb = img.convert("RGB")
                if rgb.width > MAX_WIDTH:
                    ratio = MAX_WIDTH / rgb.width
                    rgb = rgb.resize((MAX_WIDTH, int(rgb.height * ratio)), Image.Resampling.LANCZOS)

            out_name = os.path.splitext(filename)[0] + ".jpg"
            out_path = os.path.join(IMAGES_DIR, out_name)
            rgb.save(out_path, "JPEG", quality=QUALITY, optimize=True)
            if filename != out_name:
                os.remove(filepath)
            ok += 1
        except Exception as exc:
            print(f"error ({filename}): {exc}")

    print(f"optimize done — updated:{ok} skip:{skip}")


if __name__ == "__main__":
    optimize_images()
