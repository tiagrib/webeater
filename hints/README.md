# Hints System

The hints system allows you to configure how the WebeaterBeautifulSoup extractor processes web pages. Hints can be provided in several ways:

1. **Hint Files**: JSON files in the `hints/` directory
2. **Direct Configuration**: Hints directly embedded in the main config file
3. **Command Line**: Additional hint files specified via command line arguments
4. **Library Usage**: Hints passed when creating a Webeater instance

## Hint Sources (Priority Order)

1. **Default Hints**: Always loaded first (`default.json`)
2. **Config File Hints**: Hint files specified in `hint_files` array
3. **Direct Config Hints**: Hints directly in the `hints` object in config
4. **Command Line Hints**: Additional hint files from `--hints` argument
5. **Library Hints**: Hints passed to `Webeater.create(extra_hint_files=...)`

All sources are combined, with later sources taking precedence for duplicates.

## Hint Structure

Each hint file is a JSON file with the following optional structure:

```json
{
    "remove": {
        "tags": ["script", "style", "nav"],
        "classes": ["menu", "footer", "ad"],
        "ids": ["header", "sidebar"]
    },
    "main": {
        "selectors": [
            "main",
            "article",
            ".content",
            "#main-content"
        ]
    }
}
```

### Remove Section
- `tags`: HTML tags to completely remove from the page
- `classes`: CSS classes to remove (exact match)
- `ids`: Element IDs to remove (exact match)

### Main Section
- `selectors`: Array of CSS selectors used to find the main content area
- The extractor will try each selector in order and use the first match with content

## Configuration Examples

### 1. Using Hint Files Only
```json
{
    "window_size_w": 1920,
    "window_size_h": 1080,
    "hint_files": ["default", "news", "sports"]
}
```

### 2. Using Direct Hints
```json
{
    "window_size_w": 1920,
    "window_size_h": 1080,
    "hint_files": ["default"],
    "hints": {
        "remove": {
            "classes": ["custom-ad", "popup"]
        },
        "main": {
            "selectors": [".my-content", "#article-body"]
        }
    }
}
```

### 3. Command Line Usage
```bash
# Use specific config with additional hints
python __main__.py --config weat-news.json --hints sports custom

# Extract specific URL with custom hints
python __main__.py https://example.com --hints news
```

### 4. Library Usage
```python
# Create config first with all hints
config = WeatConfig(
    filename="custom-config.json",
    extra_hint_files=["news", "sports"]
)

# Pass the fully configured config to Webeater
engine = await Webeater.create(config=config)

# Or create config with direct hints
config = WeatConfig(
    hint_files=["default"],
    hints=HintsConfig(
        remove=RemoveHints(classes=["ads"]),
        main=MainContentHints(selectors=[".content"])
    )
)
engine = await Webeater.create(config=config)
```

## Architecture

The system follows a clear separation of concerns:

1. **Config Creation**: All hint loading and combining happens during `WeatConfig` initialization
2. **Engine Creation**: `Webeater.create()` receives a fully configured config object
3. **Extraction**: The extractor uses the pre-combined hints directly

This ensures that:
- All hint loading is done upfront
- The config object is immutable once created
- The Webeater engine doesn't need to know about hint loading details
- Library users get a clean, simple API

## Configuration

Configure which hints to use in your `weat.json` file:

```json
{
    "window_size_w": 1920,
    "window_size_h": 1080,
    "hints": ["default", "news", "sports"]
}
```

## Available Hints

- `default.json`: General-purpose extraction rules
- `news.json`: Optimized for news websites
- `sports.json`: Optimized for sports websites with schedules/fixtures

## Creating Custom Hints

1. Create a new JSON file in the `hints/` directory
2. Define the removal and main content rules
3. Add the hint name (without .json) to your config file

Multiple hints are combined - all removal rules are merged, and main selectors are tried in the order they appear across all hint files.