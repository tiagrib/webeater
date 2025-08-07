import pydantic
import json

from weat.log import getLog

DEFAULT_CONFIG_FILE = "weat.json"


class WeatConfig(pydantic.BaseModel):
    """Configuration for the Weat application.
    This class defines the window size for the application.
    """

    window_size_w: int = 1280
    window_size_h: int = 800

    filename: str = DEFAULT_CONFIG_FILE

    @pydantic.field_validator("window_size_w", "window_size_h")
    @classmethod
    def validate_positive(cls, v):
        if v <= 0:
            raise ValueError("Window dimensions must be positive")
        return v

    def __init__(self, filename=DEFAULT_CONFIG_FILE):
        """Initialize the configuration from a file."""
        try:
            with open(filename, "r") as f:
                data = json.loads(f.read())
                getLog().info(f"Loading configuration from {filename}")
                super().__init__(**data)
        except FileNotFoundError:
            # If the file does not exist, initialize with default values
            getLog().info(
                f"Configuration file {filename} not found. Using default values."
            )
            super().__init__()
        except pydantic.ValidationError as e:
            raise ValueError(f"Invalid configuration in {filename}: {e}") from e
        except Exception as e:
            raise RuntimeError(
                f"Failed to load configuration from {filename}: {e}"
            ) from e
        self.filename = filename
        self.save()

    def save(self):
        """Save the current configuration to the file."""
        try:
            with open(self.filename, "w") as f:
                f.write(self.model_dump_json(indent=4))
            getLog().info(f"Configuration saved to {self.filename}")
        except Exception as e:
            raise RuntimeError(f"Failed to save configuration to {self.filename}: {e}")

    def __repr__(self):
        return f"WeatConfig(window_size_w={self.window_size_w}, window_size_h={self.window_size_h})"
