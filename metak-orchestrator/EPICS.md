# Epics

## E1: metak documentation and contracts (DONE)

Populate `metak-shared/` with overview, architecture, glossary, and the five api-contract files (HtmlRenderer, ContentExtractor, hints schema, JSON output, public API). First-pass — completed 2026-05-07.

## E2: Extractor performance — `WebeaterFastBS`

**Goal:** Add a faster, cleaner ContentExtractor (`WebeaterFastBS`) without removing the existing `WebeaterBeautifulSoup`. Validate side-by-side against the existing extractor and switch the default once validated.

**Why:** The current extractor walks the DOM by hand using a fragile `>>>` / `<<<` marker scheme that the orchestrator already flagged in `metak-shared/api-contracts/content-extractor.md`. Vasco's suggestion (in `metak-shared/beautifulsoup.suggestions.py`) points to `html2text` for the HTML→Markdown step. Combined with hint-driven trimming in BS4, this should be both faster and more correct.

**Scope:**
- Keep `WebeaterBeautifulSoup` as-is. Do not delete or refactor it.
- New `webeater/thirdparty/fastbs.py` with `WebeaterFastBS(ContentExtractor)`.
- Reuse the hint-application logic (remove + main selector) verbatim.
- Replace `_extract_structured_text` with `html2text.HTML2Text` rendering of the chosen main element.
- Preserve the full ContentExtractor contract: title, content, images, links, dict mode, fetch_time, "No content found" / failure strings.
- Add a config-level extractor selector (`extractor: "bs" | "fastbs"`).
- Add tests that drive both extractors on the same fixture HTML and assert the new one's output is a strict superset (no regressions in title/images/links) and that markdown produced is non-empty and well-formed.

**Out of scope:** anything in `selenium.py` or `rendering.py`. See E3.

## E3: Renderer performance — fast paths and concurrency (DEFERRED, awaits user authorization)

Wins identified during E2 planning, not yet authorized for execution:

- **Scroll gating** — make `SeleniumRuntime.scroll_page()` opt-in (config flag) or auto-skip when the page shows no lazy-loading signals. Drops ~3.5 s/page floor.
- **HTTP fast path** — try `httpx.AsyncClient.get()` first, escalate to Selenium only when the response looks JS-rendered (empty/short body, SPA markers).
- **Concurrent fetches** — `asyncio.Semaphore(N)`-bounded parallel `get()` calls; one driver per worker.
- **Wait tuning** — drop the redundant 2 s implicit wait, keep only the explicit `WebDriverWait`.
- **Selenium → Playwright (large lift)** — async-native, CDP-direct.

Documented but not actioned this run. The user requested I focus on the extractor first and return for renderer authorization later.
