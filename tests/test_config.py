import unittest
import json
import os
import tempfile
import shutil
from unittest.mock import patch
from pydantic import ValidationError

from weat.config import WeatConfig, HintsConfig, RemoveHints, MainContentHints


class TestWeatConfig(unittest.TestCase):
    """Test cases for WeatConfig class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.test_config_file = os.path.join(self.test_dir, "test_weat.json")
        self.test_hints_dir = os.path.join(self.test_dir, "hints")
        os.makedirs(self.test_hints_dir, exist_ok=True)

        # Path to test data files
        self.test_data_dir = os.path.join(os.path.dirname(__file__), "data")

        # Create test hint file
        test_hint_data = {
            "remove": {
                "tags": ["script", "style"],
                "classes": ["ad", "popup"],
                "ids": ["footer"],
            },
            "main": {"selectors": ["main", ".content"]},
        }
        with open(os.path.join(self.test_hints_dir, "test.json"), "w") as f:
            json.dump(test_hint_data, f)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def test_default_config_creation(self):
        """Test creating config with default values when file doesn't exist."""
        # Use a path that definitely doesn't exist
        nonexistent_file = os.path.join(
            self.test_dir, "definitely_nonexistent_file.json"
        )

        with patch("weat.config.getLog"):
            config = WeatConfig.__new__(WeatConfig)
            config.__init__(filename=nonexistent_file)

        self.assertEqual(config.window_size_w, 1280)
        self.assertEqual(config.window_size_h, 800)
        self.assertEqual(config.hint_files, ["default"])
        self.assertIsNone(config.hints)
        self.assertFalse(config.debug)

    def test_config_from_file(self):
        """Test loading config from existing file."""
        config_data = {
            "window_size_w": 1920,
            "window_size_h": 1080,
            "hint_files": ["default", "news"],
            "debug": True,
        }

        with open(self.test_config_file, "w") as f:
            json.dump(config_data, f)

        with patch("weat.config.getLog"):
            with patch.object(WeatConfig, "_load_combined_hints"):
                with patch.object(WeatConfig, "save"):
                    config = WeatConfig(filename=self.test_config_file)

        self.assertEqual(config.window_size_w, 1920)
        self.assertEqual(config.window_size_h, 1080)
        self.assertEqual(config.hint_files, ["default", "news"])
        self.assertTrue(config.debug)

    def test_config_from_valid_sample_file(self):
        """Test loading config from a valid sample data file."""
        valid_sample_file = os.path.join(self.test_data_dir, "valid_sample.json")

        with patch("weat.config.getLog"):
            with patch.object(WeatConfig, "_load_combined_hints"):
                with patch.object(WeatConfig, "save"):
                    config = WeatConfig(filename=valid_sample_file)

        self.assertEqual(config.window_size_w, 1920)
        self.assertEqual(config.window_size_h, 1080)
        self.assertEqual(config.hint_files, ["default", "news"])
        self.assertTrue(config.debug)

    def test_config_validation_positive_dimensions(self):
        """Test validation of positive window dimensions."""
        # Test with zero width using test data file
        zero_width_file = os.path.join(self.test_data_dir, "invalid_zero_width.json")
        with patch("weat.config.getLog"):
            with self.assertRaises((ValueError, RuntimeError)):
                WeatConfig(filename=zero_width_file)

        # Test with negative height using test data file
        negative_height_file = os.path.join(
            self.test_data_dir, "invalid_negative_height.json"
        )
        with patch("weat.config.getLog"):
            with self.assertRaises((ValueError, RuntimeError)):
                WeatConfig(filename=negative_height_file)

    def test_config_with_extra_hint_files(self):
        """Test adding extra hint files."""
        config_data = {"hint_files": ["default"]}

        with open(self.test_config_file, "w") as f:
            json.dump(config_data, f)

        with patch("weat.config.getLog"):
            with patch.object(WeatConfig, "_load_combined_hints"):
                with patch.object(WeatConfig, "save"):
                    config = WeatConfig(
                        filename=self.test_config_file,
                        extra_hint_files=["news", "sports"],
                    )

        self.assertEqual(config.hint_files, ["default", "news", "sports"])

    def test_config_duplicate_hint_files_removal(self):
        """Test that duplicate hint files are removed while preserving order."""
        config_data = {"hint_files": ["default", "news"]}

        with open(self.test_config_file, "w") as f:
            json.dump(config_data, f)

        with patch("weat.config.getLog"):
            with patch.object(WeatConfig, "_load_combined_hints"):
                with patch.object(WeatConfig, "save"):
                    config = WeatConfig(
                        filename=self.test_config_file,
                        extra_hint_files=["news", "sports", "default"],
                    )

        self.assertEqual(config.hint_files, ["default", "news", "sports"])

    def test_config_save(self):
        """Test saving config to file."""
        # Create a temporary config file with test data
        config_data = {
            "window_size_w": 1600,
            "window_size_h": 900,
            "hint_files": ["custom"],
            "debug": True,
        }

        with open(self.test_config_file, "w") as f:
            json.dump(config_data, f)

        with patch("weat.config.getLog"):
            with patch.object(WeatConfig, "_load_combined_hints"):
                config = WeatConfig(filename=self.test_config_file)

        # Check file was created and contains correct data
        self.assertTrue(os.path.exists(self.test_config_file))

        with open(self.test_config_file, "r") as f:
            saved_data = json.load(f)

        self.assertEqual(saved_data["window_size_w"], 1600)
        self.assertEqual(saved_data["window_size_h"], 900)
        self.assertEqual(saved_data["hint_files"], ["custom"])
        self.assertTrue(saved_data["debug"])

    def test_config_save_excludes_debug_false(self):
        """Test that debug=False is excluded from saved config."""
        # Create config data without debug flag
        config_data = {
            "window_size_w": 1280,
            "window_size_h": 800,
            "hint_files": ["default"],
        }

        with open(self.test_config_file, "w") as f:
            json.dump(config_data, f)

        with patch("weat.config.getLog"):
            with patch.object(WeatConfig, "_load_combined_hints"):
                WeatConfig(filename=self.test_config_file, debug=False)

        with open(self.test_config_file, "r") as f:
            saved_data = json.load(f)

        self.assertNotIn("debug", saved_data)

    def test_config_invalid_json(self):
        """Test handling of invalid JSON in config file."""
        invalid_json_file = os.path.join(self.test_data_dir, "invalid_json.json")

        with patch("weat.config.getLog"):
            with self.assertRaises(RuntimeError):
                WeatConfig(filename=invalid_json_file)

    def test_config_invalid_data(self):
        """Test handling of invalid data in config file."""
        invalid_data_file = os.path.join(self.test_data_dir, "invalid_data_types.json")

        with patch("weat.config.getLog"):
            with self.assertRaises(ValueError):
                WeatConfig(filename=invalid_data_file)

    def test_config_repr(self):
        """Test string representation of config."""
        with patch("weat.config.getLog"):
            with patch.object(WeatConfig, "_load_combined_hints"):
                with patch.object(WeatConfig, "save"):
                    config = WeatConfig(filename="test.json")
                    config.combined_hints = HintsConfig()

        repr_str = repr(config)
        self.assertIn("WeatConfig", repr_str)
        self.assertIn("window_size_w=1280", repr_str)
        self.assertIn("window_size_h=800", repr_str)

    @patch("weat.config.HintsConfig.load_combined_hints")
    def test_load_combined_hints(self, mock_load_combined):
        """Test loading combined hints."""
        mock_hints = HintsConfig()
        mock_load_combined.return_value = mock_hints

        with patch("weat.config.getLog"):
            with patch.object(WeatConfig, "save"):
                config = WeatConfig(filename="test.json")

        mock_load_combined.assert_called_once()
        self.assertEqual(config.combined_hints, mock_hints)

    def test_get_combined_hints(self):
        """Test getting combined hints."""
        config_data = {
            "window_size_w": 1280,
            "window_size_h": 800,
            "hint_files": ["default"],
        }

        with open(self.test_config_file, "w") as f:
            json.dump(config_data, f)

        with patch("weat.config.getLog"):
            with patch.object(WeatConfig, "_load_combined_hints"):
                config = WeatConfig(filename=self.test_config_file)

        # Test when combined_hints is already loaded
        test_hints = HintsConfig()
        config.combined_hints = test_hints
        result = config.get_combined_hints()
        self.assertEqual(result, test_hints)

        # Test when combined_hints is None - should trigger _load_combined_hints
        config.combined_hints = None
        with patch.object(config, "_load_combined_hints") as mock_load:
            # Set the combined_hints inside the mock to simulate loading
            def side_effect():
                config.combined_hints = test_hints

            mock_load.side_effect = side_effect

            result = config.get_combined_hints()
            mock_load.assert_called_once()
            self.assertEqual(result, test_hints)


class TestRemoveHints(unittest.TestCase):
    """Test cases for RemoveHints class."""

    def test_default_remove_hints(self):
        """Test default RemoveHints creation."""
        hints = RemoveHints()
        self.assertEqual(hints.tags, [])
        self.assertEqual(hints.classes, [])
        self.assertEqual(hints.ids, [])

    def test_remove_hints_with_data(self):
        """Test RemoveHints with provided data."""
        hints = RemoveHints(
            tags=["script", "style"], classes=["ad", "popup"], ids=["footer", "header"]
        )
        self.assertEqual(hints.tags, ["script", "style"])
        self.assertEqual(hints.classes, ["ad", "popup"])
        self.assertEqual(hints.ids, ["footer", "header"])


class TestMainContentHints(unittest.TestCase):
    """Test cases for MainContentHints class."""

    def test_default_main_content_hints(self):
        """Test default MainContentHints creation."""
        hints = MainContentHints()
        self.assertEqual(hints.selectors, [])

    def test_main_content_hints_with_data(self):
        """Test MainContentHints with provided data."""
        selectors = ["main", ".content", "#article"]
        hints = MainContentHints(selectors=selectors)
        self.assertEqual(hints.selectors, selectors)


if __name__ == "__main__":
    unittest.main()
