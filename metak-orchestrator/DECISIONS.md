# Decisions Log

## D1: Single-repo for now; metak structure retained

- **Date:** 2026-05-07
- **Context:** The metak orchestrator scaffolding (`metak install`, commit `2143673`) was applied to a single Python package. There is no second sub-repo today.
- **Decision:** Keep the metak structure as-is. Document internal abstract interfaces (`HtmlRenderer`, `ContentExtractor`) and user-facing schemas (hints JSON, JSON output, public API/CLI) under `metak-shared/api-contracts/`, rather than skipping that folder. Treat the project as single-repo until the user explicitly authorizes a split.
- **Rationale:** User confirmed "for now single repo" on 2026-05-07. The contracts have value even within one package — they pin down the extension points (renderer/extractor swap-in) and the user-visible surface.

## D2: `html2text` over `trafilatura` for FastBS markdown conversion (SUPERSEDED by D4)

- **Date:** 2026-05-07
- **Context:** Vasco's suggestion (`metak-shared/beautifulsoup.suggestions.py`) used `html2text`. The orchestrator's earlier "what's next" note had floated `trafilatura`. Both produce Markdown-ish output but operate differently.
- **Decision:** Use `html2text` for the markdown conversion step in `WebeaterFastBS`.
- **Rationale:** `trafilatura` performs its own boilerplate-removal heuristic, which would compete with — and partially override — the user's hint system. The hint system is a documented, advertised feature of webeater. `html2text` is a pure HTML→Markdown converter and respects whatever subset of HTML we feed it after the BS4-based hint trimming. This keeps hints authoritative and isolates the change to "stop hand-rolling the walker."
- **Consequences:** We pick up a new runtime dependency (`html2text`). We do not benefit from `trafilatura`'s article-detection. If the user later wants a "smart article mode," that can be a third extractor (`WebeaterTrafilatura`) without affecting this change.

### D2 retrospective (2026-05-07, post-T2)

D2 assumed `html2text` would be a speedup over the hand-rolled walker. The T2 worker's benchmark falsified this: FastBS came in at **0.76× the legacy throughput** (1.3× slower) on the standard fixture, and worse on larger HTML. Root cause is a double-parse: BS4 parses once to apply hints, `html2text.handle(str(main_content))` re-parses internally. The hint-application requirement makes the pure string-in markdown libraries the wrong tool here. Captured in `metak-shared/LEARNED.md` (L1). The functional-correctness goals of T2 (drop the `>>>`/`<<<` marker hack, faithful contract conformance) were met; only the speed claim was not. D4 supersedes D2 with a path that walks the bs4 tree directly.

## D4: Switch FastBS body emission from `html2text` to `markdownify` to eliminate the double-parse

- **Date:** 2026-05-07 (post-T2)
- **Context:** D2 chose `html2text`. T2's benchmark showed a 1.3× slowdown caused by re-parsing inside `html2text`. We need a markdown emitter that can consume the bs4 tree we already built for hint application.
- **Decision:** Replace `html2text` with `markdownify` in `WebeaterFastBS`. Use whichever `markdownify` API consumes a pre-parsed bs4 tree (its `MarkdownConverter` class exposes per-element conversion that walks bs4 nodes; the worker assigned to T2b verifies the exact entrypoint and reports it). If no such API exists in the installed version, fall back to `markdownify(str(main_content))` and measure — accept it only if the result is at least at parity with the legacy walker.
- **Rationale:** `markdownify` is purpose-built for HTML→Markdown via bs4. Walking the existing tree skips both the `str(main_content)` serialization (~0.196 s / 100 iter on the 12 KB fixture) and the second parse inside the markdown library (~0.347 s / 100 iter). Combined recovery should be enough to bring FastBS to parity with or above the legacy walker.
- **Consequences:** Drop the `html2text` runtime dependency. Add `markdownify`. The contracts and tests written in T2 should pass unchanged because the dict shape, hint application, image/link normalisation, title extraction, and failure strings all live outside the body-emission path.
- **Validation gate:** T3 (default switch) only proceeds if the post-T2b benchmark shows FastBS at ≥ 1.0× the legacy throughput on the fixture. If FastBS still underperforms the legacy walker after T2b, T3 will be re-scoped to make the extractor configurable but keep `bs` as the default.

## D3: Renderer wins deferred until user authorization

- **Date:** 2026-05-07
- **Context:** During E2 planning, several renderer-level wins surfaced (scroll gating, HTTP fast path, concurrency, Playwright). User asked for an "enhanced extractor" specifically.
- **Decision:** Limit this run to `metak-shared/` docs + extractor work (E2). Document the renderer wins as Epic E3 in `EPICS.md` and tasks T4–T8 in the backlog of `TASKS.md`. Do not spawn workers for them.
- **Rationale:** User explicitly scoped this run to "the enhanced extractor, tested, validated compared to an existing one, and then set as default." Renderer changes are larger and warrant a fresh authorization. Better to deliver a tight extractor change that's well-tested than to overshoot.
