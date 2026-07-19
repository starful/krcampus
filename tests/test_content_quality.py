"""Tests for KR Campus content_quality / content_specs gates."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from content_quality import is_deleted_guide, template_heading_issues  # noqa: E402
from content_specs import validate_body  # noqa: E402


def _mid_pad() -> str:
    # Keep total body inside university 5500–7500 band across 5–7 sections.
    return ("Korea campus detail for international students. ") * 18


class ContentQualityTests(unittest.TestCase):
    def test_rejects_numbered_univ_template(self):
        pad = _mid_pad()
        table = "| A | B |\n| --- | --- |\n| 1 | 2 |\n\n| C | D |\n| --- | --- |\n| 3 | 4 |\n"
        body = (
            f"## 1. University Overview\n{pad}\n"
            f"## 2. English-Taught & International Programs\n{pad}\n"
            f"## 3. Faculties & Academic Strengths\n{pad}\n"
            f"## 4. Tuition, Fees & Scholarships\n{table}\n{pad}\n"
            f"## 5. Admissions for International Students\n{pad}\n"
        )
        issues = template_heading_issues(body, threshold=3)
        self.assertTrue(issues)
        # Length may also fail; force template check via helper
        self.assertTrue(any("template headings" in i for i in issues))

    def test_accepts_unique_headings(self):
        pad = _mid_pad()
        table = (
            "| Fee | KRW |\n| --- | --- |\n| Tuition | 4,000,000 |\n\n"
            "| Item | Note |\n| --- | --- |\n| Dorm | Optional |\n"
        )
        body = (
            f"## Why students choose this Seoul campus\n{pad}\n"
            f"## English pathways that actually exist\n{pad}\n"
            f"## Faculties with international intake\n{pad}\n"
            f"## Tuition snapshot and scholarships\n{table}\n{pad}\n"
            f"## Admissions timeline for foreigners\n{pad}\n"
            f"## Living near campus\n{pad}\n"
            f"## FAQ for applicants\n### Q1?\nA1\n### Q2?\nA2\n### Q3?\nA3\n### Q4?\nA4\n### Q5?\nA5\n"
        )
        # Trim if over max
        while len(body) > 7500:
            pad = pad[: max(100, len(pad) - 80)]
            body = (
                f"## Why students choose this Seoul campus\n{pad}\n"
                f"## English pathways that actually exist\n{pad}\n"
                f"## Faculties with international intake\n{pad}\n"
                f"## Tuition snapshot and scholarships\n{table}\n{pad}\n"
                f"## Admissions timeline for foreigners\n{pad}\n"
                f"## Living near campus\n{pad}\n"
                f"## FAQ for applicants\n### Q1?\nA1\n### Q2?\nA2\n### Q3?\nA3\n### Q4?\nA4\n### Q5?\nA5\n"
            )
        while len(body) < 5500:
            pad = pad + " Extra practical note."
            body = (
                f"## Why students choose this Seoul campus\n{pad}\n"
                f"## English pathways that actually exist\n{pad}\n"
                f"## Faculties with international intake\n{pad}\n"
                f"## Tuition snapshot and scholarships\n{table}\n{pad}\n"
                f"## Admissions timeline for foreigners\n{pad}\n"
                f"## Living near campus\n{pad}\n"
                f"## FAQ for applicants\n### Q1?\nA1\n### Q2?\nA2\n### Q3?\nA3\n### Q4?\nA4\n### Q5?\nA5\n"
            )
        ok, reason = validate_body("university", body)
        self.assertTrue(ok, reason)

    def test_empty_diet_plan_lookups(self):
        self.assertFalse(is_deleted_guide("housing"))


if __name__ == "__main__":
    unittest.main()
