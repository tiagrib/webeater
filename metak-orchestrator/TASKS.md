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

### T3 — Make extractor selectable via config; switch default to FastBS (Epic E2)

**Target repo:** `webeater/`
**Depends on:** T2
**Status:** Pending

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
