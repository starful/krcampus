# KR Campus

Study in Korea — jpcampus-style site (FastAPI + map + guides + schools).

## CSV (same pattern as jpcampus)

| File | Purpose |
|------|---------|
| `data/guide_topics.csv` | Study-abroad guides → `guide_*.md` |
| `data/language_schools.csv` | Korean language institutes → `school_*.md` |
| `data/universities.csv` | Universities → `univ_*.md` |

## Languages

- **English** — source `*.md`
- **Japanese** — translation `*_ja.md` via `scripts/3.create_japanese_content.py`

## Local run

```bash
cd /opt/work/krcampus
cp .env.example .env   # set GEMINI_API_KEY, KRCAMPUS_GOOGLE_MAPS_API_KEY
pip install -r requirements.txt
python3 scripts/build_data.py
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

Maps: set `KRCAMPUS_GOOGLE_MAPS_API_KEY` in `.env` (local) or Secret Manager `KRCAMPUS_GOOGLE_MAPS_API_KEY` (Cloud Run).

Open http://127.0.0.1:8080

## Routes

- `/` — map + featured schools/universities/guides
- `/schools` — language institutes
- `/universities` — universities
- `/guide` — study guides
- `/school/{id}` — school/university detail

## Deploy

```bash
./deploy.sh --content-only
./deploy.sh --deploy-only --with-git --with-deploy
```

## OK Admin

`krcampus` in `sites.yaml` — pipeline: guides → language schools → universities → JA → build.
