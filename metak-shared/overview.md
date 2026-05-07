# Project Overview

## Goal

WebEater (`weat`) is a small, focused Python tool that fetches a web page, runs JavaScript on it via headless Chrome, and extracts the human-readable content. The output is either Markdown text or a structured JSON dict (title, content, images, links, fetch_time). It is intended as a "go-to component that works out of the box" for developers and researchers who need clean text from arbitrary URLs without writing a custom scraper each time.

## What we're building

A single Python package, `webeater`, that ships:

- **A library API** (`from webeater import Webeater`) with an async factory `Webeater.create()` and a single primary method `get(url, hints=None, return_dict=False, content_only=False)`.
- **A CLI** exposed as both `weat` and `webeater` console scripts. Supports one-shot URL extraction or an interactive REPL, with shortcuts (`j!url`, `c!url`, `jc!url`) for per-request flag overrides.
- **A configurable hints system** — JSON files declaring which tags/classes/ids to strip and which CSS selectors mark the main content area. Hints are layered (default → config-file hints → direct config hints → CLI `--hints` → library `extra_hint_files`) and de-duplicated.
- **A Selenium-based renderer** with aggressive scroll-and-wait to trigger lazy-loading, plus a BeautifulSoup-based extractor that emits Markdown-style structured text.

## Current state

- Published to PyPI as `webeater` v0.1.1 (Development Status :: 3 - Alpha).
- Python 3.9–3.12 supported per `pyproject.toml`; current author tests on 3.12.3.
- Test suite uses `unittest` (recently migrated from pytest, commit `bcb9d47`); covers config loading, hint combination, validation, and exercises the actual project hint files. No live-network or end-to-end Selenium tests yet.
- Hints shipped: `default.json`, `news.json`, `sports.json`. Default config saved to `weat.json` at project root on first run.
- Recently committed: metak orchestrator scaffolding (`metak install`, commit `2143673`). `metak-shared/` docs, `metak-orchestrator/` workspace, and `AGENTS.md`/`CUSTOM.md` files are present but not yet filled in for this project — populating them is the current task.

## What's next

Open directions, in rough priority order — none of these are committed work, just visible gaps:

1. **End-to-end / integration tests** that actually drive Selenium against a known fixture page (currently only config & hints have unit tests).
2. **Pluggable renderers / extractors.** `HtmlRenderer` and `ContentExtractor` are abstract, but only Selenium and BeautifulSoup implementations exist. A lighter `requests`+`bs4` renderer for non-JS pages would speed up the common case.
3. **Documented public contract** for the JSON output shape (title, content, images, links, fetch_time) so library consumers can rely on it — captured in `api-contracts/json-output.md`.
4. **Robustness in the extractor**: the `_extract_structured_text` function currently does string-replacement gymnastics with `>>>`/`<<<` markers; this is fragile and worth replacing with a proper traversal.
5. **CLI polish**: silent-mode error formatting, exit codes, and a non-interactive default when stdin is not a TTY.
