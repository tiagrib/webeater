# Contract: JSON Output Shape

**Status:** Stable (v0.1.x). User-facing — changes are breaking.
**Source of truth:** `webeater.thirdparty.beautifulsoup.WebeaterBeautifulSoup.extract_content` and `webeater.eater.Webeater.get`.

This contract pins down the dict returned by `Webeater.get(..., return_dict=True)` and printed by the CLI under `--json`.

## Shape

```jsonc
{
    "title":      "string | null",   // contents of <title>, stripped; null if no <title>
    "content":    "string",          // Markdown-flavoured plain text (body only — no title heading)
    "images":     ["![alt](url)", ...],   // present iff include_images=True (i.e. content_only=False)
    "links":      ["[text](url)",  ...],   // present iff include_links=True  (i.e. content_only=False)
    "fetch_time": "0:00:01.234567"   // str(timedelta), total time from get() start to extract end
}
```

### Field-level guarantees

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `title` | `str | None` | always | Stripped of surrounding whitespace. `None` only if the page has no `<title>` element. |
| `content` | `str` | always | The extracted Markdown body. **Does not** include a top-level `# {title}` heading (that is added only in string-output mode). May be the literal string `"Failed to extract content: {error}"` on extractor error. |
| `images` | `list[str]` | only when `include_images=True` (CLI: not `--content-only`) | Each item is a Markdown image: `` `![{alt}]({absolute_url})` ``. Alt text defaults to the literal `"Image"` if the source had no `alt`. |
| `links` | `list[str]` | only when `include_links=True` (CLI: not `--content-only`) | Each item is a Markdown link: `` `[{text}]({absolute_url})` ``. `text` falls back to the URL when the anchor has no visible text. `javascript:`, `mailto:`, and pure-fragment (`#...`) anchors are excluded. |
| `fetch_time` | `str` | always | `str(datetime.timedelta)` — e.g. `"0:00:01.234567"`. **String, not float.** Includes both render and extract time. |

### Failure cases

- **Renderer failure** (Selenium timeout, navigation error, etc.): `Webeater.get()` returns `None` instead of a dict. Callers must handle this. The renderer is auto-reloaded before the next call.
- **Extractor failure** (invalid HTML, internal exception): the dict is still returned, but `content` will be the string `"Failed to extract content: {error}"`. `images` and `links` may be empty or absent. `fetch_time` is still set.
- **Empty page**: `content` will be `"No content found"` in string mode; in dict mode `content` may be empty or that same fallback string. (See known deviations below.)

## Relationship to the string output

When `return_dict=False`, the same extraction produces a single string laid out as:

```
# {title}

{content}

## Images

![alt1](url1)
![alt2](url2)

## Links

[text1](url1)
[text2](url2)
```

The `## Images` / `## Links` sections are only emitted when the corresponding `include_*` flag is true and the list is non-empty. The string output is whitespace-cleaned via `cleanup_whitespace`; the dict output's `content` is **also** whitespace-cleaned, but its image/link lists are raw Markdown items (no section headers).

## CLI mapping

| CLI flag | Effect on output |
|---------|------------------|
| _(none)_ | string output, includes Images and Links sections |
| `--json` | dict output (`return_dict=True`) |
| `--content-only` | string output without Images/Links sections (`include_images=False`, `include_links=False`) |
| `--json --content-only` | dict output without `images`/`links` keys |

In interactive mode the same toggles apply per-line via the `j!`, `c!`, and `jc!`/`cj!` prefixes (see `public-api.md`).

## Known deviations

- The "No content found" fallback (`webeater/thirdparty/beautifulsoup.py`) is only emitted in **string mode**. In dict mode, an empty page yields a dict with `content = ""` rather than `"No content found"`. Workers should not assume the fallback string is present in dict mode.
- `fetch_time` is set **only** in dict mode. In string mode it is logged but not returned.
- The dict's `content` does **not** include the title as a heading; if a consumer wants `# {title}` prepended, they must do it themselves.
- `WebeaterBeautifulSoup` builds the `images` / `links` lists from the chosen main-content element only — anything outside the matched main selector is not included. This means `remove.tags = ["nav"]` removing a global nav will also remove its links from the output, which is intended.
