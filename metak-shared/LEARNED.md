# Learned

Things discovered during development that are useful for future work.

## L1: `html2text` after BeautifulSoup hint application = double-parse penalty

**Discovered:** 2026-05-07, during T2 (`WebeaterFastBS` validation).

**What we found:** `html2text.HTML2Text().handle(str(main_content))` re-parses the HTML inside `html2text` (it uses its own internal `html.parser`-based reader) on top of the BeautifulSoup parse we already did to apply hints. cProfile on a 12 KB inflated fixture shows the bs4 `__init__` + the `str(main_content)` re-serialization + the `html2text.handle` re-parse together cost ~1.13 s / 100 iterations vs ~0.91 s / 100 iterations for the legacy single-parse + hand-rolled walker. Net: a 1.3× **slowdown**, not the speedup we expected. The ratio gets worse on larger HTML (down to ~0.5× at 25 KB).

**Implication:** Any extractor pipeline that pre-processes HTML with BS4 (for hint application or noise removal) and then hands the serialized result to a string-input markdown library pays for two parses. Avoid this pattern. Options that side-step the penalty:

- Walk the BeautifulSoup tree directly with a markdown emitter that consumes bs4 nodes (e.g. `markdownify`'s class-based API exposes per-tag conversion methods that consume bs4 elements).
- Skip bs4 entirely when no hints are active and pass the raw HTML to the markdown library — but this breaks the "always apply hints" contract and is not safe as a general path.
- Hand-roll a clean tree walker on the bs4 tree, learning from the legacy `_extract_structured_text` function but without its `>>>`/`<<<` marker hack.

The general lesson: **measure before adopting a markdown library as a "fast" replacement**. Pure HTML-to-Markdown libraries that take string input will re-parse what you already parsed.

## L2: Even no-double-parse markdown libraries lose to a hand-rolled walker on small fixtures

**Discovered:** 2026-05-07, during T2b (`markdownify` swap).

**What we found:** Switching `WebeaterFastBS` from `html2text` to `markdownify.MarkdownConverter().convert_soup(main_content)` killed the double-parse (the worker confirmed via source inspection that `convert_soup` walks bs4 nodes directly). FastBS went from 0.76× to 0.81× of legacy throughput — better, but still ~1.2× slower than the hand-rolled walker on a ~12 KB fixture. cProfile attributes the residual cost to `markdownify`'s general-purpose machinery: per-tag escape passes, whitespace normalisation, function-table dispatch (`convert_h1`, `convert_h2`, …), and parent-tag tracking. A focused single-pass walker that handles only headings / paragraphs / lists / tables doesn't pay any of that.

**Implication:** When the comparison baseline is a tight hand-rolled walker on small documents, no general-purpose markdown library will be faster — only cleaner. Treat libraries as a *correctness/maintainability* improvement, not a speed one. To beat a hand-rolled walker, write another hand-rolled walker (drop the bugs, keep the cadence). To get *real* extractor-side speedups on big documents, pair the hand-rolled walker with `lxml` (faster bs4 parser) — but that's a separate change with its own behavioural impact.

The compounded lesson from L1+L2: **library swaps for performance need a measured baseline first.** D2 and D4 were both invalidated by post-implementation benchmarks.
