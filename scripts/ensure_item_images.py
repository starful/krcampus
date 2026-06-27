"""MD가 있는 school/univ 중 썸네일이 없으면 default를 slug.jpg로 복사 (GCS rsync 대상)."""

import os
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
IMAGES_DIR = os.path.join(BASE_DIR, "app", "static", "images")
IMG_DIR = os.path.join(BASE_DIR, "app", "static", "img")
CONTENT_DIR = os.path.join(BASE_DIR, "app", "content")

DEFAULT_CANDIDATES = (
    "default.png",
    "default.jpg",
    "default-school.png",
    "default-univ.png",
)
PIN_CANDIDATES = {
    "school": ("pin-school.png", "default-school.png", "default.png", "default.jpg"),
    "univ": ("pin-univ.png", "default-univ.png", "default.png", "default.jpg"),
}
PROTECTED = {"logo.png", "logo.svg", "favicon.ico", "og_image.png", "default.png", "default.jpg"}


def _resolve_source(category: str) -> str | None:
    for name in PIN_CANDIDATES.get(category, DEFAULT_CANDIDATES):
        for base in (IMAGES_DIR, IMG_DIR):
            path = os.path.join(base, name)
            if os.path.isfile(path):
                return path
    for name in DEFAULT_CANDIDATES:
        path = os.path.join(IMAGES_DIR, name)
        if os.path.isfile(path):
            return path
    return None


def collect_content_slugs() -> set[str]:
    slugs: set[str] = set()
    if not os.path.isdir(CONTENT_DIR):
        return slugs
    for filename in sorted(os.listdir(CONTENT_DIR)):
        if filename.endswith("_ja.md"):
            continue
        if not (filename.startswith("school_") or filename.startswith("univ_")):
            continue
        if not filename.endswith(".md"):
            continue
        slugs.add(filename[:-3])
    return slugs


def ensure_item_images(*, slugs: set[str] | None = None) -> dict[str, int]:
    os.makedirs(IMAGES_DIR, exist_ok=True)
    targets = sorted(slugs if slugs is not None else collect_content_slugs())
    copied = skipped = failed = 0

    print(f"\n📋 default placeholder — {len(targets)}개 slug 확인\n")

    for slug in targets:
        if not slug:
            continue
        filename = f"{slug}.jpg"
        if filename in PROTECTED:
            continue
        target = os.path.join(IMAGES_DIR, filename)
        if os.path.isfile(target):
            skipped += 1
            continue

        category = "univ" if slug.startswith("univ_") else "school"
        source = _resolve_source(category)
        if not source:
            print(f"  ❌ {filename}: default 이미지 없음")
            failed += 1
            continue
        try:
            shutil.copy2(source, target)
            copied += 1
            print(f"  ✅ {filename} ← {os.path.basename(source)}")
        except OSError as exc:
            failed += 1
            print(f"  ❌ {filename}: {exc}")

    print("\n" + "─" * 50)
    print(f"📋 placeholder 완료 — 생성: {copied} / 기존: {skipped} / 실패: {failed}")
    print("─" * 50)
    return {"copied": copied, "skipped": skipped, "failed": failed}


if __name__ == "__main__":
    ensure_item_images()
