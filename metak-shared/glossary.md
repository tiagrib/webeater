# Glossary

Domain terminology for WebEater. Use these terms consistently across docs, code, and commits.

| Term | Definition |
|------|-----------|
| **WebEater** / **weat** | The project as a whole. `weat` is also the name of the CLI binary. |
| **Engine** | A live `Webeater` instance — a configured renderer + extractor pair, ready to serve `get(url)` calls. Built via the async factory `Webeater.create(config=...)`. |
| **Renderer** | The component that turns a URL into rendered HTML. Implements `HtmlRenderer`. The current implementation is `SeleniumRuntime` (headless Chrome). |
| **Extractor** | The component that turns rendered HTML into Markdown text or a JSON dict. Implements `ContentExtractor`. The current implementation is `WebeaterBeautifulSoup`. |
| **Hint** | A user-supplied directive that biases extraction. Two kinds: a **remove** hint (drop matching tags / classes / ids before extracting) and a **main** hint (CSS selectors that locate the main content area). |
| **Hint file** | A JSON file in `webeater/hints/` (or a user-supplied path) following the schema in `api-contracts/hints-schema.md`. Identified by stem name, e.g. `default`, `news`, `sports`. |
| **Combined hints** | The result of layering all hint sources (default file → config `hint_files` → direct config `hints` → CLI `--hints` → library `extra_hint_files`) and de-duplicating while preserving order. Stored on `WeatConfig.combined_hints`. |
| **Direct hints** | A `hints` block embedded inline in `weat.json`, as opposed to referencing an external hint file. |
| **Main content** | The largest DOM subtree matching one of the `main.selectors` from the active hints. The extractor falls back to `<body>` if no selector matches. |
| **Content-only mode** | An extraction mode (`content_only=True` / CLI `--content-only`) that suppresses the `images` and `links` sections of the output. |
| **JSON mode** | An extraction mode (`return_dict=True` / CLI `--json`) that returns a dict (`title`, `content`, `images`, `links`, `fetch_time`) instead of a Markdown string. |
| **Interactive mode** | The CLI REPL entered when no URL is passed on the command line. Supports per-line shortcuts `j!url`, `c!url`, `jc!url` / `cj!url`, and `q` to quit. |
| **Fetch time** | Total elapsed wall time from the start of `Webeater.get(url)` to the end of extraction, returned as a stringified `timedelta` under the `fetch_time` key in JSON mode. |
| **Hints directory** (`HINTS_DIR`) | The path resolved at import time as `<webeater package>/hints/`. Used as the default search root for hint files referenced by stem name. |
| **Orchestrator** | The Claude Code agent role that plans work, writes shared docs and API contracts, configures workers via `CUSTOM.md`, and spawns workers — but never writes application code. See `metak-orchestrator/AGENTS.md`. |
| **Worker** | A Claude Code agent scoped to a single sub-folder. Reads its assignment from the orchestrator, writes code, runs tests, posts a completion report to `metak-orchestrator/STATUS.md`. |
| **Hint source priority** | The fixed order in which hint sources are merged (default → config-file → direct config → CLI `--hints` → library `extra_hint_files`). Later sources extend earlier ones; duplicates are removed but order is preserved. |
