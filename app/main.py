import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.context import configure_templates
from app.middleware import (
    ga4_pageview_middleware,
    lang_kr_alias_middleware,
    legacy_redirect_middleware,
)
from app.paths import CONTENT_DIR, STATIC_DIR
from app.reactions import router as reactions_router
from app.routes import assets, pages, seo_routes
from app.settings import DOMAIN, GCS_IMAGE_BASE  # re-exported for scripts/tests
from app.waitlist import router as waitlist_router

app = FastAPI()

if not os.path.exists(CONTENT_DIR):
    os.makedirs(CONTENT_DIR)

configure_templates()

app.middleware("http")(legacy_redirect_middleware)
app.middleware("http")(lang_kr_alias_middleware)
app.middleware("http")(ga4_pageview_middleware)

app.include_router(reactions_router, prefix="/api")
app.include_router(waitlist_router, prefix="/api")
app.include_router(assets.router)
app.include_router(seo_routes.router)
app.include_router(pages.router)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Anonymous visit log for Starful HQ「이용자 보기」
from pathlib import Path as _Path
import logging as _logging
import sys as _sys
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
try:
    from visitkit.fastapi_api import register_visitlog
    register_visitlog(app, site_id="krcampus", db_path=_Path(__file__).resolve().parents[1] / "data" / "visitlog.sqlite3")
except Exception as _exc:  # keep site up if visitkit missing
    _logging.getLogger("krcampus").warning("visitlog not registered: %s", _exc)
