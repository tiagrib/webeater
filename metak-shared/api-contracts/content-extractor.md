# Contract: `ContentExtractor`

**Status:** Stable (v0.1.x)
**Source of truth:** `webeater/extracting.py`
**Sole current implementation:** `webeater.thirdparty.beautifulsoup.WebeaterBeautifulSoup`

An extractor turns rendered HTML into either a Markdown-flavoured plain-text string or a structured dict, biased by user-supplied hints.

## Class

```python
class ContentExtractor(ABC):
    def __init__(self): ...
    async def load(self) -> None: ...
    async def extract_content(
        self,
        url: str,
        html: str,
        include_images: bool = True,
        include_links: bool = True,
        hints: HintsConfig | None = None,
        return_dict: bool = True,
    ) -> str | dict: ...
    async def shutdown(self) -> None: ...
```

> Note: the abstract base class in `extracting.py` declares only `extract_content(self, html: str)`. The real signature used by `Webeater.get()` is the wider one above; concrete implementations and any new ones must accept it. The base class signature is a known deviation (see below).

## Lifecycle

1. **Construct** with no required arguments. The current `WebeaterBeautifulSoup.__init__` accepts optional `hint_names` and `combined_hints` parameters but ignores them — hints are passed per-call to `extract_content`. New implementations should follow the same pattern (no constructor-bound hints).
2. **`await load()`** — perform any deferred imports or setup (the in-tree implementation imports `bs4.BeautifulSoup` here to keep cold-start fast).
3. **`await extract_content(...)`** any number of times.
4. **`await shutdown()`** — release any held resources. The current implementation has none and does not override this.

## Method contracts

### `extract_content(url, html, include_images, include_links, hints, return_dict)`

- **`url`** is the canonical URL the HTML was fetched from. It is used **only** to resolve relative `src=` and `href=` attributes against an absolute base; it is not re-fetched.
- **`html`** is the raw rendered HTML produced by an `HtmlRenderer`.
- **`hints`** is a `webeater.config.HintsConfig` instance or `None`. When `None`, the extractor must operate without any selector-driven content focus or noise removal — it is not the extractor's job to load defaults.
- **`include_images`** / **`include_links`**: when `True`, gathered images and links must be included in the result. When `return_dict=False` they are appended as `## Images` and `## Links` Markdown sections; when `return_dict=True` they appear under the `images` and `links` keys.
- **`return_dict`**: when `True`, return a dict with keys `title`, `content`, and (conditionally) `images`, `links`. See `json-output.md`. When `False`, return a single string with `# {title}` and the body.
- **Exception policy**: extractors **must not** raise on malformed HTML or missing selectors. They must degrade gracefully — the in-tree implementation catches and returns the string `"Failed to extract content: {error}"` on any internal failure. New implementations should adopt the same behaviour: an empty page yields `"No content found"` (string mode) or a dict with empty content (dict mode).

### Hint application order

When `hints` is provided, implementations must:

1. **Remove** matching elements first, in this order: by `tags`, then by exact-match `classes`, then by exact-match `ids`. Matching is case-sensitive.
2. **Locate main content** by trying each selector in `main.selectors` in order. The first selector that matches at least one element wins; among matched elements, **the one with the most text wins**. This "largest match wins" rule is part of the contract — UIs frequently have multiple matches for the same selector and we want the biggest one.
3. If no `main.selectors` match, fall back to `<body>`, then to the document root.

### URL normalisation for images and links

Relative URLs in `img[src]` and `a[href]` must be normalised against `url` before being emitted:

- `//host/path` → `https://host/path`
- `/path` → `<scheme>://<host>/path`
- bare `path` → `<scheme>://<host>/<dir>/path` where `<dir>` is the directory of `url`

Anchors (`href` starting with `#`), `javascript:`, and `mailto:` links must be skipped.

### Concurrency

Extractor instances should be safe to call concurrently from multiple coroutines if the implementation library supports it (BeautifulSoup parsing is CPU-bound but stateless per call, so the in-tree implementation is effectively concurrent-safe).

## Known deviations

- The abstract base class in `webeater/extracting.py:18` declares `extract_content(self, html: str) -> str` — a much narrower signature than the real one used by `Webeater.get()`. This is a documentation bug in the base class; the real contract is the wider signature above.
- `ContentExtractor.load()` in `extracting.py:15` is declared without `self`, which would crash if called via the base class. `WebeaterBeautifulSoup` overrides it correctly. Workers fixing the base class should keep `self`.
- The Markdown emitted by `WebeaterBeautifulSoup._extract_structured_text` uses internal `>>>` / `<<<` / `>` / `<` markers as a poor-man's tree boundary tracking mechanism, which it then strips back out. This is fragile (the input HTML can contain those characters) and is a known cleanup target — see `overview.md` "What's next".
- `cleanup_whitespace` only collapses double-spaces and double-newlines; tabs and Unicode whitespace are left as-is.
- Image alt text defaults to the literal string `"Image"` when missing — not an empty string.
