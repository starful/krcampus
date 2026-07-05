import unittest

from fastapi.testclient import TestClient

from app.main import app
from app.settings import DOMAIN
from app.content_loader import load_school_data, load_guides


class RouteSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_core_routes_return_200(self):
        for path in ["/", "/schools", "/universities", "/guide", "/about", "/policy", "/contact", "/compare"]:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)

    def test_core_routes_have_canonical(self):
        target = self.client.get("/schools")
        self.assertIn(f'<link rel="canonical" href="{DOMAIN}/schools">', target.text)

    def test_sitemap_contains_lastmod_and_hreflang(self):
        response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code, 200)
        self.assertIn("<lastmod>", response.text)
        self.assertIn('hreflang="en"', response.text)
        self.assertIn('hreflang="ja"', response.text)

    def test_legacy_redirect_map(self):
        response = self.client.get("/privacy", follow_redirects=False)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.headers.get("location"), "/policy")

    def test_lang_kr_alias_redirects_to_ja(self):
        response = self.client.get("/guide?lang=kr", follow_redirects=False)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.headers.get("location"), "/guide?lang=ja")

    def test_reactions_api_returns_counts(self):
        response = self.client.get("/api/reactions/smoke-test-slug")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("likes", payload)
        self.assertIn("dislikes", payload)

    def test_sample_detail_pages_render(self):
        schools, _ = load_school_data("en")
        school_id = next((s.get("id") for s in schools if s.get("id")), None)
        self.assertIsNotNone(school_id)
        school_response = self.client.get(f"/school/{school_id}")
        self.assertEqual(school_response.status_code, 200)

        guides = load_guides("en")
        guide_slug = next((g["link"].split("/")[-1].split("?")[0] for g in guides if g.get("link")), None)
        self.assertIsNotNone(guide_slug)
        guide_response = self.client.get(f"/guide/{guide_slug}")
        self.assertEqual(guide_response.status_code, 200)
        self.assertIn("reaction-panel", guide_response.text)
        self.assertIn("count-like", school_response.text)

        guide_ja = self.client.get("/guide/best-national-universities-korea?lang=ja")
        self.assertEqual(guide_ja.status_code, 200, guide_ja.text[:200])

    def test_guide_slug_redirects_from_legacy_japan_urls(self):
        for old_path, new_path in [
            ("/guide/best-national-universities-japan", "/guide/best-national-universities-korea"),
            ("/guide/top-womens-education-japan", "/guide/top-womens-universities-korea"),
            ("/guide/women-universities-korea", "/guide/top-womens-universities-korea"),
        ]:
            with self.subTest(old_path=old_path):
                response = self.client.get(old_path, follow_redirects=False)
                self.assertEqual(response.status_code, 301)
                self.assertEqual(response.headers.get("location"), new_path)

    def test_static_pages_use_site_header(self):
        response = self.client.get("/about")
        self.assertEqual(response.status_code, 200)
        self.assertIn("site-header", response.text)
        self.assertIn("main-footer", response.text)
        self.assertNotIn("© 2024 KR Campus", response.text)


if __name__ == "__main__":
    unittest.main()
