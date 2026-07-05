from urllib.parse import urlencode

from fastapi import Request
from fastapi.responses import RedirectResponse

from app.settings import REDIRECT_MAP


def redirect_target(path: str) -> str | None:
    normalized = path.rstrip("/") or "/"
    target = REDIRECT_MAP.get(normalized) or REDIRECT_MAP.get(f"{normalized}/")
    if not target:
        return None
    if not target.startswith("/"):
        return f"/{target}"
    if target == normalized:
        return None
    return target


async def lang_kr_alias_middleware(request: Request, call_next):
    """Redirect legacy ?lang=kr bookmarks to ?lang=ja."""
    if request.query_params.get("lang") == "kr":
        params = dict(request.query_params)
        params["lang"] = "ja"
        query = urlencode(params)
        redirect_url = f"{request.url.path}?{query}" if query else request.url.path
        return RedirectResponse(url=redirect_url, status_code=301)
    return await call_next(request)


async def legacy_redirect_middleware(request: Request, call_next):
    response = await call_next(request)
    if response.status_code != 404:
        return response
    if request.url.path.startswith("/api") or request.url.path.startswith("/static"):
        return response

    target = redirect_target(request.url.path)
    if not target:
        return response

    query = request.url.query
    redirect_url = f"{target}?{query}" if query and "?" not in target else target
    return RedirectResponse(url=redirect_url, status_code=301)
