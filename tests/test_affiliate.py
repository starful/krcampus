"""KR Campus affiliate: Amazon.jp + Coupang (EN/JA) + Klook."""

from app.affiliate import (
    AMAZON_TAG,
    COUPANG_CATEGORIES,
    DISCLOSURE_KO,
    GUIDE_AMAZON_MAP,
    GUIDE_COUPANG_MAP,
    GUIDE_KLOOK_SLUGS,
    affiliate_context,
    amazon_search_url,
    normalize_guide_slug,
)


def test_normalize_strips_prefixes():
    assert normalize_guide_slug("guide_packing-korea") == "packing-korea"
    assert normalize_guide_slug("packing-korea_ja") == "packing-korea"


def test_amazon_url_uses_co_jp_and_tag():
    url = amazon_search_url("TOPIK 問題集")
    assert "amazon.co.jp/s?k=" in url
    assert AMAZON_TAG in url


def test_english_shows_amazon_and_coupang():
    ctx = affiliate_context("dorm-application", lang="en")
    assert ctx["show_affiliate"] is True
    assert ctx["show_amazon"] is True
    assert ctx["show_coupang"] is True
    assert "amazon.co.jp" in ctx["amazon_search_url"]
    assert DISCLOSURE_KO in ctx["affiliate_disclosure"]


def test_japanese_lifestyle_shows_amazon_and_coupang():
    ctx = affiliate_context("dorm-application", lang="ja")
    assert ctx["show_amazon"] is True
    assert ctx["show_coupang"] is True
    assert ctx["affiliate_category"] == "home_interior"
    assert DISCLOSURE_KO in ctx["affiliate_disclosure"]
    assert ctx["coupang_desktop_href"] == COUPANG_CATEGORIES["home_interior"]["desktop_href"]


def test_japanese_topik_amazon_only():
    ctx = affiliate_context("topik", lang="ja")
    assert ctx["show_amazon"] is True
    assert ctx["show_coupang"] is False
    assert ctx["show_klook"] is False
    assert "TOPIK" in ctx["amazon_keyword"]


def test_arrival_shows_klook():
    ctx = affiliate_context("arrival", lang="en")
    assert ctx["show_klook"] is True
    assert "klook.tpo.mx" in ctx["klook_url"]
    ctx_ja = affiliate_context("arrival", lang="ja")
    assert ctx_ja["show_klook"] is True
    assert "klook.tpo.mx" in ctx_ja["klook_url"]


def test_unmapped_visa_hides():
    assert affiliate_context("visa", lang="ja")["show_affiliate"] is False
    assert affiliate_context("visa", lang="en")["show_affiliate"] is False


def test_maps_use_known_coupang_categories():
    for slug, cat in GUIDE_COUPANG_MAP.items():
        assert cat in COUPANG_CATEGORIES, slug
        assert slug in GUIDE_AMAZON_MAP, slug


def test_klook_slugs_are_mapped():
    for slug in GUIDE_KLOOK_SLUGS:
        assert slug in GUIDE_COUPANG_MAP or slug in GUIDE_AMAZON_MAP


def test_school_shows_amazon_and_klook():
    ctx = affiliate_context("school_foo", lang="en", item_type="school")
    assert ctx["show_affiliate"] is True
    assert ctx["show_amazon"] is True
    assert ctx["show_klook"] is True
    assert ctx["show_coupang"] is False
    assert "TOPIK" in ctx["amazon_keyword"]
    assert "ED7IfKaq" in ctx["klook_url"]


def test_university_shows_amazon_and_klook_ja():
    ctx = affiliate_context("univ_bar", lang="ja", item_type="university")
    assert ctx["show_affiliate"] is True
    assert ctx["show_amazon"] is True
    assert ctx["show_klook"] is True
    assert "Amazon" in ctx["affiliate_title"]
    assert "Klook" in ctx["affiliate_title"]
    assert "ED7IfKaq" in ctx["klook_url"]
