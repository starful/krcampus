# KR Campus Scripts

Content pipeline and maintenance utilities. Run from repo root.

## Official pipeline (deploy order)

Use this sequence for content updates:

```bash
python3 scripts/2.generate_ai_guides.py          # optional: new guides from CSV
python3 scripts/1.collect_language_schools.py    # optional: refresh school CSV
python3 scripts/1.collect_universities.py        # optional: refresh university CSV
python3 scripts/3.create_japanese_content.py     # EN → *_ja.md translations
python3 scripts/build_data.py                    # MD → schools_data*.json
python3 scripts/build_social_images.py           # guide OG JPEGs (skips up-to-date)
python3 scripts/seo_guard.py                     # pre-deploy checks
```

Or use `./deploy.sh --full` which runs the content steps above plus deploy.

| Script | Purpose |
|--------|---------|
| `1.collect_language_schools.py` | Collect language institute data → CSV |
| `1.collect_universities.py` | Collect university data → CSV |
| `2.generate_ai_guides.py` | Generate guide markdown from `data/guide_topics.csv` |
| `3.create_japanese_content.py` | **Primary** EN → `*_ja.md` translation |
| `build_data.py` | Build `app/static/json/schools_data*.json` (skips if up to date) |
| `build_social_images.py` | Pre-render guide social JPEGs (skips if up to date) |
| `seo_guard.py` | Validate SEO metadata across pages |

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
| `generate_favicons.py` | Generate favicon set |

## SEO & content expansion

| Script | Purpose |
|--------|---------|
| `optimize_meta_copy.py` | Tune meta titles/descriptions |
| `seed_guides.py` | Seed guide topics |
| `seed_japanese_content.py` | Offline JA seed copy |
| `expand_seeds.py` | Expand seed topics |
| `expand_all_content.py` | Bulk content expansion |
| `auto_generate_featured.py` | Generate curated featured guides |
| `generate_longtail_seed.py` | Long-tail topic seeds |
| `topic_queue_csv.py` | Manage topic queue CSV |

## Alternate / legacy flows

| Script | Purpose |
|--------|---------|
| `3.generate_japanese_native.py` | Native JA MD for sources missing `*_ja.md` |
| `3.create_korean_content.py` | Legacy KR translation (rarely used) |
| `geocode_locations.py` | Geocode school addresses |
| `archive/bulk_generate_ja.py` | **Deprecated** — use `3.create_japanese_content.py` |
| `archive/_patch_krcampus.py` | One-time jpcampus → krcampus migration (historical) |
