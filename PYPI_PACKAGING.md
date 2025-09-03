# WebEater PyPI Distribution

This directory contains the files needed to package and distribute WebEater to PyPI.

## Quick Start for Publishing

1. **Install build tools:**
   ```bash
   pip install build twine
   ```

2. **Build the package:**
   ```bash
   python -m build
   ```

3. **Check the package:**
   ```bash
   twine check dist/*
   ```

4. **Upload to Test PyPI (recommended first):**
   ```bash
   twine upload --repository testpypi dist/*
   ```

5. **Upload to PyPI:**
   ```bash
   twine upload dist/*
   ```

## Important Notes

- Make sure to update the version in `pyproject.toml` before each release
- Update your email address in `pyproject.toml`
- Ensure all tests pass before publishing
- Consider adding a CHANGELOG.md file

## Testing the Package

After uploading to Test PyPI, you can test install:
```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ --no-cache-dir --force-reinstall --no-deps webeater
```