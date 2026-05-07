# Contract: `HtmlRenderer`

**Status:** Stable (v0.1.x)
**Source of truth:** `webeater/rendering.py`
**Sole current implementation:** `webeater.thirdparty.selenium.SeleniumRuntime`

A renderer is responsible for taking a URL and returning fully-rendered HTML — that is, HTML as it would exist in the browser DOM after JavaScript has executed and any reasonable lazy-loading has been triggered.

## Class

```python
class HtmlRenderer(ABC):
    def __init__(self): ...
    async def load(self, window_size_w: int = 1920, window_size_h: int = 1080) -> Any: ...
    async def get_rendered_html(self, url: str, interact: bool = False, driver=None) -> str: ...
    async def shutdown(self) -> None: ...
```

All four methods are required. `__init__` must be cheap — heavy work (driver boot, library import) belongs in `load()`.

## Lifecycle

1. **Construct** the renderer with no arguments. Implementations may capture lightweight handles in `__init__` (e.g. cached references to library types) but **must not** start a browser, open a network socket, or block.
2. **`await load(window_size_w, window_size_h)`** — perform the expensive setup. After this returns successfully, the renderer is "ready". `load()` must be safely idempotent: calling it twice should not start a second backend.
3. **`await get_rendered_html(url, interact=False)`** any number of times. Must be callable concurrently with itself only if the implementation is safe — the Selenium implementation is **not** concurrent-safe (single Chrome driver), so callers must serialize.
4. **`await shutdown()`** — release all resources. After `shutdown()` the renderer must not be used again.

A renderer **may** also expose `reload()` (the Selenium implementation does) so callers can recover from a wedged backend without losing the renderer object.

## Method contracts

### `load(window_size_w, window_size_h)`

- Booting the rendering backend (driver, browser, library imports) happens here.
- The window size hints how the page should be laid out before extraction. Implementations are free to clamp or ignore this.
- Must return the renderer (or an internal driver handle); callers in this codebase do not consume the return value, so `None` is also acceptable.
- On failure, must raise — partial state is not allowed.

### `get_rendered_html(url, interact=False)`

- **Input**: an `http://` or `https://` URL. URL validation is the **caller's** responsibility; renderers are not required to reject invalid schemes (the CLI rejects them upstream).
- **Output**: a `str` containing the page HTML *after* JS has run and after any lazy-load triggering work the implementation performs (scrolling, etc).
- **Exception policy**: on any failure (timeout, navigation error, driver crash) the renderer **must** raise. The caller in `Webeater.get()` catches all exceptions and triggers a `reload()`; therefore implementations should leave the renderer in a recoverable state on failure (or document that `reload()` must be called).
- The `interact=True` flag is reserved for future page-interaction logic (clicking tabs, paginating). Implementations that don't support it must raise `NotImplementedError`.
- The `driver=` keyword is a vestigial parameter on the abstract method and is unused by the in-tree caller; implementations should ignore it.

### `shutdown()`

- Must release all OS-level resources (subprocesses, sockets). Idempotent if called twice — the second call should be a no-op or at worst log a warning.

## Concurrency

A single renderer instance may be assumed single-tenant by implementations. Callers needing parallelism should create multiple renderers.

## Known deviations

- `HtmlRenderer.shutdown()` is declared but raises `NotImplementedError` in the base class even though it is required — implementations must override it. (See `webeater/rendering.py:12`.)
- `SeleniumRuntime.shutdown()` does not check whether `self.Driver` is `None`; calling it before `load()` will raise `AttributeError`. Workers fixing renderer lifecycle bugs should add the guard.
- `SeleniumRuntime.scroll_page()` uses a module-level `WINDOW_SIZE_H` constant (3000) for its scroll math rather than the configured `self.window_size_h`. This is intentional today — the configured height drives the Chrome viewport, the constant drives scroll cadence — but the duplication is a known trap.
- Page-load timeout is hard-coded to 5 seconds (`self.Driver.set_page_load_timeout, 5` in `webeater/thirdparty/selenium.py:190`). Slow sites may fail; this is not yet configurable from `WeatConfig`.
