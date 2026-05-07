# Decisions Log

## D1: Single-repo for now; metak structure retained

- **Date:** 2026-05-07
- **Context:** The metak orchestrator scaffolding (`metak install`, commit `2143673`) was applied to a single Python package. There is no second sub-repo today.
- **Decision:** Keep the metak structure as-is. Document internal abstract interfaces (`HtmlRenderer`, `ContentExtractor`) and user-facing schemas (hints JSON, JSON output, public API/CLI) under `metak-shared/api-contracts/`, rather than skipping that folder. Treat the project as single-repo until the user explicitly authorizes a split.
- **Rationale:** User confirmed "for now single repo" on 2026-05-07. The contracts have value even within one package — they pin down the extension points (renderer/extractor swap-in) and the user-visible surface.

## D2: `html2text` over `trafilatura` for FastBS markdown conversion

- **Date:** 2026-05-07
- **Context:** Vasco's suggestion (`metak-shared/beautifulsoup.suggestions.py`) used `html2text`. The orchestrator's earlier "what's next" note had floated `trafilatura`. Both produce Markdown-ish output but operate differently.
- **Decision:** Use `html2text` for the markdown conversion step in `WebeaterFastBS`.
- **Rationale:** `trafilatura` performs its own boilerplate-removal heuristic, which would compete with — and partially override — the user's hint system. The hint system is a documented, advertised feature of webeater. `html2text` is a pure HTML→Markdown converter and respects whatever subset of HTML we feed it after the BS4-based hint trimming. This keeps hints authoritative and isolates the change to "stop hand-rolling the walker."
- **Consequences:** We pick up a new runtime dependency (`html2text`). We do not benefit from `trafilatura`'s article-detection. If the user later wants a "smart article mode," that can be a third extractor (`WebeaterTrafilatura`) without affecting this change.

## D3: Renderer wins deferred until user authorization

- **Date:** 2026-05-07
- **Context:** During E2 planning, several renderer-level wins surfaced (scroll gating, HTTP fast path, concurrency, Playwright). User asked for an "enhanced extractor" specifically.
- **Decision:** Limit this run to `metak-shared/` docs + extractor work (E2). Document the renderer wins as Epic E3 in `EPICS.md` and tasks T4–T8 in the backlog of `TASKS.md`. Do not spawn workers for them.
- **Rationale:** User explicitly scoped this run to "the enhanced extractor, tested, validated compared to an existing one, and then set as default." Renderer changes are larger and warrant a fresh authorization. Better to deliver a tight extractor change that's well-tested than to overshoot.
