#!/usr/bin/env python3
"""Seed guide_*.md files from data/guide_topics.csv (jpcampus format)."""
import csv
import json
import os
from datetime import date

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(BASE, "data", "guide_topics.csv")
OUT = os.path.join(BASE, "app", "content")

THUMBS = {
    "Visa": "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=500",
    "Budget": "https://images.unsplash.com/photo-1561414927-6d86591d0c4f?w=500",
    "Housing": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=500",
    "Selection": "https://images.unsplash.com/photo-1528164344705-47542687000d?w=500",
    "Preparation": "https://images.unsplash.com/photo-1501504905252-473c47e087f8?w=500",
    "Part-time": "https://images.unsplash.com/photo-1556740758-90de374c12ad?w=500",
    "Insurance": "https://images.unsplash.com/photo-1505751172876-fa1923c5c528?w=500",
    "Settlement": "https://images.unsplash.com/photo-1563986768609-322da13575f3?w=500",
    "Region": "https://images.unsplash.com/photo-1542051841857-5f90071e7989?w=500",
    "Exam": "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=500",
}


def body_for(row):
    slug = row["slug"]
    title = row["title"]
    desc = row["description"]
    return f"""## Overview

{desc}

This guide is part of **KR Campus** — practical resources for studying in Korea.

## Key points

- Plan visa and intake timing early
- Budget for tuition plus Seoul/Busan living costs
- Compare language institutes before you apply

## Next steps

Browse [language institutes](/schools) and [universities](/universities), or read more [Study in Korea guides](/guide).

*Topic: {slug} · {title}*
"""


def main():
    os.makedirs(OUT, exist_ok=True)
    today = date.today().isoformat()
    with open(CSV, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            slug = (row.get("slug") or "").strip()
            if not slug:
                continue
            path = os.path.join(OUT, f"guide_{slug}.md")
            if os.path.isfile(path):
                # Fix id in existing visa guide
                with open(path, encoding="utf-8") as fh:
                    txt = fh.read()
                if '"id": "guide_' in txt:
                    txt = txt.replace(f'"id": "guide_{slug}"', f'"id": "{slug}"')
                    txt = txt.replace(f"id: guide_{slug}", f"id: {slug}")
                    with open(path, "w", encoding="utf-8") as fh:
                        fh.write(txt)
                continue
            cat = row.get("category", "Guide")
            fm = {
                "layout": "guide",
                "id": slug,
                "title": row["title"],
                "category": cat,
                "tags": [cat],
                "description": row["description"],
                "thumbnail": THUMBS.get(cat, THUMBS["Budget"]),
                "date": today,
            }
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("---\n")
                fh.write(json.dumps(fm, ensure_ascii=False, indent=2))
                fh.write("\n---\n\n")
                fh.write(body_for(row))
            print(f"created {path}")


if __name__ == "__main__":
    main()
