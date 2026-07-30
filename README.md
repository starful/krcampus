# KR Campus

**Study in Korea** — map-first platform for language schools, universities, and study-abroad guides. Sister site to [JP Campus](https://jpcampus.net) with a Korea focus and Japanese translations.

| | |
|--|--|
| **Live** | [https://krcampus.net](https://krcampus.net) |
| **GitHub** | [starful/krcampus](https://github.com/starful/krcampus) |
| **Hub ID** | `krcampus` |
| **GA4** | Property `540991708` · GSC `sc-domain:krcampus.net` |

## Features

- Interactive map + list UI for schools and universities
- Markdown CMS under `app/content` (guides, schools, universities)
- **English** source content; **Japanese** via `scripts/3.generate_japanese_native.py`
- SEO: canonical URLs, hreflang, sitemap, `scripts/seo_guard.py` in deploy pipeline
- Bilingual UI (`?lang=` / i18n JSON)

## Tech stack

- **Backend:** Python 3.11+, FastAPI, Uvicorn
- **Frontend:** Jinja2, vanilla JS, Google Maps
- **Data:** Markdown → `scripts/build_data.py` → `app/static/json/`
- **Infra:** Docker, Cloud Build, Cloud Run
- **AI:** Gemini (guide/school generation scripts)

## Content sources

| CSV | Output |
|-----|--------|
| `data/guide_topics.csv` | `guide_*.md` |
| `data/language_schools.csv` | `school_*.md` |
| `data/universities.csv` | `univ_*.md` |

## OK Admin pipeline

Order (configurable via env limits): AI guides → language schools → universities → (optional JA) → featured → images → optimize → build → optional SEO guard.

Run from Hub **Content** tab or locally:

```bash
cd /opt/work/krcampus
pip install -r requirements.txt
cp .env.example .env   # GEMINI_API_KEY, KRCAMPUS_GOOGLE_MAPS_API_KEY
python3 scripts/build_data.py
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

## Deploy

```bash
./deploy.sh --content-only              # generate + build
./deploy.sh --deploy-only               # Cloud Run only
./deploy.sh --deploy-only --with-git --with-deploy
```

Modes: `--full`, `--content-only`, `--deploy-only`. Options: `--with-git`, `--with-deploy`.

Production deploy: merge to `main`, pull locally, then OK Admin **④ Deploy** or `./deploy.sh --deploy-only`.

## GCS images

- Bucket: `ok-project-assets` · prefix: `krcampus/`
- Places types: `university`, `school`

## Routes

- `/` — map + featured content
- `/schools`, `/universities`, `/guide`
- `/school/{id}` — detail pages

## Tests

```bash
pytest tests/
```

## Related

- Registry: `/opt/work/sites.yaml`
- Ops hub: [okadmin](../okadmin/README.md) · Ship workflow: [CONTRIBUTING](../okadmin/CONTRIBUTING.md)
