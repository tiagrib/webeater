#!/usr/bin/env python3
"""
Automated publishing script for webeater package.

This script handles:
- Version management in __init__.py and pyproject.toml
- Running tests with tox
- Building the package
- Publishing to Test PyPI or PyPI

Usage:
    python publish.py [test|release]
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional


class PublishError(Exception):
    """Custom exception for publishing errors."""

    pass


class WebeaterPublisher:
    """Handles the publishing workflow for webeater package."""

    def __init__(self, mode: str = "test", skip_tox: bool = False):
        self.mode = mode
        self.skip_tox = skip_tox
        self.root_path = Path(__file__).parent
        self.init_file = self.root_path / "webeater" / "__init__.py"
        self.pyproject_file = self.root_path / "pyproject.toml"
        self.python_exe = sys.executable  # Use current Python executable

        # Validate files exist
        if not self.init_file.exists():
            raise PublishError(f"__init__.py not found at {self.init_file}")
        if not self.pyproject_file.exists():
            raise PublishError(f"pyproject.toml not found at {self.pyproject_file}")

    def get_current_version(self) -> str:
        """Extract current version from __init__.py."""
        content = self.init_file.read_text(encoding="utf-8")
        match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
        if not match:
            raise PublishError("Could not find __version__ in __init__.py")
        return match.group(1)

    def validate_version(self, version: str) -> bool:
        """Validate version string format (major.minor.patch)."""
        pattern = r"^\d+\.\d+\.\d+$"
        return bool(re.match(pattern, version))

    def increment_patch_version(self, version: str) -> str:
        """Increment the patch version number."""
        parts = version.split(".")
        if len(parts) != 3:
            raise PublishError(f"Invalid version format: {version}")

        try:
            major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
            return f"{major}.{minor}.{patch + 1}"
        except ValueError:
            raise PublishError(f"Invalid version format: {version}")

    def get_new_version(self, current_version: str) -> str:
        """Prompt user for new version or auto-increment."""
        print(f"\nCurrent version: {current_version}")
        print("Options:")
        print("1. Press Enter to auto-increment patch version")
        print("2. Enter a specific version (format: major.minor.patch)")

        user_input = input(
            "\nEnter new version (or press Enter for auto-increment): "
        ).strip()

        if not user_input:
            # Auto-increment patch version
            new_version = self.increment_patch_version(current_version)
            print(f"Auto-incrementing to: {new_version}")
            return new_version

        # Validate user-provided version
        if not self.validate_version(user_input):
            raise PublishError(
                f"Invalid version format: {user_input}. Use major.minor.patch (e.g., 1.2.3)"
            )

        return user_input

    def version_exists_on_pypi(self, version: str) -> bool:
        """Check if the given version exists on PyPI or Test PyPI."""
        import requests

        package_name = "webeater"
        if self.mode == "test":
            url = f"https://test.pypi.org/pypi/{package_name}/json"
        else:
            url = f"https://pypi.org/pypi/{package_name}/json"
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                return False
            data = resp.json()
            return version in data.get("releases", {})
        except Exception:
            return False

    def update_init_version(self, new_version: str) -> None:
        """Update version in __init__.py."""
        current_version = self.get_current_version()

        if new_version == current_version:
            print(f"✓ Version {new_version} already set in {self.init_file}")
            return

        content = self.init_file.read_text(encoding="utf-8")

        # Replace __version__ line
        new_content = re.sub(
            r'__version__\s*=\s*["\'][^"\']+["\']',
            f'__version__ = "{new_version}"',
            content,
        )

        if new_content == content:
            raise PublishError("Could not update version in __init__.py")

        self.init_file.write_text(new_content, encoding="utf-8")
        print(f"✓ Updated version in {self.init_file}")

    def update_pyproject_version(self, new_version: str) -> None:
        """Update version in pyproject.toml."""
        content = self.pyproject_file.read_text(encoding="utf-8")

        # Check if version is already set
        current_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
        if current_match and current_match.group(1) == new_version:
            print(f"✓ Version {new_version} already set in {self.pyproject_file}")
            return

        # Replace version line in [project] section
        new_content = re.sub(
            r'(version\s*=\s*)["\'][^"\']+["\']', f'\\1"{new_version}"', content
        )

        if new_content == content:
            raise PublishError("Could not update version in pyproject.toml")

        self.pyproject_file.write_text(new_content, encoding="utf-8")
        print(f"✓ Updated version in {self.pyproject_file}")

    def run_command_with_streaming(
        self, command: list, description: str, cwd: Optional[Path] = None
    ) -> None:
        """Run a command with real-time output streaming."""
        print(f"\n🔄 {description}...")
        print(f"Running: {' '.join(command)}")

        try:
            process = subprocess.Popen(
                command,
                cwd=cwd or self.root_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            # Stream output in real-time
            for line in process.stdout:
                print(line, end="")

            # Wait for process to complete
            return_code = process.wait()

            if return_code != 0:
                raise subprocess.CalledProcessError(return_code, command)

        except subprocess.CalledProcessError as e:
            print(f"\n❌ Error: {description} failed")
            print(f"Return code: {e.returncode}")
            raise PublishError(f"{description} failed with return code {e.returncode}")

        print(f"\n✓ {description} completed successfully")

    def run_tox(self) -> None:
        """Run tox to ensure all tests pass."""
        self.run_command_with_streaming(["tox"], "Running tests with tox")

    def build_package(self) -> None:
        """Build the package wheel and source distribution."""
        # Clean previous builds
        dist_path = self.root_path / "dist"
        if dist_path.exists():
            import shutil

            shutil.rmtree(dist_path)
            print("✓ Cleaned previous build artifacts")

        self.run_command_with_streaming(
            [self.python_exe, "-m", "build"], "Building package"
        )

    def check_package(self) -> None:
        """Check the built package with twine."""
        self.run_command_with_streaming(
            ["twine", "check", "dist/*"], "Checking package with twine"
        )

    def upload_package(self, new_version: str) -> None:
        """Upload package to PyPI or Test PyPI."""
        target = "Test PyPI" if self.mode == "test" else "PyPI"

        print(f"\n⚠️  About to upload version {new_version} to {target}")

        if self.mode == "release":
            print(
                "🚨 WARNING: This will upload to the REAL PyPI! This action cannot be undone."
            )

        confirm = (
            input(f"Are you sure you want to upload to {target}? (yes/y/no/n): ")
            .strip()
            .lower()
        )

        if confirm not in ["yes", "y"]:
            print("❌ Upload cancelled by user")
            sys.exit(0)

        if self.mode == "test":
            command = ["twine", "upload", "--repository", "testpypi", "dist/*"]
        else:
            command = ["twine", "upload", "dist/*"]

        self.run_command_with_streaming(command, f"Uploading to {target}")

        # Provide installation instructions
        print(f"\n🎉 Successfully uploaded to {target}!")
        if self.mode == "test":
            print("\nTo test the package, run:")
            print(
                f"pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ webeater=={new_version}"
            )
        else:
            print("\nTo install the package, run:")
            print(f"pip install webeater=={new_version}")

    def publish(self) -> None:
        """Main publishing workflow."""
        try:
            print(f"🚀 Starting webeater publishing workflow (mode: {self.mode})")

            # Run tests (unless skipped)
            if self.skip_tox:
                print("\n⚠️  Skipping tox tests as requested")
            else:
                self.run_tox()

            # Get current version
            current_version = self.get_current_version()

            # Get new version from user
            new_version = self.get_new_version(current_version)

            # Check if version exists on PyPI/TestPyPI
            if self.version_exists_on_pypi(new_version):
                print(
                    f"❌ Version {new_version} already exists on the target PyPI repository. Aborting."
                )
                sys.exit(1)

            # Update version in both files
            self.update_init_version(new_version)
            self.update_pyproject_version(new_version)

            # Build package
            self.build_package()

            # Check package
            self.check_package()

            # Upload package
            self.upload_package(new_version)

        except PublishError as e:
            print(f"\n❌ Publishing failed: {e}")
            sys.exit(1)
        except KeyboardInterrupt:
            print("\n❌ Publishing cancelled by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Publish webeater package to PyPI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python publish.py                    # Publish to Test PyPI (default)
  python publish.py test               # Publish to Test PyPI
  python publish.py release            # Publish to PyPI (production)
  python publish.py --skip-tox         # Skip tests and publish to Test PyPI
  python publish.py release --skip-tox # Skip tests and publish to PyPI
        """,
    )
    parser.add_argument(
        "mode",
        nargs="?",
        choices=["test", "release"],
        default="test",
        help="Publishing mode: 'test' for Test PyPI, 'release' for PyPI (default: test)",
    )
    parser.add_argument(
        "--skip-tox",
        action="store_true",
        help="Skip running tox tests before publishing",
    )

    args = parser.parse_args()

    # Verify we're in the right directory
    if not Path("pyproject.toml").exists():
        print(
            "❌ Error: pyproject.toml not found. Please run this script from the project root."
        )
        sys.exit(1)

    # Check required tools are installed
    missing_tools = []

    # Check tox (only if not skipping)
    if not args.skip_tox:
        try:
            subprocess.run(["tox", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing_tools.append("tox")

    # Check twine
    try:
        subprocess.run(["twine", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        missing_tools.append("twine")

    # Check requests
    try:
        import requests  # noqa: F401
    except ImportError:
        missing_tools.append("requests")

    # Check build (as python module)
    try:
        subprocess.run(
            [sys.executable, "-m", "build", "--version"],
            capture_output=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        missing_tools.append("build")

    if missing_tools:
        print(f"❌ Error: Missing required tools: {', '.join(missing_tools)}")
        print(f"Install them with: pip install {' '.join(missing_tools)}")
        sys.exit(1)

    # Create publisher and run
    publisher = WebeaterPublisher(args.mode, skip_tox=args.skip_tox)
    publisher.publish()


if __name__ == "__main__":
    main()
