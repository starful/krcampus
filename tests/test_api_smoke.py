import unittest

from fastapi.testclient import TestClient

from app.main import app


class ApiSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_reactions_api_returns_json(self):
        response = self.client.get("/api/reactions/smoke-test-slug")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("likes", payload)
        self.assertIn("dislikes", payload)

    def test_robots_and_sitemap_exist(self):
        robots = self.client.get("/robots.txt")
        self.assertEqual(robots.status_code, 200)
        self.assertIn("Sitemap:", robots.text)

        sitemap = self.client.get("/sitemap.xml")
        self.assertEqual(sitemap.status_code, 200)
        self.assertIn("<urlset", sitemap.text)
        self.assertIn("xhtml:link", sitemap.text)

    def test_favicon_and_manifest_routes_exist(self):
        for path in [
            "/favicon.ico",
            "/favicon-32x32.png",
            "/favicon-48x48.png",
            "/apple-touch-icon.png",
            "/site.webmanifest",
        ]:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
