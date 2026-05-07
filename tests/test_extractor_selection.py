"""Tests for selecting the content extractor via ``WeatConfig.extractor``.

Covers:

- Default extractor is ``WebeaterFastBS``.
- ``extractor="bs"`` selects ``WebeaterBeautifulSoup``.
- ``extractor="fastbs"`` selects ``WebeaterFastBS``.
- Invalid values raise ``pydantic.ValidationError``.
- The default ``extractor`` value is omitted from the persisted ``weat.json``;
  a non-default value (``"bs"``) is persisted.

These tests construct ``Webeater`` directly via ``Webeater(config=...)`` instead
of awaiting ``Webeater.create()`` because the latter boots Selenium / headless
Chrome via ``_async_init``. Per ``metak-shared/architecture.md`` only
``_async_init`` boots the renderer; ``__init__`` is safe.
"""

import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

import pydantic

from webeater.config import WeatConfig
from webeater.eater import Webeater
from webeater.thirdparty.beautifulsoup import WebeaterBeautifulSoup
from webeater.thirdparty.fastbs import WebeaterFastBS


class TestExtractorSelection(unittest.TestCase):
    """Verify ``WeatConfig.extractor`` correctly drives ``Webeater``'s extractor."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_config_file = os.path.join(self.test_dir, "weat.json")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _make_config(self, **kwargs):
        """Build a ``WeatConfig`` rooted in the temp dir, with no preexisting file."""
        with patch("webeater.config.getLog"):
            return WeatConfig(filename=self.test_config_file, **kwargs)

    def test_default_extractor_is_fastbs(self):
        """A default ``WeatConfig`` selects the FastBS extractor."""
        config = self._make_config()
        self.assertEqual(config.extractor, "fastbs")

        with patch("webeater.eater.getLog"):
            engine = Webeater(config=config)

        self.assertIsInstance(engine.context_extractor, WebeaterFastBS)

    def test_extractor_bs_explicit(self):
        """``extractor='bs'`` selects the legacy ``WebeaterBeautifulSoup``."""
        config = self._make_config(extractor="bs")
        self.assertEqual(config.extractor, "bs")

        with patch("webeater.eater.getLog"):
            engine = Webeater(config=config)

        self.assertIsInstance(engine.context_extractor, WebeaterBeautifulSoup)

    def test_extractor_fastbs_explicit(self):
        """``extractor='fastbs'`` selects ``WebeaterFastBS``."""
        config = self._make_config(extractor="fastbs")
        self.assertEqual(config.extractor, "fastbs")

        with patch("webeater.eater.getLog"):
            engine = Webeater(config=config)

        self.assertIsInstance(engine.context_extractor, WebeaterFastBS)

    def test_extractor_invalid_raises(self):
        """Any value other than ``'bs'`` or ``'fastbs'`` is rejected."""
        with patch("webeater.config.getLog"):
            try:
                WeatConfig(filename=self.test_config_file, extractor="garbage")
            except pydantic.ValidationError:
                return
            except ValueError:
                # ``WeatConfig.__init__`` wraps pydantic.ValidationError in a
                # ValueError when the bad value comes from the on-disk file.
                # When passed via kwargs, pydantic raises directly; assert that.
                self.fail(
                    "Expected pydantic.ValidationError, got ValueError "
                    "(invalid value passed via kwargs should raise pydantic directly)"
                )
            self.fail("Expected pydantic.ValidationError for extractor='garbage'")

    def test_default_save_omits_extractor_field(self):
        """A default ``WeatConfig`` must not persist ``extractor`` to ``weat.json``.

        A non-default value (``'bs'``) must be persisted so users can opt in.
        """
        # Default config (extractor defaults to "fastbs") -> no extractor in file.
        self._make_config()
        with open(self.test_config_file, "r") as f:
            saved = json.load(f)
        self.assertNotIn(
            "extractor",
            saved,
            "Default extractor='fastbs' must be omitted from saved weat.json",
        )

        # Explicit non-default value -> persisted.
        # Use a fresh path so the previous default-save does not leak in.
        non_default_path = os.path.join(self.test_dir, "weat_bs.json")
        with patch("webeater.config.getLog"):
            WeatConfig(filename=non_default_path, extractor="bs")
        with open(non_default_path, "r") as f:
            saved_bs = json.load(f)
        self.assertEqual(saved_bs.get("extractor"), "bs")


if __name__ == "__main__":
    unittest.main()
