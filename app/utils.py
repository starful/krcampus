"""Backward-compatible re-exports — prefer `app.content_loader`, `app.i18n`, etc."""

from app.compare import (
    build_compare_export,
    compare_city,
    compare_fee_label,
    compare_fee_value,
    prepare_compare_items,
)
from app.content_loader import load_guides, load_school_data
from app.filters import (
    calculate_tag_counts,
    get_category_filters,
    get_quick_filters,
    get_region_filters,
    get_school_feature_filters,
    get_type_filters,
)
from app.http_utils import get_client_ip
from app.i18n import get_ui_text
from app.paths import BASE_DIR, CONTENT_DIR, STATIC_DIR, TEMPLATES_DIR
from app.thumbnails import (
    assign_thumbnails,
    diversify_guide_thumbnails,
    resolve_guide_detail_thumbnail,
    resolve_guide_list_thumbnail,
    resolve_guide_thumbnail,
)

__all__ = [
    "BASE_DIR",
    "STATIC_DIR",
    "CONTENT_DIR",
    "TEMPLATES_DIR",
    "calculate_tag_counts",
    "assign_thumbnails",
    "get_ui_text",
    "get_type_filters",
    "get_category_filters",
    "get_school_feature_filters",
    "get_region_filters",
    "get_quick_filters",
    "load_school_data",
    "load_guides",
    "resolve_guide_detail_thumbnail",
    "resolve_guide_list_thumbnail",
    "resolve_guide_thumbnail",
    "diversify_guide_thumbnails",
    "prepare_compare_items",
    "compare_fee_value",
    "compare_fee_label",
    "compare_city",
    "build_compare_export",
    "get_client_ip",
]
