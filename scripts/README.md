# KR Campus Scripts

Content pipeline and maintenance utilities. Run from repo root.

## Core pipeline (deploy order)

| Script | Purpose |
|--------|---------|
| `1.collect_language_schools.py` | Collect language institute data → CSV |
| `1.collect_universities.py` | Collect university data → CSV |
| `2.generate_ai_guides.py` | Generate guide markdown from `data/guide_topics.csv` |
| `3.create_japanese_content.py` | Translate EN content → `*_ja.md` |
| `build_data.py` | Build `app/static/json/schools_data*.json` from markdown |

Typical sequence:

```bash
python3 scripts/2.generate_ai_guides.py
python3 scripts/1.collect_language_schools.py
python3 scripts/1.collect_universities.py
python3 scripts/3.create_japanese_content.py
python3 scripts/build_data.py
```

## Shared utilities

| Script | Purpose |
|--------|---------|
| `common.py` | Paths, Gemini setup, logging, JSON cleanup |
| `content_specs.py` | Content generation specs |
| `content_generator.py` | Shared generator helpers |
| `md_dates.py` | Frontmatter date utilities |
| `batch_limits.py` | API batch rate limits |

## Images & assets

| Script | Purpose |
|--------|---------|
| `fetch_images.py` | Fetch school/university images |
| `ensure_item_images.py` | Ensure image files exist for items |
| `optimize_images.py` | Compress/resize images |
| `build_social_images.py` | Pre-render social share JPEGs |
| `generate_favicons.py` | Generate favicon set |

## SEO & content expansion

| Script | Purpose |
|--------|---------|
| `seo_guard.py` | Validate SEO metadata across pages |
| `optimize_meta_copy.py` | Tune meta titles/descriptions |
| `seed_guides.py` | Seed guide topics |
| `seed_japanese_content.py` | Seed JA translations |
| `expand_seeds.py` | Expand seed topics |
| `expand_all_content.py` | Bulk content expansion |
| `generate_longtail_seed.py` | Long-tail topic seeds |
| `topic_queue_csv.py` | Manage topic queue CSV |
| `auto_generate_featured.py` | Mark featured guides |

## One-off / alternate flows

| Script | Purpose |
|--------|---------|
| `3.create_korean_content.py` | Legacy KR content script (superseded by JA flow) |
| `3.generate_japanese_native.py` | Native JA generation variant |
| `bulk_generate_ja.py` | Bulk JA translation |
| `geocode_locations.py` | Geocode school addresses |
| `archive/_patch_krcampus.py` | One-time jpcampus → krcampus migration (historical) |
