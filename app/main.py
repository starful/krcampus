import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.context import configure_templates
from app.middleware import legacy_redirect_middleware
from app.paths import CONTENT_DIR, STATIC_DIR
from app.reactions import router as reactions_router
from app.routes import assets, pages, seo_routes
from app.settings import DOMAIN

app = FastAPI()

if not os.path.exists(CONTENT_DIR):
    os.makedirs(CONTENT_DIR)

configure_templates()

app.middleware("http")(legacy_redirect_middleware)

app.include_router(reactions_router, prefix="/api")
app.include_router(assets.router)
app.include_router(seo_routes.router)
app.include_router(pages.router)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
