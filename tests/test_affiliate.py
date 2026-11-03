"""KR Campus affiliate: Rakuten Travel/eSIM + Agoda + Amazon (KKday/Korean College removed)."""

from app.affiliate import (
    GUIDE_PREP_SLUGS,
    affiliate_context,
    rakuten_esim_url,
    rakuten_travel_url,
)
from app.a8_affiliate import a8_banners_context
from app.amazon_affiliate import amazon_context, kind_for


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


def test_arrival_shows_agoda_only_a8():
    ctx = affiliate_context("arrival", lang="en")
    assert ctx["show_affiliate"] is True
    assert ctx["show_rakuten_travel"] is True
    a8 = a8_banners_context(slug="arrival", lang="en", item_type="guide")
    assert a8["show_a8_banners"] is True
    assert [b["id"] for b in a8["a8_banners"]] == ["agoda"]
    assert "agoda.com/partners" in a8["a8_banners"][0]["click_url"]
    assert a8["show_agoda_cta"] is True


def test_mobile_shows_rakuten_esim():
    ctx = affiliate_context("mobile", lang="en")
    assert ctx["show_affiliate"] is True
    assert ctx["show_rakuten_esim"] is True
    assert ctx["show_rakuten_travel"] is True


def test_topik_shows_agoda_only_a8():
    a8 = a8_banners_context(slug="topik", lang="en", item_type="guide")
    assert a8["show_a8_banners"] is True
    assert [b["id"] for b in a8["a8_banners"]] == ["agoda"]
    assert "agoda.com/partners" in a8["a8_banners"][0]["click_url"]


def test_prep_slugs_still_show_box():
    for slug in ("arrival", "packing-korea", "sim-esim-korea"):
        assert slug in GUIDE_PREP_SLUGS
        ctx = affiliate_context(slug, lang="en")
        assert ctx["show_affiliate"] is True


def test_housing_agoda_a8():
    a8 = a8_banners_context(slug="housing", lang="en", item_type="guide")
    assert a8["show_a8_banners"] is True
    assert a8["a8_banners"][0]["id"] == "agoda"


def test_school_shows_agoda_only_a8():
    a8 = a8_banners_context(slug="some-school", lang="en", item_type="school")
    assert [b["id"] for b in a8["a8_banners"]] == ["agoda"]
    assert a8["show_agoda_cta"] is True


def test_no_a8_net_banners():
    for slug, kind in (("arrival", "guide"), ("topik", "guide"), ("x", "school")):
        a8 = a8_banners_context(slug=slug, lang="ja", item_type=kind)
        for b in a8["a8_banners"]:
            assert "a8.net" not in b["click_url"]
            assert not b["pixel_url"]


def test_amazon_kinds():
    expect = {
        "housing": "一人暮らし 寝具",
        "language": "韓国語 参考書",
        "topik": "韓国語 参考書",
        "arrival": "海外旅行 便利グッズ",
        "packing": "海外旅行 便利グッズ",
        "school": "留学 準備",
        "default": "韓国 留学 グッズ",
        "unknown": "韓国 留学 グッズ",
    }
    for kind, kw in expect.items():
        ctx = amazon_context(kind=kind, lang="ja")
        assert ctx["show_amazon"] is True
        assert ctx["amazon_cta"]["keyword"] == kw
        assert "tag=starful06-22" in ctx["amazon_cta"]["click_url"]
        assert "amazon.co.jp/s?k=" in ctx["amazon_cta"]["click_url"]


def test_amazon_kind_for_pages():
    assert kind_for("arrival", "guide") == "arrival"
    assert kind_for("packing-korea", "guide") == "packing"
    assert kind_for("topik_ja", "guide") == "topik"
    assert kind_for("housing", "guide") == "housing"
    assert kind_for("anything", "school") == "school"
    assert kind_for("monthly-budget-seoul", "guide") == "default"
