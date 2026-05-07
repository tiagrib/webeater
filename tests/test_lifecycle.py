"""
Lifecycle tests for the renderer and extractor abstract base classes.

These tests cover the bug-fix work in T1: ensuring that
``SeleniumRuntime.shutdown()`` is safe to call before ``load()`` and
idempotent across repeat calls, and that the ``ContentExtractor`` ABC
exposes the wide ``extract_content`` signature documented in
``metak-shared/api-contracts/content-extractor.md``.

These tests must NOT start Chrome. They only construct the runtime
class and exercise its lifecycle hooks.
"""

import asyncio
import inspect
import unittest

from webeater.config import HintsConfig
from webeater.extracting import ContentExtractor
from webeater.thirdparty.selenium import SeleniumRuntime


class TestSeleniumRuntimeShutdownLifecycle(unittest.TestCase):
    """Verify SeleniumRuntime.shutdown() is safe before load() and idempotent."""

    def test_shutdown_without_load_does_not_raise(self):
        """Calling shutdown() on a fresh runtime must not raise."""
        runtime = SeleniumRuntime()
        # Sanity-check the precondition: load() never ran, so Driver is None.
        self.assertIsNone(runtime.Driver)

        # The bug being guarded against: this used to call self.Driver.quit()
        # unconditionally and raise AttributeError.
        asyncio.run(runtime.shutdown())

        self.assertIsNone(runtime.Driver)

    def test_shutdown_is_idempotent(self):
        """Calling shutdown() twice must not raise."""
        runtime = SeleniumRuntime()
        asyncio.run(runtime.shutdown())
        # Second call: still must not raise.
        asyncio.run(runtime.shutdown())
        self.assertIsNone(runtime.Driver)

    def test_shutdown_clears_driver_after_quit(self):
        """After a successful shutdown(), Driver is reset to None."""

        class _FakeDriver:
            def __init__(self):
                self.quit_called = 0

            def quit(self):
                self.quit_called += 1

        runtime = SeleniumRuntime()
        fake = _FakeDriver()
        runtime.Driver = fake

        asyncio.run(runtime.shutdown())

        self.assertEqual(fake.quit_called, 1)
        self.assertIsNone(runtime.Driver)

        # And a follow-up shutdown is still a no-op (does not call quit again).
        asyncio.run(runtime.shutdown())
        self.assertEqual(fake.quit_called, 1)


class TestContentExtractorAbcSignature(unittest.TestCase):
    """Verify the ContentExtractor ABC matches the contract."""

    def test_load_has_self_parameter(self):
        """ContentExtractor.load must accept self."""
        sig = inspect.signature(ContentExtractor.load)
        self.assertIn("self", sig.parameters)

    def test_extract_content_has_wide_signature(self):
        """ContentExtractor.extract_content must accept the full keyword set."""
        sig = inspect.signature(ContentExtractor.extract_content)
        params = sig.parameters
        for expected in (
            "self",
            "url",
            "html",
            "include_images",
            "include_links",
            "hints",
            "return_dict",
        ):
            self.assertIn(
                expected,
                params,
                f"ContentExtractor.extract_content missing parameter: {expected}",
            )

        # Defaults from the contract.
        self.assertEqual(params["include_images"].default, True)
        self.assertEqual(params["include_links"].default, True)
        self.assertIsNone(params["hints"].default)
        self.assertEqual(params["return_dict"].default, True)

    def test_subclass_can_override_with_wide_signature(self):
        """A concrete subclass may implement the wide extract_content."""

        class _Stub(ContentExtractor):
            async def load(self):
                pass

            async def shutdown(self):
                pass

            async def extract_content(
                self,
                url: str,
                html: str,
                include_images: bool = True,
                include_links: bool = True,
                hints=None,
                return_dict: bool = True,
            ):
                return {
                    "title": "",
                    "content": html,
                    "url": url,
                    "include_images": include_images,
                    "include_links": include_links,
                    "hints": hints,
                    "return_dict": return_dict,
                }

        stub = _Stub()
        result = asyncio.run(
            stub.extract_content(
                "https://example.com",
                "<p>hi</p>",
                hints=HintsConfig(),
                return_dict=True,
            )
        )
        self.assertEqual(result["url"], "https://example.com")
        self.assertEqual(result["content"], "<p>hi</p>")
        self.assertTrue(result["include_images"])
        self.assertTrue(result["include_links"])
        self.assertTrue(result["return_dict"])
        self.assertIsInstance(result["hints"], HintsConfig)

    def test_base_extract_content_raises_not_implemented(self):
        """The ABC's extract_content must raise NotImplementedError when invoked directly."""

        class _Bare(ContentExtractor):
            async def load(self):
                pass

            async def shutdown(self):
                pass

            # Intentionally does NOT override extract_content.

        bare = _Bare()
        with self.assertRaises(NotImplementedError):
            asyncio.run(
                bare.extract_content(
                    "https://example.com",
                    "<p>hi</p>",
                )
            )


if __name__ == "__main__":
    unittest.main()
