import unittest
import json
import os
import tempfile
import shutil
from unittest.mock import patch

from weat.config import HintsConfig, RemoveHints, MainContentHints


class TestHintsConfig(unittest.TestCase):
    """Test cases for HintsConfig class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.test_hints_dir = os.path.join(self.test_dir, "hints")
        os.makedirs(self.test_hints_dir, exist_ok=True)

        # Path to test data files
        self.test_data_dir = os.path.join(os.path.dirname(__file__), "data")

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def _create_hint_file(self, filename, data):
        """Helper to create hint files."""
        filepath = os.path.join(self.test_hints_dir, f"{filename}.json")
        with open(filepath, "w") as f:
            json.dump(data, f)
        return filepath

    def test_default_hints_config(self):
        """Test default HintsConfig creation."""
        hints = HintsConfig()
        self.assertIsNone(hints.remove)
        self.assertIsNone(hints.main)

    def test_hints_config_with_data(self):
        """Test HintsConfig with provided data."""
        remove_hints = RemoveHints(tags=["script"], classes=["ad"])
        main_hints = MainContentHints(selectors=["main"])

        hints = HintsConfig(remove=remove_hints, main=main_hints)
        self.assertEqual(hints.remove, remove_hints)
        self.assertEqual(hints.main, main_hints)

    def test_load_from_file_success(self):
        """Test successful loading from file."""
        hint_data = {
            "remove": {
                "tags": ["script", "style"],
                "classes": ["ad", "popup"],
                "ids": ["footer"],
            },
            "main": {"selectors": ["main", ".content"]},
        }

        filepath = self._create_hint_file("test", hint_data)

        with patch("weat.config.getLog"):
            hints = HintsConfig.load_from_file(filepath)

        self.assertIsNotNone(hints.remove)
        self.assertEqual(hints.remove.tags, ["script", "style"])
        self.assertEqual(hints.remove.classes, ["ad", "popup"])
        self.assertEqual(hints.remove.ids, ["footer"])

        self.assertIsNotNone(hints.main)
        self.assertEqual(hints.main.selectors, ["main", ".content"])

    def test_load_from_valid_test_data_file(self):
        """Test loading from valid test data file."""
        valid_hint_file = os.path.join(self.test_data_dir, "valid_hint.json")

        with patch("weat.config.getLog"):
            hints = HintsConfig.load_from_file(valid_hint_file)

        self.assertIsNotNone(hints.remove)
        self.assertEqual(hints.remove.tags, ["script", "style"])
        self.assertEqual(hints.remove.classes, ["ad", "popup"])
        self.assertEqual(hints.remove.ids, ["footer"])

        self.assertIsNotNone(hints.main)
        self.assertEqual(hints.main.selectors, ["main", ".content"])

    def test_load_from_file_legacy_main_format(self):
        """Test loading from file with legacy main format (list instead of object)."""
        hint_data = {
            "remove": {"tags": ["script"]},
            "main": ["main", ".content", "#article"],  # Legacy format
        }

        filepath = self._create_hint_file("legacy", hint_data)

        with patch("weat.config.getLog"):
            hints = HintsConfig.load_from_file(filepath)

        self.assertIsNotNone(hints.main)
        self.assertEqual(hints.main.selectors, ["main", ".content", "#article"])

    def test_load_from_file_not_found(self):
        """Test loading from non-existent file."""
        nonexistent_file = os.path.join(self.test_hints_dir, "nonexistent.json")

        with patch("weat.config.getLog") as mock_log:
            hints = HintsConfig.load_from_file(nonexistent_file)

        # Should return empty hints and log warning
        self.assertIsNone(hints.remove)
        self.assertIsNone(hints.main)
        mock_log.return_value.warning.assert_called_once()

    def test_load_from_file_invalid_json(self):
        """Test loading from file with invalid JSON."""
        # Use the invalid hint file from test data
        invalid_hint_file = os.path.join(self.test_data_dir, "invalid_hint.json")

        with patch("weat.config.getLog") as mock_log:
            hints = HintsConfig.load_from_file(invalid_hint_file)

        # Should return empty hints and log error
        self.assertIsNone(hints.remove)
        self.assertIsNone(hints.main)
        mock_log.return_value.error.assert_called_once()

    def test_load_from_file_invalid_json_temp_file(self):
        """Test loading from file with invalid JSON (temporary file)."""
        filepath = os.path.join(self.test_hints_dir, "invalid.json")
        with open(filepath, "w") as f:
            f.write("{ invalid json")

        with patch("weat.config.getLog") as mock_log:
            hints = HintsConfig.load_from_file(filepath)

        # Should return empty hints and log error
        self.assertIsNone(hints.remove)
        self.assertIsNone(hints.main)
        mock_log.return_value.error.assert_called_once()

    def test_load_combined_hints_empty(self):
        """Test combining hints with no input."""
        hints = HintsConfig.load_combined_hints([], hints_dir=self.test_hints_dir)
        self.assertIsNone(hints.remove)
        self.assertIsNone(hints.main)

    def test_load_combined_hints_single_file(self):
        """Test combining hints from single file."""
        hint_data = {
            "remove": {"tags": ["script"], "classes": ["ad"]},
            "main": {"selectors": ["main"]},
        }

        self._create_hint_file("single", hint_data)

        with patch("weat.config.getLog"):
            hints = HintsConfig.load_combined_hints(
                ["single"], hints_dir=self.test_hints_dir
            )

        self.assertIsNotNone(hints.remove)
        self.assertEqual(hints.remove.tags, ["script"])
        self.assertEqual(hints.remove.classes, ["ad"])

        self.assertIsNotNone(hints.main)
        self.assertEqual(hints.main.selectors, ["main"])

    def test_load_combined_hints_multiple_files(self):
        """Test combining hints from multiple files."""
        hint1_data = {
            "remove": {"tags": ["script"], "classes": ["ad"]},
            "main": {"selectors": ["main"]},
        }

        hint2_data = {
            "remove": {"tags": ["style"], "classes": ["popup"], "ids": ["footer"]},
            "main": {"selectors": [".content"]},
        }

        self._create_hint_file("hint1", hint1_data)
        self._create_hint_file("hint2", hint2_data)

        with patch("weat.config.getLog"):
            hints = HintsConfig.load_combined_hints(
                ["hint1", "hint2"], hints_dir=self.test_hints_dir
            )

        # Check combined remove hints
        self.assertIsNotNone(hints.remove)
        self.assertEqual(set(hints.remove.tags), {"script", "style"})
        self.assertEqual(set(hints.remove.classes), {"ad", "popup"})
        self.assertEqual(hints.remove.ids, ["footer"])

        # Check combined main hints
        self.assertIsNotNone(hints.main)
        self.assertEqual(set(hints.main.selectors), {"main", ".content"})

    def test_load_combined_hints_with_direct_hints(self):
        """Test combining hints with direct hints provided."""
        direct_hints = HintsConfig(
            remove=RemoveHints(tags=["direct_tag"]),
            main=MainContentHints(selectors=["direct_selector"]),
        )

        hint_data = {
            "remove": {"tags": ["file_tag"], "classes": ["file_class"]},
            "main": {"selectors": ["file_selector"]},
        }

        self._create_hint_file("file", hint_data)

        with patch("weat.config.getLog"):
            hints = HintsConfig.load_combined_hints(
                ["file"], direct_hints=direct_hints, hints_dir=self.test_hints_dir
            )

        # Check that both direct and file hints are combined
        self.assertIsNotNone(hints.remove)
        self.assertEqual(set(hints.remove.tags), {"direct_tag", "file_tag"})
        self.assertEqual(hints.remove.classes, ["file_class"])

        self.assertIsNotNone(hints.main)
        self.assertEqual(
            set(hints.main.selectors), {"direct_selector", "file_selector"}
        )

    def test_load_combined_hints_removes_duplicates(self):
        """Test that duplicate values are removed while preserving order."""
        hint1_data = {
            "remove": {"tags": ["script", "style"], "classes": ["ad"]},
            "main": {"selectors": ["main", ".content"]},
        }

        hint2_data = {
            "remove": {
                "tags": ["style", "nav"],  # 'style' is duplicate
                "classes": ["ad", "popup"],  # 'ad' is duplicate
            },
            "main": {
                "selectors": [".content", "article"]  # '.content' is duplicate
            },
        }

        self._create_hint_file("hint1", hint1_data)
        self._create_hint_file("hint2", hint2_data)

        with patch("weat.config.getLog"):
            hints = HintsConfig.load_combined_hints(
                ["hint1", "hint2"], hints_dir=self.test_hints_dir
            )

        # Check that duplicates are removed and order is preserved
        self.assertEqual(hints.remove.tags, ["script", "style", "nav"])
        self.assertEqual(hints.remove.classes, ["ad", "popup"])
        self.assertEqual(hints.main.selectors, ["main", ".content", "article"])

    def test_load_combined_hints_partial_data(self):
        """Test combining hints where some files have partial data."""
        # First file has only remove hints
        hint1_data = {"remove": {"tags": ["script"]}}

        # Second file has only main hints
        hint2_data = {"main": {"selectors": ["main"]}}

        self._create_hint_file("hint1", hint1_data)
        self._create_hint_file("hint2", hint2_data)

        with patch("weat.config.getLog"):
            hints = HintsConfig.load_combined_hints(
                ["hint1", "hint2"], hints_dir=self.test_hints_dir
            )

        self.assertIsNotNone(hints.remove)
        self.assertEqual(hints.remove.tags, ["script"])

        self.assertIsNotNone(hints.main)
        self.assertEqual(hints.main.selectors, ["main"])

    def test_load_combined_hints_nonexistent_files(self):
        """Test combining hints with some nonexistent files."""
        hint_data = {"remove": {"tags": ["script"]}}

        self._create_hint_file("exists", hint_data)

        with patch("weat.config.getLog"):
            hints = HintsConfig.load_combined_hints(
                ["exists", "nonexistent"], hints_dir=self.test_hints_dir
            )

        # Should still work with the existing file
        self.assertIsNotNone(hints.remove)
        self.assertEqual(hints.remove.tags, ["script"])

    def test_hints_config_repr(self):
        """Test string representation of HintsConfig."""
        # Test with empty hints
        hints = HintsConfig()
        repr_str = repr(hints)
        self.assertIn("HintsConfig", repr_str)
        self.assertIn("0 selectors", repr_str)

        # Test with main hints
        hints = HintsConfig(main=MainContentHints(selectors=["main", ".content"]))
        repr_str = repr(hints)
        self.assertIn("2 selectors", repr_str)

    def test_actual_hint_files_loading(self):
        """Test loading actual hint files from the project."""
        # This test uses the actual hints directory
        project_hints_dir = "hints"

        with patch("weat.config.getLog"):
            # Test loading default hints
            default_hints = HintsConfig.load_from_file(
                os.path.join(project_hints_dir, "default.json")
            )

        self.assertIsNotNone(default_hints.remove)
        self.assertIsNotNone(default_hints.main)
        self.assertIn("script", default_hints.remove.tags)
        self.assertIn("main", default_hints.main.selectors)

        with patch("weat.config.getLog"):
            # Test loading news hints
            news_hints = HintsConfig.load_from_file(
                os.path.join(project_hints_dir, "news.json")
            )

        self.assertIsNotNone(news_hints.remove)
        self.assertIsNotNone(news_hints.main)
        self.assertIn("sidebar", news_hints.remove.classes)
        self.assertIn("article", news_hints.main.selectors)

    def test_combined_actual_hints(self):
        """Test combining actual hint files from the project."""
        with patch("weat.config.getLog"):
            combined = HintsConfig.load_combined_hints(
                ["default", "news"], hints_dir="hints"
            )

        self.assertIsNotNone(combined.remove)
        self.assertIsNotNone(combined.main)

        # Should have tags from both files
        all_tags = set(combined.remove.tags)
        self.assertIn("script", all_tags)  # from default
        self.assertIn("iframe", all_tags)  # from news

        # Should have selectors from both files
        all_selectors = set(combined.main.selectors)
        self.assertIn("main", all_selectors)  # from default
        self.assertIn("article", all_selectors)  # from both, no duplicate


if __name__ == "__main__":
    unittest.main()
