# Task Board

## Current Sprint

### T1 — Fix ABC signature deviations and lifecycle nits (Epic E2 enabler)

**Target repo:** `webeater/` (single-repo project)
**Status:** Pending

Bring the abstract base classes in `webeater/extracting.py` and `webeater/rendering.py` in line with the contracts in `metak-shared/api-contracts/`, and fix two small lifecycle bugs that block reliable shutdown. This must land *before* T2 so the FastBS worker has a correct base class to extend.

**Required changes:**

1. `webeater/extracting.py`:
   - `ContentExtractor.load` currently has signature `async def load():` (missing `self`). Fix to `async def load(self):` and keep the `NotImplementedError`.
   - `ContentExtractor.extract_content` currently has signature `async def extract_content(self, html: str) -> str`. Replace with the real signature used by `Webeater.get`:
     ```python
     async def extract_content(
         self,
         url: str,
         html: str,
         include_images: bool = True,
         include_links: bool = True,
         hints: HintsConfig = None,
         return_dict: bool = True,
     ) -> str | dict: ...
     ```
   - Import `HintsConfig` from `webeater.config`. Use `from __future__ import annotations` if needed to avoid runtime cycle issues, or use a string forward-reference.
2. `webeater/thirdparty/selenium.py`:
   - `SeleniumRuntime.shutdown()` currently calls `self.Driver.quit()` unconditionally; guard with `if self.Driver:` and set `self.Driver = None` afterwards.
3. `webeater/eater.py`:
   - `Webeater.shutdown()` already gates on `self.html_renderer` truthiness; verify it remains correct after #2 and add a defensive `if hasattr(self, "html_renderer") and self.html_renderer:` if the worker judges it necessary.

**Acceptance criteria:**

- `python run_tests.py` passes locally with all existing tests green.
- No behavioural change observable from the public API (`Webeater.create / get / shutdown`, CLI flags).
- A new test (in `tests/test_lifecycle.py`) exercises `await SeleniumRuntime().shutdown()` *without* a prior `load()` and confirms it does not raise. Selenium itself does not need to start — the test just instantiates the class.
- Worker commits with message `fix: align ContentExtractor ABC signature and harden shutdown lifecycle` (or similar Conventional Commits form).

**Notes for the worker:**
- Read `metak-shared/api-contracts/content-extractor.md` and `metak-shared/api-contracts/html-renderer.md` first.
- Do **not** change the auto-save behaviour of `WeatConfig.__init__` — that's documented as a known deviation and the user has not authorized that change.
- Do **not** touch `webeater/thirdparty/beautifulsoup.py` other than to update the abstract method signature it inherits from. Behaviour must not change.
- Run the full test suite, not just one file.

---

### T2 — Implement `WebeaterFastBS` extractor with html2text (Epic E2)

**Target repo:** `webeater/`
**Depends on:** T1
**Status:** Pending

Add a new ContentExtractor implementation, `WebeaterFastBS`, in `webeater/thirdparty/fastbs.py`. It must be a drop-in replacement for `WebeaterBeautifulSoup` — the engine will eventually pick between the two via a config field.

**Implementation plan:**

1. Start with a copy of `webeater/thirdparty/beautifulsoup.py`.
2. Keep all hint-driven trimming logic verbatim:
   - `remove.tags` → `element.decompose()` for each matching tag.
   - `remove.classes` → token-membership match against `class` attribute.
   - `remove.ids` → exact-match against `id` attribute.
   - `main.selectors` → first selector with at least one match wins; pick the largest-by-text-length match.
   - Fallback to `<body>` then to the document root.
3. Replace `_extract_structured_text` and the `>>> / <<<` marker hack with `html2text.HTML2Text`:
   ```python
   import html2text
   converter = html2text.HTML2Text()
   converter.body_width = 0          # don't wrap lines
   converter.ignore_links = not include_links     # we re-attach our own list
   converter.ignore_images = not include_images   # we re-attach our own list
   converter.skip_internal_links = True
   markdown = converter.handle(str(main_content))
   ```
   (Tune the flags as needed — the goal is clean Markdown without html2text's own image/link sections, since we still emit our own `## Images` / `## Links` blocks.)
4. Keep `_extract_images` and `_extract_links` (or their equivalents) so the JSON-mode output and string-mode `## Images` / `## Links` sections still match the existing contract. Copy them over; don't reinvent.
5. Keep title extraction (`<title>` text). Keep the `# {title}` heading prefix in string mode and the `title` key in dict mode.
6. Keep the failure-mode strings: `"Failed to extract content: {error}"` on exception, `"No content found"` on empty body in string mode.
7. Run `cleanup_whitespace` on the final Markdown so trailing/leading blank lines stay sane.

**Dependency:**
- Add `html2text>=2024.2.26` (pick the latest stable on PyPI at time of work) to `pyproject.toml` `dependencies` and `requirements.txt`.

**Tests (must be added):**

- `tests/data/fixtures/sample_article.html` — a small static HTML fixture (article with title, paragraphs, headers, list, table, two images, three links, a `<nav>`, a `<footer>`, and a `<script>`). Worker writes this fixture by hand. ~50–150 lines of HTML.
- `tests/test_fastbs.py` covering:
  - `extract_content(return_dict=True)` returns a dict with required keys (`title`, `content`, `images`, `links`).
  - With a `HintsConfig` that strips `nav`, `footer`, `script`: those tags' text does NOT appear in `content`.
  - `main.selectors=["article"]` correctly picks the article element.
  - Image and link URL normalisation matches the contract (relative → absolute, `mailto:` skipped, `#` skipped).
  - Empty HTML → `"No content found"` in string mode (or empty content in dict mode per `json-output.md`).
  - **Comparison test**: drive both `WebeaterBeautifulSoup` and `WebeaterFastBS` on the same fixture with the same hints, assert that:
    - Both produce a non-empty `content`.
    - The set of image URLs is identical.
    - The set of link URLs is identical.
    - Both titles match.
- `tests/test_suite.py` updated to register `TestWebeaterFastBS`.

**Validation harness (must be added):**

- `tests/bench_extractors.py` — a small standalone script (NOT a unittest test) that loads the same fixture, runs both extractors N=100 times, and prints wall-clock per call for both. This is used to demonstrate the speedup and is not run by CI. Worker should run it once and paste the output into the completion report.

**Acceptance criteria:**

- All existing tests pass.
- New tests pass.
- `WebeaterFastBS` conforms to `metak-shared/api-contracts/content-extractor.md` (worker must verify by reading the contract and ticking off each guarantee).
- `bench_extractors.py` shows FastBS is at least 2× faster than the current implementation on the fixture, OR the worker produces a written explanation of why the speedup is smaller. (No regression below current speed is acceptable.)
- The default extractor is **NOT** changed in this task — `Webeater.__init__` still uses `WebeaterBeautifulSoup`. T3 handles the switch.
- Worker commits as one logical commit: `feat: add WebeaterFastBS extractor backed by html2text` plus a separate test commit if preferred.

**Notes for the worker:**
- Read `metak-shared/api-contracts/content-extractor.md`, `metak-shared/api-contracts/json-output.md`, and `metak-shared/api-contracts/hints-schema.md` before writing code.
- Vasco's draft in `metak-shared/beautifulsoup.suggestions.py` shows the html2text idea but **omits** title/images/links. Don't omit those — Vasco's draft is incomplete.
- Do not delete `metak-shared/beautifulsoup.suggestions.py`; it is a reference doc, not application code.
- Add `html2text` as a runtime dependency. Update both `pyproject.toml` and `requirements.txt`. Pin the version conservatively.

---

### T2b — Replace `html2text` with `markdownify` in `WebeaterFastBS` (Epic E2, perf recovery)

**Target repo:** `webeater/`
**Depends on:** T2
**Status:** Pending
**Driver:** D4. The T2 benchmark showed FastBS at 0.76× legacy throughput because of the double-parse penalty (see `metak-shared/LEARNED.md` L1). T2b switches to `markdownify` to walk the existing bs4 tree directly.

**Required changes:**

1. `webeater/thirdparty/fastbs.py`:
   - Remove the `html2text` import and the `HTML2Text()` block.
   - Use `markdownify` instead. **First** investigate which `markdownify` entrypoint can consume a pre-parsed `bs4` Tag/BeautifulSoup. Inspect the installed version (e.g. `python -c "import markdownify; help(markdownify.MarkdownConverter)"`). The class `MarkdownConverter` typically exposes a `convert_soup(soup)` method (or equivalent) that walks bs4 nodes; if that exists, use it. If only `markdownify(html_string)` is available in the installed version, fall back to that and measure — but flag the fallback in your report.
   - Configure the converter to: not wrap lines (`bullets="-"`, `wrap=False` or equivalent), strip links and images (we re-attach our own), preserve heading levels, keep table structure if cheap. Read `markdownify`'s docs/source for the exact options. If a behaviour cannot be configured, document the divergence.
   - Pipe the result through `cleanup_whitespace`.
2. `pyproject.toml` and `requirements.txt`:
   - Remove `html2text`.
   - Add `markdownify` (pin to a current stable, e.g. `markdownify>=0.13`).
3. `tests/bench_extractors.py`:
   - No code changes required. Re-run after the swap.

**Acceptance criteria:**

- All existing tests still pass (`python run_tests.py`).
- The output of `WebeaterFastBS` on the fixture continues to satisfy `test_compare_with_legacy_bs` (titles match, image set matches, link set matches, content non-empty). If `markdownify`'s emission produces a structurally different markdown body that is nonetheless equivalent in extracted information, that is acceptable — the comparison test only asserts on title/images/links/non-empty, not on the body string. Confirm.
- `python tests/bench_extractors.py` shows FastBS at **≥ 1.0×** the legacy throughput. The orchestrator will use this number to decide T3's scope.
- Two commits suggested:
  - `refactor: swap html2text for markdownify in WebeaterFastBS`
  - `chore(deps): replace html2text with markdownify`

  (Or one combined commit if it stays small.)

**Notes for the worker:**
- Re-read `metak-shared/api-contracts/content-extractor.md`. The contract is unchanged — only the emission library is.
- Do NOT silently change the failure-mode strings or the dict shape.
- If `markdownify`'s default heading style (`#` vs `===`/`---` setext) differs from `html2text`, that's fine — pick `#`-style (ATX) explicitly to match the legacy walker's heading shape.
- Re-run `python tests/bench_extractors.py` and paste the output verbatim into the completion report.
- If after T2b FastBS is **still** slower than legacy, do NOT try to optimise further inside this task. Stop, report, and the orchestrator will decide whether to attempt a hand-rolled walker (a third epic-level decision) or ship FastBS as opt-in only.

**Completion report:** append `### T2b — completion report (2026-05-07)` to `STATUS.md` with the same format as T2: implemented, contract compliance, test results, benchmark output, deviations, files touched, commit hashes.

---

### T2c — Replace `markdownify` with a hand-rolled clean walker in FastBS (Epic E2, perf recovery #2)

**Target repo:** `webeater/`
**Depends on:** T2b
**Status:** Pending
**Driver:** D5. T2b (markdownify) ran at 0.81× legacy throughput. The library overhead is unavoidable on small docs. The legacy hand-rolled walker is fast — its only real defect is the `>>>`/`<<<` marker scheme it emits and then string-replaces afterwards. T2c writes a clean walker that matches the legacy speed character but emits proper Markdown directly.

**What to do:**

1. In `webeater/thirdparty/fastbs.py`, replace the `MarkdownConverter().convert_soup(main_content)` call with a new module-private function `_walk_to_markdown(element) -> str`. Take `webeater/thirdparty/beautifulsoup.py:_extract_structured_text` as a structural reference, but produce real Markdown directly:
   - **No** `>{res}<` / `>>>` / `<<<` markers anywhere.
   - **No** post-hoc `text.replace(">>><<<", ...)` chain.
   - Use explicit `\n\n` separators between block-level pieces.
   - Headings: `'#' * level + ' ' + text + '\n\n'` for `h1`–`h6`. Map `<header>` to level 1 (or 2 — pick one and document; the legacy used level 0 which produced ` ` as the prefix, which is broken).
   - Paragraphs: `text + '\n\n'`.
   - Unordered lists: each item on its own line as `'- ' + item_text`. Then `'\n'` after the list.
   - Ordered lists: each item as `'1. ' + item_text` (Markdown auto-numbers `1.` items, so this is fine and matches the legacy behaviour).
   - Tables: emit a real GitHub-Flavoured Markdown table (`| cell | cell |\n| --- | --- |\n| ... |`). The legacy emitted `T|...|` which is not Markdown. This is an enhancement; the comparison test does NOT assert on body content, so it is safe.
   - Other inline / unknown elements: recurse into children, accumulate text, deduplicate within the same parent only when the legacy did (preserve the de-dup behaviour for repeated content blocks).
   - The function returns a single string. Run it through `cleanup_whitespace` at the call site.
2. Drop the `markdownify` runtime dependency:
   - Remove the `markdownify>=...` line from `pyproject.toml` and `requirements.txt`.
   - Remove the `markdownify` import from `fastbs.py`.
3. Keep everything else identical: hint application, title extraction, `_extract_images`, `_extract_links`, dict assembly, failure strings, logger.
4. Run the suite. All 98 tests must still pass — particularly `test_compare_with_legacy_bs`, which only checks title/images/links/non-empty body, so structural body-string differences are fine.
5. Run `python tests/bench_extractors.py`. Capture verbatim.

**Acceptance criteria:**

- All existing tests pass.
- Bench shows FastBS at **≥ 1.0×** the legacy throughput on the standard fixture. If between 0.95× and 1.0×, that is acceptable as long as FastBS is faster than T2b's 0.81× — note explicitly in the report. The orchestrator will use the number to gate T3.
- No `markdownify` import anywhere in `webeater/`.
- `tests/bench_extractors.py` still works without modification.

**Constraints:**

- Do NOT touch `webeater/thirdparty/beautifulsoup.py` (legacy must stay intact for the comparison test).
- Do NOT change the default extractor (T3's job).
- Do NOT widen the comparison test to assert on body content.
- Python 3.9+. Black-formatted. No emojis. Conventional Commits. No `--no-verify`.

**Workflow:**

1. Read `metak-orchestrator/DECISIONS.md` D2-retro / D4-retro / D5, `metak-shared/LEARNED.md` L1/L2, `metak-shared/api-contracts/content-extractor.md`, the current `webeater/thirdparty/fastbs.py`, and `webeater/thirdparty/beautifulsoup.py:_extract_structured_text` (as reference).
2. Replace the body emission in `fastbs.py`. Drop `markdownify`.
3. Run tests until green.
4. Run bench, capture output.
5. Commit: `refactor: hand-roll clean tree walker in WebeaterFastBS, drop markdownify`.
6. Append `### T2c — completion report (2026-05-07)` to `STATUS.md` with: implemented, test results, bench output verbatim, new ratio, gate result (PASS / FAIL), deviations, files touched, commit hashes.

If T2c also fails the gate, stop and report. Do NOT attempt a third optimisation pass — the orchestrator will accept the result and re-scope T3.

---

### T3 — Make extractor selectable via config; switch default to FastBS (Epic E2)

**Target repo:** `webeater/`
**Depends on:** T2c
**Status:** Pending — *the default switch is conditional on T2c achieving ≥ 1.0× legacy throughput. If T2c still underperforms, T3 will be re-scoped to keep `bs` as the default and ship FastBS as opt-in.*

After T2 lands and is validated, expose the choice and flip the default.

**Required changes:**

1. `webeater/config.py` (`WeatConfig`):
   - Add a field `extractor: Literal["bs", "fastbs"] = "fastbs"`.
   - Persist it in `save()` only when non-default (mirror the `debug` exclusion pattern), to avoid noise in user `weat.json` files.
2. `webeater/eater.py` (`Webeater.__init__`):
   - Branch on `self.config.extractor`:
     - `"bs"` → `WebeaterBeautifulSoup()`
     - `"fastbs"` → `WebeaterFastBS()`
3. `weat.json` at repo root: leave unchanged. The default (`"fastbs"`) takes effect even when the field is absent.
4. `README.md`:
   - Add a short subsection under "Configuration and Advanced documentation" naming both extractors and how to choose one.
   - Mention that FastBS is the default and `bs` is the legacy path.
5. `metak-shared/api-contracts/public-api.md` and `metak-shared/architecture.md`:
   - Update to reflect the new `extractor` field.
   - Worker updates these only if they remain accurate after the change. If they need broader edits, flag for orchestrator follow-up rather than rewriting.

**Acceptance criteria:**

- All tests pass.
- A new test verifies that `WeatConfig(extractor="bs")` causes `Webeater` to instantiate `WebeaterBeautifulSoup`, and `extractor="fastbs"` (or default) causes it to instantiate `WebeaterFastBS`.
- A pydantic validation test asserts that `extractor="garbage"` raises `ValidationError`.
- The default `weat.json` produced by a fresh `WeatConfig()` does **not** contain `"extractor": "fastbs"` (because it's the default).
- Worker commit: `feat: select extractor via config and default to fastbs`.

**Notes for the worker:**
- After this task, run the CLI manually against `https://example.com` (or skip if no network) and confirm the output looks reasonable. If skipping, mark the task as "pending live validation" in the completion report.
- Do not touch the renderer. E3 is a separate epic.

---

## Backlog

- T4 (E3): scroll gating in `SeleniumRuntime.scroll_page()`.
- T5 (E3): HTTP fast path with `httpx.AsyncClient`.
- T6 (E3): concurrency primitive for parallel fetches.
- T7 (E3): tune Selenium waits.
- T8 (E3): evaluate Playwright migration.

These are described in `EPICS.md` and held until the user authorizes E3.
