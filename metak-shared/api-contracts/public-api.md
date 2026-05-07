# Contract: Public Library and CLI Surface

**Status:** Stable (v0.1.x). User-facing — changes are breaking.
**Source of truth:** `webeater/__init__.py`, `webeater/eater.py`, `webeater/__main__.py`, `webeater/config.py`.

This document pins down what library consumers and CLI users may rely on. Anything not listed here is internal and may change without a deprecation notice.

## Library surface

### Public exports (from `webeater`)

```python
from webeater import Webeater
```

`__all__ = ["Webeater"]`. `__version__`, `__author__`, `__email__`, `__license__` are also exposed as module attributes.

### `Webeater.create(config: WeatConfig | None = None) -> Webeater`

Async factory. The only supported way to construct a ready-to-use engine.

- If `config is None`, a default `WeatConfig()` is constructed (which will read `./weat.json` if present, or fall back to defaults).
- Returns a fully-initialised `Webeater`: Selenium driver booted, BeautifulSoup loaded.
- Must be `await`-ed.
- May raise on rendering-backend startup failure (Chrome missing, etc.).

### `Webeater.get(url, hints=None, return_dict=False, content_only=False)`

Async. Fetches and extracts.

- **`url`** (required, positional): an `http://` or `https://` URL. URL validation is **the caller's responsibility** — invalid schemes are not rejected here, they are simply passed to Selenium and will likely fail.
- **`hints`** (`HintsConfig | None`): per-call hint override. **Currently the only supported value is `None`** — the implementation falls through to `self.content_extraction_hints` (the combined hints from config). This parameter is reserved for future per-call overrides; do not rely on passing a non-None value.
- **`return_dict`** (`bool`, default `False`): see `json-output.md`.
- **`content_only`** (`bool`, default `False`): when `True`, skip image and link extraction.
- **Returns**: `str` or `dict` per `return_dict`, or `None` on renderer failure.
- **Renderer failure recovery**: on a Selenium exception, `get()` triggers `html_renderer.reload()` and returns `None`. The engine remains usable for subsequent calls.

### `Webeater.shutdown() -> None`

Async. Quits the Selenium driver. The extractor has no resources to release. Idempotent only if you don't call `get()` again afterwards — there is no reload-on-use guard.

### Configuration: `WeatConfig`

Importable as `from webeater.config import WeatConfig, HintsConfig, RemoveHints, MainContentHints`.

```python
WeatConfig(
    filename: str = "weat.json",        # path to load/save
    extra_hint_files: list[str] = None, # appended to hint_files, de-duped
    debug: bool = False,
    # …or any field name as a kwarg
)
```

- Reads `filename` if it exists, otherwise uses defaults.
- Calls `_load_combined_hints()` immediately so `combined_hints` is populated by the time `__init__` returns.
- **Calls `save()` at the end of `__init__`**, persisting the merged config back to `filename`. This is intentional — the file rewrites itself with normalised hint lists on every load. Workers must be aware that constructing a `WeatConfig` is a side-effecting operation on disk.

#### Public fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `window_size_w` | `int` | `1280` | Validated `> 0`. |
| `window_size_h` | `int` | `800`  | Validated `> 0`. |
| `hint_files` | `list[str]` | `["default"]` | Hint stem names to load from `HINTS_DIR`. |
| `hints` | `HintsConfig | None` | `None` | Inline hints; layered between `hint_files` and CLI/library extras. |
| `combined_hints` | `HintsConfig | None` | computed | **Excluded from serialization.** |
| `filename` | `str` | `"weat.json"` | **Excluded from serialization.** |
| `debug` | `bool` | `False` | Excluded from `save()` when `False`. |

## CLI surface

Console scripts: **`weat`** and **`webeater`**. Both invoke `webeater.__main__:cli_main`.

### Flags

| Flag | Argument | Default | Description |
|------|---------|---------|-------------|
| `url` (positional) | string | _(none)_ | URL to fetch. If omitted, the CLI enters interactive mode. |
| `-c`, `--config` | path | `weat.json` | Config file to load (and rewrite). |
| `--hints` | one or more stem names | _(none)_ | Additional hint files to layer on top of those in the config. |
| `--debug` | flag | off | Enables debug logging via `webeater.log.setLogDebug(True)`. |
| `--silent` | flag | off | Suppresses info/debug logs and prints **only** the result or `Error: ...`. Useful for scripts. |
| `--json` | flag | off | Returns a JSON-style dict (`return_dict=True`). |
| `--content-only` | flag | off | Skips image and link extraction. |

### URL validation

URLs must start with `http://` or `https://`. The CLI rejects anything else **before** passing the URL to the engine, with the message `"Please provide a valid URL starting with http:// or https://"` (or `"Error: ..."` in silent mode).

### Output formatting

In one-shot mode:

- Default: `Content fetched from {url}: {result}` to stdout.
- `--silent`: just `{result}` on a single line, or `Error: {message}` on failure.

### Interactive (REPL) mode

Entered when no `url` is passed. Prompt: `Enter a URL to fetch content (or 'q' to quit): `.

Per-line shortcuts (case-insensitive prefix on the URL):

| Prefix | Effect |
|--------|--------|
| `j!url` | Equivalent to `--json` for this URL only. |
| `c!url` | Equivalent to `--content-only` for this URL only. |
| `jc!url` / `cj!url` | Both. |
| `q` | Exit the REPL. |
| _(empty line)_ | Re-prompt; no error. |

The base CLI flags (`--silent`, etc.) still apply to every line in the REPL.

## Stability and breaking-change policy

- **Breaking changes** to anything in this document require a major-version bump (or a 0.x → 0.y bump while in alpha) and a CHANGELOG entry.
- The `hints` parameter on `Webeater.get()` is reserved-but-unsupported as of v0.1.x. Adding real per-call hint overrides is **not** a breaking change.
- The renderer / extractor abstract base classes (`HtmlRenderer`, `ContentExtractor`) are **not** re-exported from `webeater.__init__` and are therefore not considered public for v0.1.x. Power users importing them directly do so at their own risk; the contracts in `html-renderer.md` and `content-extractor.md` describe what they get.

## Known deviations

- `Webeater.shutdown()` does not gate on `self.html_renderer` being live — calling it twice will call `Driver.quit()` twice and raise on the second call.
- `WeatConfig.__init__` always calls `save()`, even if no fields changed. This rewrites `weat.json` on every load, which is surprising for a "config object" and shows up as a working-tree dirty file in some workflows.
- The default `WeatConfig` has `window_size_w=1280, window_size_h=800`, but the `SeleniumRuntime` module-level constants are `WINDOW_SIZE_W=1920, WINDOW_SIZE_H=3000`, and the bundled `weat.json` ships with `1920 / 3000`. The two defaults disagree; the config wins when one is provided, and the runtime constants are used only as fallbacks.
- The `--debug` flag is consumed by the logger before `WeatConfig` reads its own `debug` field, so if `weat.json` has `"debug": true` and the CLI is invoked without `--debug`, log level is **not** raised. This is a known minor inconsistency.
