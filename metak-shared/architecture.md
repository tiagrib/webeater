# System Architecture

## Overview

WebEater is a single Python package (`webeater/`) with no out-of-process services. The architecture is a small pipeline:

```
URL ──► HtmlRenderer ──► raw HTML ──► ContentExtractor ──► Markdown text │ JSON dict
         (Selenium)                       (BeautifulSoup)                     │
                                                                              ▼
                                                                          consumer
                                                                       (CLI │ library)
```

Two abstract base classes define the only meaningful internal seams:

- `webeater.rendering.HtmlRenderer` — fetches and renders a URL into a fully-loaded HTML string. Implemented by `webeater.thirdparty.selenium.SeleniumRuntime`.
- `webeater.extracting.ContentExtractor` — turns rendered HTML into either Markdown text or a dict with title/content/images/links. Implemented by `webeater.thirdparty.fastbs.WebeaterFastBS` (default) and `webeater.thirdparty.beautifulsoup.WebeaterBeautifulSoup` (legacy, opt-in via `WeatConfig.extractor="bs"`).

These two interfaces are documented as contracts in `metak-shared/api-contracts/` because they are the swap points if the project ever grows alternative renderers or extractors. The hints JSON schema and the library/CLI public surface are also documented as contracts because they are user-facing.

## Service Map

| Module | Responsibility | Talks to |
|--------|---------------|----------|
| `webeater.eater.Webeater` | Top-level facade. Holds config, owns the renderer and extractor, exposes async `create()` and `get()`. | `WeatConfig`, `HtmlRenderer`, `ContentExtractor` |
| `webeater.config` | Pydantic models (`WeatConfig`, `HintsConfig`, `RemoveHints`, `MainContentHints`). Loads/saves `weat.json`, layers and de-duplicates hint files from `webeater/hints/`. | filesystem (`weat.json`, `hints/*.json`) |
| `webeater.rendering.HtmlRenderer` (abstract) | Async `load(window_size_w, window_size_h)`, `get_rendered_html(url, interact=False)`, `shutdown()`. | implementation-specific |
| `webeater.thirdparty.selenium.SeleniumRuntime` | Concrete renderer. Headless Chrome via Selenium, eager page-load strategy, multi-pass scroll to trigger lazy loads, hard 5s page-load timeout. | Chrome (subprocess) |
| `webeater.extracting.ContentExtractor` (abstract) | Async `load()`, `extract_content(url, html, hints, return_dict, include_images, include_links)`, `shutdown()`. | implementation-specific |
| `webeater.thirdparty.beautifulsoup.WebeaterBeautifulSoup` (legacy) | Concrete `ContentExtractor`. Strips by tag/class/id from hints, picks main content by hint selectors (largest match wins), walks the tree to emit Markdown-flavoured structured text, optionally appends images/links. Selected via `WeatConfig.extractor="bs"`. | `bs4` |
| `webeater.thirdparty.fastbs.WebeaterFastBS` (default) | Concrete `ContentExtractor`. Hand-rolled clean-tree walker over a `bs4`-parsed DOM; emits GitHub-Flavoured Markdown (including real tables) without a third-party markdown library. Default extractor since T3. | `bs4` |
| `webeater.__main__` | CLI entrypoint (`weat`, `webeater` console scripts). Parses args, builds `WeatConfig`, awaits `Webeater.create()`, dispatches one-shot or REPL. | terminal |
| `webeater.log` | Singleton `coloredlogs` setup with global debug/silent toggles. | stderr |
| `webeater.util.cleanup_whitespace` | Whitespace collapse helper used by the extractor. | — |
| `webeater/hints/*.json` | Bundled hint files (`default`, `news`, `sports`); installed as package data. | loaded by `HintsConfig` |
| `weat.json` (cwd) | Persisted user configuration; written back by `WeatConfig.save()` after every load. | filesystem |

## Data flow

1. **Configuration phase** (`WeatConfig.__init__`): read `weat.json` from cwd if present, merge `extra_hint_files`, then call `_load_combined_hints()` which walks `webeater/hints/{name}.json` for each hint name, layering `remove.tags / remove.classes / remove.ids / main.selectors` and removing duplicates while preserving order. The combined hints are stored in a non-persisted `combined_hints` field. `save()` is then called to persist the merged config back to disk.
2. **Engine creation** (`Webeater.create(config)`): instantiates `SeleniumRuntime` and `WebeaterBeautifulSoup`, then `_async_init()` awaits `html_renderer.load(width, height)` (boots headless Chrome) and `context_extractor.load()` (imports `bs4`).
3. **Per-request** (`Webeater.get(url, ...)`): `html_renderer.get_rendered_html(url)` → on failure, the renderer is reloaded and content is `None`; on success, `context_extractor.extract_content(url, html, hints=combined_hints, ...)` produces the result. When `return_dict=True`, the dict is augmented with `fetch_time` (string of total elapsed time including render + extract).
4. **Shutdown** (`Webeater.shutdown()`): only quits the Selenium driver. The extractor has no resources to release in the current implementation.

## Tech stack

- **Language**: Python 3.9+ (tested on 3.12.3).
- **Validation**: pydantic v2 (`pydantic>=2.11.7`).
- **Rendering**: Selenium 4 + headless Chrome (user must have Chrome installed; Selenium Manager resolves the driver automatically — no chromedriver in `requirements.txt`).
- **Parsing**: BeautifulSoup 4 with the stdlib `html.parser`. The default extractor is `WebeaterFastBS` — a hand-rolled clean-tree walker over the `bs4` DOM with no third-party markdown library. The legacy `WebeaterBeautifulSoup` extractor remains available via `WeatConfig.extractor="bs"`.
- **Logging**: `coloredlogs`.
- **Async**: stock `asyncio`; blocking Selenium calls are wrapped with `asyncio.to_thread`.
- **Packaging**: setuptools via `pyproject.toml`; CLI entry points `weat` and `webeater`; hint JSON files included as package data.
- **Tests**: `unittest` (migrated from pytest in commit `bcb9d47`); runner is `run_tests.py`. `pytest`/`pytest-asyncio` remain in optional `[dev]`/`[test]` extras.

## Deployment topology

None. The package is `pip install`'d into the user's environment. There is no server, no daemon, no persistent state beyond the `weat.json` file written next to the user's working directory.

## ADRs

### ADR-001: Selenium-only rendering for v0.1.x

- **Context**: Many target sites are JS-heavy (the README explicitly cites this as a feature). A `requests`-only path would fail on those.
- **Decision**: Always render through headless Chrome via Selenium. No fallback path for static HTML.
- **Rationale**: Simpler implementation; one code path; "works out of the box" goal trumps the perf cost on simple pages.
- **Consequences**: Heavy dependency footprint, slow first call (Chrome boot), requires Chrome installed on the host. A future ADR may add an optional `requests`-based fast path for static pages.

### ADR-002: Combined hints computed at config load, immutable thereafter

- **Context**: Hints can come from five sources (default file, config `hint_files`, direct `hints` block in config, CLI `--hints`, library `extra_hint_files`).
- **Decision**: `WeatConfig.__init__` loads and combines all sources into `combined_hints` once; the engine reads only `combined_hints`. `combined_hints` is `exclude=True` from serialization.
- **Rationale**: Keeps the engine ignorant of hint-loading mechanics and avoids re-loading on every request. See `webeater/hints/README.md` for the rationale in the user docs.
- **Consequences**: Per-call hint overrides are not currently supported in the public API beyond the unused `hints` parameter on `Webeater.get()` (which falls back to `combined_hints`). This is a known minor limitation.

### ADR-003: `unittest` over `pytest` for the test runner

- **Context**: Original tests were written for pytest. Commit `bcb9d47` migrated to `unittest`.
- **Decision**: All test classes inherit `unittest.TestCase`; `run_tests.py` wraps `unittest`. `pytest` remains in optional dev/test extras for those who prefer it.
- **Rationale**: Stdlib-only test execution path — contributors don't need to install anything beyond `requirements.txt` to run tests.
- **Consequences**: No async test fixtures from `pytest-asyncio`; live-Selenium integration tests will need to manage their own event loop.

### ADR-004: metak orchestrator scaffolding (single-repo for now)

- **Context**: `metak install` was run on 2026-05-07 (commit `2143673`), creating `metak-shared/`, `metak-orchestrator/`, `AGENTS.md`, and per-tool agent rule files (`.clinerules`, `.windsurfrules`, `GEMINI.md`, etc.).
- **Decision**: Adopt the metak structure even though webeater is currently a single-package single-repo project. The "service map" above lives inside one Python package, not across repos.
- **Rationale**: Establishes orchestrator-led planning and contract gates before the codebase grows. Keeps room for future split (e.g., separate renderer service) without a re-org.
- **Consequences**: `metak-shared/api-contracts/` documents *intra-package* abstract interfaces and user-facing schemas, not cross-repo wire formats. If a sub-repo is later spun out, the contracts move with it.

### ADR-005: Default extractor switched to `WebeaterFastBS`

- **Context**: T3 introduced the `WeatConfig.extractor` field with values `"bs"` and `"fastbs"`. `WebeaterFastBS` is a hand-rolled clean-tree walker that emits real GitHub-Flavoured Markdown tables and runs faster than the legacy walker on the standard fixture.
- **Decision**: Default `WeatConfig.extractor` to `"fastbs"`. The engine selects the extractor at construction time. The default is omitted from saved `weat.json` files. Legacy `WebeaterBeautifulSoup` remains available via `extractor="bs"`.
- **Rationale**: Better default output quality and speed without sacrificing the documented opt-in path for users that depend on the legacy extractor's exact output. See `metak-orchestrator/DECISIONS.md` D5 for full history.
- **Consequences**: Switching extractors requires constructing a new `Webeater`; per-call extractor swaps are not supported.
