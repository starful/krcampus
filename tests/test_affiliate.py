"""KR Campus affiliate: Amazon.jp + Rakuten Travel/eSIM + Klook airport."""

from app.affiliate import (
    AMAZON_TAG,
    GUIDE_AMAZON_MAP,
    GUIDE_KLOOK_SLUGS,
    RAKUTEN_KOREA_ESIM_URL,
    RAKUTEN_KOREA_TRAVEL_URL,
    affiliate_context,
    amazon_search_url,
    normalize_guide_slug,
    rakuten_esim_url,
    rakuten_travel_url,
)


def test_normalize_strips_prefixes():
    assert normalize_guide_slug("guide_packing-korea") == "packing-korea"
    assert normalize_guide_slug("packing-korea_ja") == "packing-korea"


def test_amazon_url_uses_co_jp_and_tag():
    url = amazon_search_url("TOPIK 問題集")
    assert "amazon.co.jp/s?k=" in url
    assert AMAZON_TAG in url


def test_rakuten_short_links():
    assert rakuten_travel_url() == RAKUTEN_KOREA_TRAVEL_URL
    assert "hPhGZl" in rakuten_travel_url()
    assert rakuten_esim_url() == RAKUTEN_KOREA_ESIM_URL
    assert "h9O1Fq" in rakuten_esim_url()


def test_english_shows_amazon_and_rakuten_for_lifestyle():
    ctx = affiliate_context("dorm-application", lang="en")
    assert ctx["show_affiliate"] is True
    assert ctx["show_amazon"] is True
    assert ctx["show_klook"] is False
    assert ctx["show_rakuten_travel"] is True
    assert ctx["show_rakuten_esim"] is False
    assert "hPhGZl" in ctx["rakuten_travel_url"]
    assert "coupang" not in ctx["affiliate_desc"].lower()


def test_arrival_shows_klook_airport_not_esim_klook():
    ctx = affiliate_context("arrival", lang="en")
    assert ctx["show_klook"] is True
    assert "BSwK5MnY" in ctx["klook_url"]
    assert ctx["show_rakuten_travel"] is True
    assert ctx["show_rakuten_esim"] is False


def test_esim_guide_uses_rakuten_esim():
    ctx = affiliate_context("sim-esim-korea", lang="en")
    assert ctx["show_rakuten_esim"] is True
    assert "h9O1Fq" in ctx["rakuten_esim_url"]
    assert ctx["show_klook"] is False
    ctx_ja = affiliate_context("mobile", lang="ja")
    assert ctx_ja["show_rakuten_esim"] is True
    assert "h9O1Fq" in ctx_ja["rakuten_esim_url"]


def test_unmapped_visa_hides():
    assert affiliate_context("visa", lang="ja")["show_affiliate"] is False
    assert affiliate_context("visa", lang="en")["show_affiliate"] is False


def test_amazon_map_keys_are_nonempty():
    assert GUIDE_AMAZON_MAP
    for slug, kw in GUIDE_AMAZON_MAP.items():
        assert slug and kw


def test_klook_slugs_still_show_box():
    for slug in GUIDE_KLOOK_SLUGS:
        ctx = affiliate_context(slug, lang="en")
        assert ctx["show_affiliate"] is True


def test_school_shows_amazon_travel_and_esim():
    ctx = affiliate_context("school_foo", lang="en", item_type="school")
    assert ctx["show_affiliate"] is True
    assert ctx["show_amazon"] is True
    assert ctx["show_rakuten_travel"] is True
    assert ctx["show_rakuten_esim"] is True
    assert ctx["show_klook"] is False
    assert "TOPIK" in ctx["amazon_keyword"]
    assert "hPhGZl" in ctx["rakuten_travel_url"]
    assert "h9O1Fq" in ctx["rakuten_esim_url"]


def test_university_ja():
    ctx = affiliate_context("univ_bar", lang="ja", item_type="university")
    assert ctx["show_affiliate"] is True
    assert ctx["show_amazon"] is True
    assert ctx["show_rakuten_esim"] is True
    assert ctx["show_klook"] is False
    assert "Amazon" in ctx["affiliate_title"]


def test_context_has_no_coupang_keys():
    ctx = affiliate_context("dorm-application", lang="en")
    assert "show_coupang" not in ctx
