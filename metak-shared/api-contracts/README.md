# API Contracts

This folder documents the stable interfaces that any worker working on webeater must conform to. Two flavours of contract live here:

1. **Internal abstract interfaces** — the seams inside the `webeater` package that define how a renderer or extractor plugs in. Today there is one implementation of each, but the abstraction is real and any new implementation must conform to the contract here.
2. **User-facing schemas and APIs** — anything a library consumer or CLI user depends on (hint JSON shape, JSON-mode output dict, library entrypoints, CLI flags). Changes to these are breaking changes.

## Index

| Contract | What it pins down |
|----------|-------------------|
| [`html-renderer.md`](html-renderer.md) | The `HtmlRenderer` abstract base class — load/get/shutdown lifecycle and the rendered-HTML guarantee. |
| [`content-extractor.md`](content-extractor.md) | The `ContentExtractor` abstract base class — load/extract/shutdown lifecycle and the extraction inputs/outputs. |
| [`hints-schema.md`](hints-schema.md) | The JSON schema for hint files (`remove.tags / remove.classes / remove.ids`, `main.selectors`) and the layering/de-duplication rules. |
| [`json-output.md`](json-output.md) | The dict shape returned when `return_dict=True` (`title`, `content`, `images`, `links`, `fetch_time`). |
| [`public-api.md`](public-api.md) | The library and CLI public surface — `Webeater.create`, `Webeater.get`, `Webeater.shutdown`, the `weat` / `webeater` CLI flags, and interactive-mode shortcuts. |

## Conventions

- Each contract has a **Status** line (Stable / Beta / Experimental) and a **Known deviations** section at the bottom listing any places where the implementation diverges from the contract today. Workers must check this section before assuming the contract holds.
- Workers must not import private symbols across the `HtmlRenderer` / `ContentExtractor` boundary; new implementations must rely solely on what is documented in the contract.
- When changing a contract, update this folder *first* and flag the change to the orchestrator. Code changes that violate a contract without a corresponding contract update will be rejected at review.
