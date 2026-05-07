"""
Bench harness comparing ``WebeaterBeautifulSoup`` and ``WebeaterFastBS``.

Standalone script — NOT a unittest test. Run it manually:

    python tests/bench_extractors.py

Loads ``tests/data/fixtures/sample_article.html``, warms each extractor
with 5 calls, then times ``N`` calls each via ``time.perf_counter()`` and
prints average wall-clock per call plus the FastBS / legacy speedup ratio.
"""

import asyncio
import os
import sys
import time

# Ensure the project root is importable when this script is invoked directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from webeater.config import HintsConfig, MainContentHints, RemoveHints  # noqa: E402
from webeater.thirdparty.beautifulsoup import WebeaterBeautifulSoup  # noqa: E402
from webeater.thirdparty.fastbs import WebeaterFastBS  # noqa: E402

FIXTURE_URL = "https://example.com/articles/sample"
FIXTURE_PATH = os.path.join(
    os.path.dirname(__file__), "data", "fixtures", "sample_article.html"
)
N = 100
WARMUP = 5


def _build_hints() -> HintsConfig:
    return HintsConfig(
        remove=RemoveHints(tags=["script"]),
        main=MainContentHints(selectors=["article"]),
    )


async def _bench_one(extractor, html: str, hints: HintsConfig, n: int) -> float:
    """Run ``extractor.extract_content`` ``n`` times. Returns total seconds."""
    t0 = time.perf_counter()
    for _ in range(n):
        await extractor.extract_content(
            FIXTURE_URL,
            html,
            include_images=True,
            include_links=True,
            hints=hints,
            return_dict=True,
        )
    return time.perf_counter() - t0


async def _run() -> None:
    with open(FIXTURE_PATH, "r", encoding="utf-8") as fh:
        html = fh.read()
    hints = _build_hints()

    legacy = WebeaterBeautifulSoup()
    await legacy.load()
    fast = WebeaterFastBS()
    await fast.load()

    # Warmup.
    await _bench_one(legacy, html, hints, WARMUP)
    await _bench_one(fast, html, hints, WARMUP)

    legacy_secs = await _bench_one(legacy, html, hints, N)
    fast_secs = await _bench_one(fast, html, hints, N)

    legacy_ms = (legacy_secs / N) * 1000.0
    fast_ms = (fast_secs / N) * 1000.0

    print(f"Fixture: {FIXTURE_PATH}")
    print(f"Iterations: {N} (warmup {WARMUP})")
    print(f"WebeaterBeautifulSoup: avg {legacy_ms:.3f} ms / call")
    print(f"WebeaterFastBS:        avg {fast_ms:.3f} ms / call")
    if fast_ms > 0:
        ratio = legacy_ms / fast_ms
        print(f"Speedup (legacy / fast): {ratio:.2f}x")
    else:
        print("Speedup: N/A (fast_ms is zero)")


if __name__ == "__main__":
    asyncio.run(_run())
