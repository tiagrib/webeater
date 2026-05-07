# Contract: Hints JSON Schema

**Status:** Stable (v0.1.x). User-facing — changes are breaking.
**Source of truth:** `webeater/config.py` (pydantic models `HintsConfig`, `RemoveHints`, `MainContentHints`).
**User docs:** `webeater/hints/README.md`

A hint file is a JSON document that biases the extractor: which DOM nodes to drop before extracting, and which CSS selectors mark the main content area. Hints are loaded from `webeater/hints/{stem}.json` (bundled hints) or any user-supplied path, and are layered together to produce the **combined hints** used by the engine.

## Schema

```jsonc
{
    "remove": {
        "tags":    ["string", ...],   // HTML tag names to delete from the DOM
        "classes": ["string", ...],   // exact-match class names to delete
        "ids":     ["string", ...]    // exact-match element ids to delete
    },
    "main": {
        "selectors": ["css selector", ...]   // candidate selectors for the main content area
    }
}
```

Both top-level keys are optional. Either or both may be omitted; an empty object `{}` is a valid hint file. The `remove` and `main` objects may also each omit any of their inner keys.

### Legacy form

If `main` is provided as a JSON array, it is auto-promoted to `{ "selectors": [...] }`. This is a back-compat affordance — new files should use the object form.

```jsonc
// Legacy (still accepted)
{ "main": ["article", ".content"] }

// Preferred
{ "main": { "selectors": ["article", ".content"] } }
```

### Field semantics

| Field | Match rule | Example |
|-------|-----------|---------|
| `remove.tags` | Tag-name match. Removes every element with that tag, anywhere in the document. | `["script", "style", "nav"]` |
| `remove.classes` | Element is removed if its `class` attribute *contains* the given name (split on whitespace, exact token match). | `["sidebar", "ad"]` |
| `remove.ids` | Element is removed if its `id` attribute equals the given value exactly. | `["footer", "comments-section"]` |
| `main.selectors` | Standard CSS selectors passed to `BeautifulSoup.select`. The first selector that matches at least one element wins; the largest-by-text-length match within that selector becomes the main content. | `["article", ".article-content", "#main"]` |

`main.selectors` accepts the full BeautifulSoup CSS selector dialect, including attribute selectors (`[role="main"]`, `[class*="calendar"]`).

## Bundled hint files

These ship inside the package (`webeater/hints/`) and are referenced by stem name:

- **`default`** — broad noise removal (script/style/nav/footer/aside/ads), broad main-content selectors (`main`, `article`, `.content`, `#main`, ...). Always loaded first.
- **`news`** — strips sidebars, related-articles, social-share, comments, newsletter-signup; selects article/story bodies.
- **`sports`** — selectors biased to schedules, fixtures, calendars, match-results.

Users may add their own files alongside these or pass absolute paths through `extra_hint_files`.

## Layering and de-duplication

Hints are layered in this fixed order. Later sources extend earlier ones, never replace them.

1. `default.json` from the package (always loaded first via the implicit `["default"]` value of `WeatConfig.hint_files`).
2. Files named in `weat.json`'s `hint_files` array.
3. The inline `hints` block of `weat.json`, if present.
4. Files passed via the CLI flag `--hints name1 name2 ...`.
5. Files passed via the library kwarg `extra_hint_files=[...]` on `WeatConfig(...)`.

Layering rules:

- All `remove.tags`, `remove.classes`, `remove.ids`, and `main.selectors` lists are **concatenated** across sources.
- Each list is then **de-duplicated while preserving the first-occurrence order**. This is contractual — the order of `main.selectors` controls which selector is tried first.
- A missing `remove` or `main` block in a layer is a no-op for that layer.

## Resolving hint names to files

When a hint name is referenced (e.g. `"news"`), the loader looks for `<HINTS_DIR>/<name>.json` where `HINTS_DIR` defaults to `webeater/hints/` inside the installed package. The `hints_dir` argument to `HintsConfig.load_combined_hints` allows callers to redirect this lookup; absolute paths are not currently supported via that codepath — pass an alternate `hints_dir`.

## Failure modes

- **File not found**: a warning is logged and the loader continues with the remaining sources. The missing file does **not** abort the load.
- **Invalid JSON or malformed structure**: an error is logged and the loader returns an empty `HintsConfig` for that file (skipped, but the others still apply).
- **Empty file**: treated as `{}`.

## Known deviations

- `RemoveHints.classes` matching: the current code-side rule is "classes attribute contains the token" — implemented by `lambda tag: tag.has_attr("class") and class_name in tag.get("class", [])`. This is a token-membership check, not a substring check. Users writing class hints should pass the exact class name, not a substring.
- `RemoveHints.ids` is exact-match equality, not membership.
- The `combined_hints` field on `WeatConfig` is `exclude=True` and is therefore **not** persisted when `WeatConfig.save()` writes `weat.json` back. Only the source-of-truth `hint_files` and inline `hints` are persisted.
