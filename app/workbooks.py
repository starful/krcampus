"""Free printable workbooks (PDF lead magnets), ported from jpcampus.

No PDFs exist yet for KR Campus — WORKBOOK_FILES/GUIDE_WORKBOOKS stay empty
until real files are added under app/static/workbooks/, at which point
workbook_context() starts returning items for the matching guide/stay pages.
"""

from __future__ import annotations

from typing import Any

from app.affiliate import normalize_guide_slug
from app.i18n import get_ui_text

WORKBOOK_FILES: dict[str, str] = {}

GUIDE_WORKBOOKS: dict[str, tuple[str, ...]] = {}


def workbook_href(workbook_id: str) -> str:
    filename = WORKBOOK_FILES[workbook_id]
    return f"/static/workbooks/{filename}"


def workbook_context(
    lang: str,
    *,
    guide_slug: str | None = None,
    page_kind: str | None = None,
) -> dict[str, Any]:
    ids: tuple[str, ...] = ()
    if page_kind in {"stays_list", "stay_detail"}:
        ids = GUIDE_WORKBOOKS.get("housing", ())
    elif guide_slug:
        ids = GUIDE_WORKBOOKS.get(normalize_guide_slug(guide_slug), ())

    if not ids:
        return {"workbooks": []}

    ui = get_ui_text(lang)
    items = []
    for workbook_id in ids:
        filename = WORKBOOK_FILES[workbook_id]
        items.append(
            {
                "id": workbook_id,
                "href": workbook_href(workbook_id),
                "filename": filename,
                "title": ui[f"workbook_{workbook_id}_title"],
                "desc": ui[f"workbook_{workbook_id}_desc"],
            }
        )
    return {"workbooks": items}
