# Project Custom Instructions

These rules apply to ALL agents (orchestrator + workers) operating in the webeater repository.

## Tech stack

- **Language:** Python 3.9+ (tested on 3.12.3). Do not use syntax that breaks 3.9 compatibility (no `match`, careful with `|` type-union outside `from __future__ import annotations`).
- **Validation:** pydantic v2.
- **Rendering:** Selenium 4 + headless Chrome. Caller must have Chrome installed; Selenium Manager resolves the driver.
- **Parsing:** BeautifulSoup 4 with stdlib `html.parser`.
- **Markdown conversion (FastBS only):** `html2text`. Decision rationale in `metak-orchestrator/DECISIONS.md` (D2).
- **Async:** stock `asyncio`. Wrap blocking Selenium calls with `asyncio.to_thread`.
- **Logging:** `coloredlogs` via `webeater.log.getLog("name")`. Honour the `setLogDebug` / `setLogSilent` toggles.

## Conventions

- Conventional Commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`. Scope optional.
- No emojis in code, commit messages, or documentation. Use `[OK]`, `[FAIL]`, `[WARN]` if status indicators are needed.
- Black formatting (line length 88). Run `black .` before committing if you've reformatted anything.
- Public symbols are re-exported via `webeater/__init__.py`. Don't broaden `__all__` casually — every entry there is a public-API contract.

## Tests

- Framework: `unittest` (not pytest). Tests are discovered by `python run_tests.py` and `python -m unittest discover tests`. Do not introduce pytest-only fixtures or markers — `pytest` is in optional `[dev]` extras only.
- Tests must use temp dirs (`tempfile.mkdtemp` + `shutil.rmtree` in `tearDown`) for any filesystem work. Never read or write the real `weat.json` at repo root from a test.
- Tests must NOT hit the live network. Use static HTML fixtures under `tests/data/` for extractor work.
- Selenium tests must be marked or guarded so they don't run by default — booting Chrome is too heavy for unit-test cycles.
- Every new component must have tests that exercise its public methods. "Compiles clean" is not validation.

## Integration with metak

- Workers: read `AGENTS.md` and `CUSTOM.md` at the repo root and any in your target subfolder. Read the relevant `metak-shared/api-contracts/*.md` before changing a contracted interface.
- Workers: when done, append a completion report to `metak-orchestrator/STATUS.md` covering: what was implemented, which tests were run and their results, deviations from the task spec, and open concerns.
- Workers: write completion reports even when the task is partially blocked. Mark the blocker explicitly so the orchestrator can act.
- Workers: commit small. One logical change per commit. Do not bundle T1's signature fix with T2's new extractor.
- Workers: never skip pre-commit hooks (no `--no-verify`).
- Workers: do NOT touch `metak-shared/` — propose changes via the orchestrator. Exception: `metak-shared/LEARNED.md` may be appended to with discoveries.

## Project-specific rules

- The hint system is a public-facing feature. Don't change hint loading / layering / de-duplication semantics without an api-contract update first.
- The `weat.json` auto-rewrite on every `WeatConfig(...)` construction is **intentional for now** (see `metak-shared/api-contracts/public-api.md` "Known deviations"). Do not "fix" it in a passing change.
- The CLI's `weat` and `webeater` console scripts are both first-class entrypoints. Don't drop one without an explicit task.
- The `>>>` / `<<<` marker scheme in `webeater/thirdparty/beautifulsoup.py:_extract_structured_text` is known-fragile. Do not extend it; if you need richer markdown, build it on top of `html2text` in the FastBS path instead.

## When stuck

- Re-read `metak-shared/api-contracts/` for the contract you're working against.
- Check `metak-shared/LEARNED.md` for known pitfalls.
- Verify assumptions against the running code, not memory or documentation.
- If still blocked, append to `metak-orchestrator/STATUS.md` with what you tried and what failed, and stop. Do not invent a workaround that violates a contract.
