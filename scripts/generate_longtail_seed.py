#!/usr/bin/env python3
import csv
import json
import os
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_CSV = os.path.join(BASE_DIR, "data", "longtail_topics_seed_20.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "app", "content")

DEFAULT_THUMBNAIL = "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=500"


def make_frontmatter(row: dict) -> dict:
    return {
        "layout": "guide",
        "id": row["slug"],
        "title": row["title"],
        "category": row["category"],
        "lang": "en",
        "tags": ["Longtail", row["goal"], row["city"]],
        "description": row["description"],
        "thumbnail": DEFAULT_THUMBNAIL,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }


def make_body(row: dict) -> str:
    city = row["city"]
    goal = row["goal"]
    budget = row["budget"]
    budget_text = {
        "low": "budget-sensitive profile",
        "medium": "balanced budget profile",
        "high": "premium budget profile",
    }.get(budget, "balanced budget profile")

    return f"""# {row["title"]}

This guide is designed for international students with a **{budget_text}** who are focusing on **{goal}** in **{city}**.
It helps you compare options quickly without losing sight of visa timelines, housing setup, and academic goals.

## Who This Guide Is For

- Students comparing schools by city, commuting, and living cost.
- Students trying to reduce trial-and-error before final school selection.
- Students who need a practical shortlist before contacting admissions teams.

## How to Compare Your Options

Use these filters first:

| Filter | Why It Matters | What to Check |
|---|---|---|
| Tuition | Total budget fit | annual tuition + fees |
| Location | Daily commute and jobs | train access + neighborhood |
| Program Fit | Learning outcome speed | JLPT/EJU/business track |
| Housing | Setup friction | dorm availability + move-in support |

Then compare with these pages:

- [All Language Schools](/schools)
- [All Universities](/universities)
- [Essential Guides](/guide)

## Recommended Decision Process

1. Build a shortlist of 5-8 options.
2. Narrow to 3 options with tuition + location fit.
3. Contact schools for latest intake and seat availability.
4. Confirm housing and visa document deadlines.

## Common Mistakes to Avoid

- Choosing only by tuition and ignoring transit/lifestyle costs.
- Ignoring language-level mismatch between current level and class pace.
- Delaying application documents until peak season.

## Final Checklist

- Can I sustain this plan for at least 12 months?
- Is the program track aligned with my final objective?
- Do I have a backup option in another city?

For broader preparation, also read:

- [Student Monthly Cost Guide](/guide/japan-student-monthly-cost-by-city)
- [Housing Setup Guide](/guide/japan-dormitory-vs-sharehouse-students)
- [Visa Basics](/guide/visa)
"""


def main() -> None:
    if not os.path.exists(DATA_CSV):
        raise FileNotFoundError(f"Missing topic seed file: {DATA_CSV}")
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    created = 0
    skipped = 0
    with open(DATA_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            slug = row["slug"].strip()
            if not slug:
                continue
            filepath = os.path.join(OUTPUT_DIR, f"guide_{slug}.md")
            if os.path.exists(filepath):
                skipped += 1
                continue

            frontmatter = make_frontmatter(row)
            body = make_body(row)
            with open(filepath, "w", encoding="utf-8") as out:
                out.write("---\n")
                out.write(json.dumps(frontmatter, ensure_ascii=False, indent=2))
                out.write("\n---\n\n")
                out.write(body)
            created += 1

    print(f"Longtail seed generation done. Created={created}, Skipped={skipped}")


if __name__ == "__main__":
    main()
