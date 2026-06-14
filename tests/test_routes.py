import unittest

from fastapi.testclient import TestClient

from app.main import app, DOMAIN
from app.utils import load_school_data, load_guides


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


if __name__ == "__main__":
    unittest.main()
