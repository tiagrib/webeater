import pydantic
import json
import os
from typing import List, Optional

from webeater.log import getLog

DEFAULT_CONFIG_FILE = "weat.json"


class RemoveHints(pydantic.BaseModel):
    """Hints for removing unwanted elements."""

    tags: List[str] = []
    classes: List[str] = []
    ids: List[str] = []


class MainContentHints(pydantic.BaseModel):
    """Hints for finding main content areas."""

    selectors: List[str] = []


class HintsConfig(pydantic.BaseModel):
    """Configuration for hints in the Weat application.
    This class defines the hints to be used in the application.
    """

    remove: Optional[RemoveHints] = None
    main: Optional[MainContentHints] = None

    @classmethod
    def load_from_file(cls, filepath: str) -> "HintsConfig":
        """Load hints configuration from a JSON file."""
        try:
            with open(filepath, "r") as f:
                data = json.load(f)

                # if 'main' is provided as a list, convert it to a MainContentHints object
                if "main" in data and isinstance(data["main"], list):
                    data["main"] = {"selectors": data["main"]}

                return cls(**data)
        except FileNotFoundError:
            getLog().warning(f"Hints file {filepath} not found. Using empty hints.")
            return cls()
        except Exception as e:
            getLog().error(f"Failed to load hints from {filepath}: {e}")
            return cls()

    @classmethod
    def load_combined_hints(
        cls,
        hint_files: List[str],
        direct_hints: Optional["HintsConfig"] = None,
        hints_dir: str = "hints",
    ) -> "HintsConfig":
        """Load and combine multiple hint files and direct hints into a single configuration."""
        # Start with direct hints if provided, otherwise create empty
        if direct_hints:
            combined_hints = direct_hints
        else:
            combined_hints = cls()

        # Load and combine hint files
        for hint_name in hint_files:
            filepath = os.path.join(hints_dir, f"{hint_name}.json")
            hint_config = cls.load_from_file(filepath)

            # Combine remove hints
            if hint_config.remove:
                if combined_hints.remove is None:
                    combined_hints.remove = RemoveHints()

                combined_hints.remove.tags.extend(hint_config.remove.tags)
                combined_hints.remove.classes.extend(hint_config.remove.classes)
                combined_hints.remove.ids.extend(hint_config.remove.ids)

            # Combine main content hints
            if hint_config.main:
                if combined_hints.main is None:
                    combined_hints.main = MainContentHints()

                combined_hints.main.selectors.extend(hint_config.main.selectors)

        # Remove duplicates while preserving order
        if combined_hints.remove:
            combined_hints.remove.tags = list(dict.fromkeys(combined_hints.remove.tags))
            combined_hints.remove.classes = list(
                dict.fromkeys(combined_hints.remove.classes)
            )
            combined_hints.remove.ids = list(dict.fromkeys(combined_hints.remove.ids))

        if combined_hints.main:
            combined_hints.main.selectors = list(
                dict.fromkeys(combined_hints.main.selectors)
            )

        return combined_hints

    def __repr__(self):
        main_count = len(self.main.selectors) if self.main else 0
        return f"HintsConfig(remove={self.remove}, main={main_count} selectors)"


class WeatConfig(pydantic.BaseModel):
    """Configuration for the Weat application.
    This class defines the window size for the application.
    """

    window_size_w: int = 1280
    window_size_h: int = 800
    hint_files: List[str] = ["default"]  # List of hint file names to load
    hints: Optional[HintsConfig] = None  # Direct hint configuration data
    combined_hints: Optional[HintsConfig] = pydantic.Field(
        None, exclude=True
    )  # Final combined hints (computed)

    filename: str = pydantic.Field(DEFAULT_CONFIG_FILE, exclude=True)
    debug: bool = False

    @pydantic.field_validator("window_size_w", "window_size_h")
    @classmethod
    def validate_positive(cls, v):
        if v <= 0:
            raise ValueError("Window dimensions must be positive")
        return v

    def __init__(
        self,
        filename=DEFAULT_CONFIG_FILE,
        extra_hint_files: List[str] = None,
        debug=False,
        **kwargs,
    ):
        """Initialize the configuration from a file."""
        try:
            with open(filename, "r") as f:
                data = json.loads(f.read())
                getLog().info(f"Loading configuration from {filename}")
                super().__init__(**data, **kwargs)
        except FileNotFoundError:
            # If the file does not exist, initialize with default values
            getLog().info(
                f"Configuration file {filename} not found. Using default values."
            )
            super().__init__(**kwargs)
        except pydantic.ValidationError as e:
            raise ValueError(f"Invalid configuration in {filename}: {e}") from e
        except Exception as e:
            raise RuntimeError(
                f"Failed to load configuration from {filename}: {e}"
            ) from e
        self.filename = filename

        # Add extra hint files from command line or other sources
        if extra_hint_files:
            # Combine with existing hint files, avoiding duplicates
            all_hints = self.hint_files + extra_hint_files
            self.hint_files = list(
                dict.fromkeys(all_hints)
            )  # Remove duplicates while preserving order

        # Immediately load and combine all hints
        self._load_combined_hints()

        self.save()

    def _load_combined_hints(self, hints_dir: str = "hints"):
        """Load and combine all hints into the combined_hints field."""
        self.combined_hints = HintsConfig.load_combined_hints(
            hint_files=self.hint_files, direct_hints=self.hints, hints_dir=hints_dir
        )
        getLog().debug(f"Combined hints loaded: {self.combined_hints}")

    def get_combined_hints(self) -> HintsConfig:
        """Get the combined hints configuration."""
        if self.combined_hints is None:
            self._load_combined_hints()
        return self.combined_hints

    def save(self):
        """Save the current configuration to the file."""
        try:
            # Create a dict with selective exclusions
            data = self.model_dump(exclude_none=True)

            # Remove debug field if it's False (default value)
            if data.get("debug") is False:
                data.pop("debug", None)

            with open(self.filename, "w") as f:
                f.write(json.dumps(data, indent=4))
            getLog().debug(f"Configuration saved to {self.filename}")
        except Exception as e:
            raise RuntimeError(f"Failed to save configuration to {self.filename}: {e}")

    def __repr__(self):
        return f"WeatConfig(window_size_w={self.window_size_w}, window_size_h={self.window_size_h}, hint_files={self.hint_files}, combined_hints={self.combined_hints})"
