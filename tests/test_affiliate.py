"""KR Campus affiliate: Rakuten Travel/eSIM + A8 (Klook removed)."""

from app.affiliate import (
    GUIDE_PREP_SLUGS,
    affiliate_context,
    rakuten_esim_url,
    rakuten_travel_url,
)
from app.a8_affiliate import a8_banners_context


def test_rakuten_short_links():
    assert rakuten_travel_url() == "https://a.r10.to/hPhGZl"
    assert "hPhGZl" in rakuten_travel_url()
    assert rakuten_esim_url() == "https://a.r10.to/h9O1Fq"
    assert "h9O1Fq" in rakuten_esim_url()


def test_english_shows_rakuten_for_lifestyle():
    ctx = affiliate_context("dorm-application", lang="en")
    assert ctx["show_affiliate"] is True
    assert ctx["show_rakuten_travel"] is True
    assert ctx["show_rakuten_esim"] is False
    assert "hPhGZl" in ctx["rakuten_travel_url"]
    assert "coupang" not in ctx["affiliate_desc"].lower()
    assert "amazon" not in ctx["affiliate_desc"].lower()


def test_arrival_shows_kkday_a8_not_klook():
    ctx = affiliate_context("arrival", lang="en")
    assert ctx["show_affiliate"] is True
    assert ctx["show_rakuten_travel"] is True
    a8 = a8_banners_context(slug="arrival", lang="en", item_type="guide")
    assert a8["show_a8_banners"] is True
    assert a8["a8_banners"][0]["id"] == "kkday"


def test_mobile_shows_rakuten_esim():
    ctx = affiliate_context("mobile", lang="en")
    assert ctx["show_affiliate"] is True
    assert ctx["show_rakuten_esim"] is True
    assert ctx["show_rakuten_travel"] is True


def test_topik_shows_korean_college_a8():
    a8 = a8_banners_context(slug="topik", lang="en", item_type="guide")
    assert a8["show_a8_banners"] is True
    assert a8["a8_banners"][0]["id"] == "korean_college"


def test_prep_slugs_still_show_box():
    for slug in ("arrival", "packing-korea", "sim-esim-korea"):
        assert slug in GUIDE_PREP_SLUGS
        ctx = affiliate_context(slug, lang="en")
        assert ctx["show_affiliate"] is True


def test_housing_agoda_a8():
    a8 = a8_banners_context(slug="housing", lang="en", item_type="guide")
    assert a8["show_a8_banners"] is True
    assert a8["a8_banners"][0]["id"] == "agoda"
