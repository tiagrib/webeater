"""
Tests for ``WebeaterFastBS``.

These tests must NOT hit the network. They run against the static
``tests/data/fixtures/sample_article.html`` fixture and exercise the public
``extract_content`` surface defined in
``metak-shared/api-contracts/content-extractor.md``.
"""

import asyncio
import os
import unittest

from webeater.config import HintsConfig, MainContentHints, RemoveHints
from webeater.thirdparty.beautifulsoup import WebeaterBeautifulSoup
from webeater.thirdparty.fastbs import WebeaterFastBS

FIXTURE_URL = "https://example.com/articles/sample"
FIXTURE_PATH = os.path.join(
    os.path.dirname(__file__), "data", "fixtures", "sample_article.html"
)


def _load_fixture() -> str:
    with open(FIXTURE_PATH, "r", encoding="utf-8") as fh:
        return fh.read()


def _make_extractor() -> WebeaterFastBS:
    """Build and load a fresh FastBS extractor."""
    extractor = WebeaterFastBS()
    asyncio.run(extractor.load())
    return extractor


def _make_legacy_extractor() -> WebeaterBeautifulSoup:
    """Build and load a fresh legacy BS extractor."""
    extractor = WebeaterBeautifulSoup()
    asyncio.run(extractor.load())
    return extractor


class TestWebeaterFastBS(unittest.TestCase):
    """Public-API tests for the FastBS extractor."""

    @classmethod
    def setUpClass(cls):
        cls.html = _load_fixture()

    # ---------- dict shape ----------

    def test_extract_returns_dict_shape(self):
        """``return_dict=True`` returns a dict with the contracted keys."""
        extractor = _make_extractor()
        result = asyncio.run(
            extractor.extract_content(
                FIXTURE_URL,
                self.html,
                include_images=True,
                include_links=True,
                hints=None,
                return_dict=True,
            )
        )
        self.assertIsInstance(result, dict)
        for key in ("title", "content", "images", "links"):
            self.assertIn(key, result)
        self.assertEqual(result["title"], "Sample Article For FastBS Tests")
        self.assertIsInstance(result["content"], str)
        self.assertIsInstance(result["images"], list)
        self.assertIsInstance(result["links"], list)
        self.assertTrue(len(result["content"]) > 0)

    # ---------- hint application ----------

    def test_hints_remove_strips_tags(self):
        """``remove.tags`` decomposes nodes before extraction."""
        extractor = _make_extractor()
        hints = HintsConfig(
            remove=RemoveHints(tags=["nav", "footer", "script"]),
        )
        result = asyncio.run(
            extractor.extract_content(
                FIXTURE_URL,
                self.html,
                include_images=True,
                include_links=True,
                hints=hints,
                return_dict=True,
            )
        )
        body = result["content"]
        # Sentinels that live ONLY inside removed tags must be gone.
        self.assertNotIn("NavJunkSentinelText", body)
        self.assertNotIn("FooterJunkSentinelText", body)
        self.assertNotIn("ScriptSentinelInsideArticleShouldBeStripped", body)
        # Nav links/footer links should also be gone from the link list.
        link_blob = "\n".join(result["links"])
        self.assertNotIn("NavHomeLink", link_blob)
        self.assertNotIn("FooterPrivacyLink", link_blob)

    def test_main_selector_picks_article(self):
        """``main.selectors=['article']`` picks the article and produces non-empty content."""
        extractor = _make_extractor()
        hints = HintsConfig(main=MainContentHints(selectors=["article"]))
        result = asyncio.run(
            extractor.extract_content(
                FIXTURE_URL,
                self.html,
                include_images=True,
                include_links=True,
                hints=hints,
                return_dict=True,
            )
        )
        body = result["content"]
        self.assertTrue(len(body) > 0)
        # Article content present.
        self.assertIn("ArticleProseMarkerOne", body)
        self.assertIn("ArticleProseMarkerTwo", body)
        # Sidebar lives OUTSIDE the article — must not leak in.
        self.assertNotIn("SidebarJunkSentinelText", body)
        # Site header h1 (outside <article>) must not leak in.
        self.assertNotIn("Site Header That Is Not The Article", body)

    # ---------- URL normalisation ----------

    def test_image_url_normalisation(self):
        """Relative img/href become absolute; mailto/javascript/# anchors are skipped."""
        extractor = _make_extractor()
        hints = HintsConfig(main=MainContentHints(selectors=["article"]))
        result = asyncio.run(
            extractor.extract_content(
                FIXTURE_URL,
                self.html,
                include_images=True,
                include_links=True,
                hints=hints,
                return_dict=True,
            )
        )

        # Absolute image preserved.
        self.assertIn(
            "![AbsoluteImage](https://cdn.example.com/absolute-image.png)",
            result["images"],
        )
        # Root-relative image normalised against scheme + host.
        self.assertIn(
            "![RelativeImage](https://example.com/static/relative-image.png)",
            result["images"],
        )

        link_blob = "\n".join(result["links"])
        # Absolute link preserved.
        self.assertIn("https://external.example.org/article", link_blob)
        # Root-relative link normalised.
        self.assertIn("https://example.com/internal/page", link_blob)
        # mailto: and javascript: and # anchors are excluded.
        self.assertNotIn("mailto:", link_blob)
        self.assertNotIn("javascript:", link_blob)
        self.assertNotIn("#section-anchor", link_blob)

    # ---------- empty / failure modes ----------

    def test_empty_html_no_content_found(self):
        """Empty HTML in string mode returns the ``No content found`` fallback."""
        extractor = _make_extractor()
        result = asyncio.run(
            extractor.extract_content(
                FIXTURE_URL,
                "",
                include_images=True,
                include_links=True,
                hints=None,
                return_dict=False,
            )
        )
        self.assertIsInstance(result, str)
        self.assertEqual(result, "No content found")

    def test_failure_mode_returns_error_string(self):
        """Internal exceptions yield ``Failed to extract content: ...``.

        We force the failure by stubbing ``_BSCLASS`` with something that
        raises on construction.
        """
        extractor = WebeaterFastBS()

        class _ExplodingBS:
            def __init__(self, *args, **kwargs):
                raise RuntimeError("forced failure for test")

        extractor._BSCLASS = _ExplodingBS

        result = asyncio.run(
            extractor.extract_content(
                FIXTURE_URL,
                "<p>anything</p>",
                include_images=True,
                include_links=True,
                hints=None,
                return_dict=False,
            )
        )
        self.assertIsInstance(result, str)
        self.assertTrue(
            result.startswith("Failed to extract content:"),
            f"Unexpected result: {result!r}",
        )

    # ---------- comparison with legacy ----------

    def test_compare_with_legacy_bs(self):
        """FastBS and legacy BS agree on title, image set, link set, and both produce content.

        This is the validation against the existing extractor — it ties the
        two implementations together at the contracted boundaries.
        """
        hints = HintsConfig(
            remove=RemoveHints(tags=["script"]),
            main=MainContentHints(selectors=["article"]),
        )

        fast = _make_extractor()
        legacy = _make_legacy_extractor()

        fast_result = asyncio.run(
            fast.extract_content(
                FIXTURE_URL,
                self.html,
                include_images=True,
                include_links=True,
                hints=hints,
                return_dict=True,
            )
        )
        legacy_result = asyncio.run(
            legacy.extract_content(
                FIXTURE_URL,
                self.html,
                include_images=True,
                include_links=True,
                hints=hints,
                return_dict=True,
            )
        )

        self.assertEqual(fast_result["title"], legacy_result["title"])
        self.assertEqual(set(fast_result["images"]), set(legacy_result["images"]))
        self.assertEqual(set(fast_result["links"]), set(legacy_result["links"]))
        self.assertTrue(len(fast_result["content"]) > 0)
        self.assertTrue(len(legacy_result["content"]) > 0)


if __name__ == "__main__":
    unittest.main()
