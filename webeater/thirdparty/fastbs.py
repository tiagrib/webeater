"""
WebeaterFastBS - a ``ContentExtractor`` implementation that mirrors
``WebeaterBeautifulSoup`` for hint application, title/image/link extraction
and output assembly, but replaces the fragile hand-rolled
``_extract_structured_text`` walker (with its ``>>>`` / ``<<<`` marker scheme
and post-hoc string replacements) with a clean single-pass tree walker that
emits proper Markdown directly.

The walker (`_walk_to_markdown`) keeps the speed character of the legacy
hand-rolled walker - no general-purpose markdown library, no double-parse -
while emitting Markdown without any intermediate marker strings.

Contract: see ``metak-shared/api-contracts/content-extractor.md``.
"""

from webeater.util import cleanup_whitespace
from webeater.extracting import ContentExtractor
from webeater.log import getLog
from webeater.config import HintsConfig


class WebeaterFastBS(ContentExtractor):
    """Fast BeautifulSoup content extractor with a hand-rolled clean walker.

    Drop-in equivalent of ``WebeaterBeautifulSoup`` for the contracted fields
    (title, images, links, dict shape). The body Markdown is produced by
    ``_walk_to_markdown`` walking the bs4 tree directly and emitting clean
    Markdown without the legacy ``>>>`` / ``<<<`` marker hack.
    """

    def __init__(self, hint_names: list = None, combined_hints: HintsConfig = None):
        super().__init__()
        self.log = getLog("weat-fastbs")

    async def load(self):
        from bs4 import BeautifulSoup  # type: ignore

        self._BSCLASS = BeautifulSoup

    async def extract_content(
        self,
        url: str,
        html: str,
        include_images: bool = True,
        include_links: bool = True,
        hints: HintsConfig = None,
        return_dict: bool = True,
    ):
        """Extract content from ``html`` using hints and emit Markdown / dict.

        See ``metak-shared/api-contracts/content-extractor.md`` for the full
        contract. Mirrors ``WebeaterBeautifulSoup.extract_content`` byte-for-byte
        in everything except the body-text generation step, which uses
        ``_walk_to_markdown`` instead of ``_extract_structured_text`` + the
        legacy marker-strip ``replace`` chain.
        """
        try:
            soup = self._BSCLASS(html, "html.parser")

            if hints and hints.remove:
                # Remove by tag
                if hints.remove.tags:
                    for tag in hints.remove.tags:
                        for element in soup.find_all(tag):
                            self.log.debug(f"Removing element with tag: {tag}")
                            element.decompose()

                # Remove by exact class name (token-membership match)
                if hints.remove.classes:
                    for class_name in hints.remove.classes:
                        for element in soup.find_all(
                            lambda tag: tag.has_attr("class")
                            and class_name in tag.get("class", [])
                        ):
                            try:
                                element_str = str(element)
                            except Exception:
                                element_str = ""
                            self.log.debug(f"Removing element with class: {class_name}")
                            element.decompose()

                # Remove by exact id
                if hints.remove.ids:
                    for id_name in hints.remove.ids:
                        for element in soup.find_all(
                            lambda tag: tag.has_attr("id")
                            and tag.get("id", "") == id_name
                        ):
                            self.log.debug(f"Removing element with id: {id_name}")
                            element.decompose()

            # Try to find main content areas using hint selectors.
            main_content = None
            if hints and hints.main and hints.main.selectors:
                for selector in hints.main.selectors:
                    try:
                        found = soup.select(selector)
                        if found:
                            # Use the largest content area (by text length).
                            main_content = max(found, key=lambda x: len(x.get_text()))
                            self.log.debug(
                                f"Found main content with hint selector: {selector}"
                            )
                            break
                    except Exception:
                        continue

            # Fall back to <body> then to the document root.
            if not main_content:
                main_content = soup.find("body") or soup
                self.log.info("Using full body content")

            text_content = []

            # Title (always extracted from the original soup).
            title = (
                soup.find("title").get_text().strip() if soup.find("title") else None
            )
            if title and not return_dict:
                text_content.append(f"# {title}\n")

            # Body markdown via the clean hand-rolled walker. No double-parse
            # (we walk the bs4 tree we already built for hints) and no
            # ``>>>`` / ``<<<`` marker strings: each block-level element emits
            # final-form Markdown directly.
            content_text = _walk_to_markdown(main_content)
            content_text = cleanup_whitespace(content_text)

            if content_text:
                text_content.append(content_text)

            # Images.
            images = []
            if include_images:
                images = _extract_images(main_content, url)
                if images and not return_dict:
                    text_content.append("\n\n## Images\n\n" + "\n".join(images))

            # Links.
            links = []
            if include_links:
                links = _extract_links(main_content, url)
                if links and not return_dict:
                    text_content.append("\n\n## Links\n\n" + "\n".join(links))

            text_content = "\n".join(text_content).strip()

            if return_dict:
                ret = {
                    "title": title,
                    "content": text_content,
                }
                if include_images:
                    ret["images"] = images
                if include_links:
                    ret["links"] = links
                return ret
            else:
                return text_content.strip() or "No content found"

        except Exception as e:
            self.log.error(f"FastBS extraction failed: {e}")
            return f"Failed to extract content: {str(e)}"


# ---------------------------------------------------------------------------
# Clean hand-rolled walker
# ---------------------------------------------------------------------------

# Block-level tags handled with dedicated emission rules. Anything else is
# either an inline tag (recurse and concatenate) or unknown (recurse).
_HEADING_TAGS = frozenset({"h1", "h2", "h3", "h4", "h5", "h6"})


def _walk_to_markdown(element) -> str:
    """Walk a bs4 element and emit clean Markdown directly.

    Single-pass over ``element.children``. Each block-level child emits its
    final Markdown form (heading, paragraph, list, table, code block) with
    explicit ``\\n\\n`` separators. No intermediate marker strings, no
    post-hoc ``replace`` chain.

    Within the same parent we de-duplicate identical block emissions
    (``unique_parts``, mirroring the legacy walker's per-frame dedup). The
    set is *not* shared across recursion levels.
    """
    from bs4 import NavigableString  # type: ignore

    # NavigableString leaf: just its stripped text.
    if isinstance(element, NavigableString):
        return element.strip()

    if element is None:
        return ""

    # No children attribute / not iterable: degrade to plain text.
    if not hasattr(element, "children"):
        try:
            return element.get_text().strip()
        except Exception:
            return ""

    parts = []
    unique_parts = set()

    for child in element.children:
        piece = _emit_child(child, unique_parts)
        if piece:
            parts.append(piece)

    return "".join(parts)


def _emit_child(child, unique_parts: set) -> str:
    """Emit Markdown for one child node. Returns ``""`` if nothing to emit."""
    from bs4 import NavigableString  # type: ignore

    # Text nodes: trailing space so adjacent inline runs stay separated.
    if isinstance(child, NavigableString):
        text = child.strip()
        if not text:
            return ""
        return text + " "

    tag_name = child.name.lower() if child.name else ""

    # --- Block-level: headings -------------------------------------------
    if tag_name in _HEADING_TAGS:
        text = child.get_text().strip()
        if not text or text in unique_parts:
            return ""
        unique_parts.add(text)
        level = int(tag_name[1])
        return f"{'#' * level} {text}\n\n"

    # Semantic <header> (not <h1>): render its children but do not emit a
    # heading marker. (The legacy used level 0 -> a bare ``#`` prefix, which
    # is not valid Markdown. Choosing "no marker" is the documented
    # decision here.)
    if tag_name == "header":
        inner = _walk_to_markdown(child).strip()
        if not inner or inner in unique_parts:
            return ""
        unique_parts.add(inner)
        return inner + "\n\n"

    # --- Block-level: paragraphs -----------------------------------------
    if tag_name == "p":
        text = child.get_text().strip()
        if not text or text in unique_parts:
            return ""
        unique_parts.add(text)
        return f"{text}\n\n"

    # --- Block-level: lists ----------------------------------------------
    if tag_name in ("ul", "ol"):
        prefix = "- " if tag_name == "ul" else "1. "
        out = []
        for li in child.find_all("li", recursive=False):
            item_text = li.get_text().strip()
            if not item_text or item_text in unique_parts:
                continue
            unique_parts.add(item_text)
            out.append(f"{prefix}{item_text}\n")
        if not out:
            return ""
        return "".join(out) + "\n"

    # --- Block-level: tables ---------------------------------------------
    if tag_name == "table":
        table_md = _emit_table(child)
        if not table_md or table_md in unique_parts:
            return ""
        unique_parts.add(table_md)
        return table_md + "\n"

    # --- Block-level: code blocks ----------------------------------------
    if tag_name == "pre":
        # Either <pre><code>...</code></pre> or just <pre>.
        code_text = child.get_text()
        # Trim a single trailing newline (typical) but preserve the block.
        if code_text.endswith("\n"):
            code_text = code_text[:-1]
        if not code_text:
            return ""
        return f"```\n{code_text}\n```\n\n"

    # --- Inline / structural: <br> ---------------------------------------
    if tag_name == "br":
        return "\n"

    # --- Inline / unknown: recurse into children -------------------------
    # If the child has its own block-level descendants, we want their proper
    # Markdown emission; if it is a plain inline run, we collapse to text.
    if _has_block_descendant(child):
        return _walk_to_markdown(child)

    # Pure inline: collapse to stripped text + trailing space.
    text = child.get_text().strip()
    if not text:
        return ""
    return text + " "


def _has_block_descendant(element) -> bool:
    """Cheap check: does ``element`` contain any block-level descendant?

    We use ``find`` with a shortlist of block tags. ``find`` short-circuits
    on the first match, so this is cheap for the common "no block inside
    this inline" case.
    """
    if not hasattr(element, "find"):
        return False
    return (
        element.find(
            [
                "p",
                "h1",
                "h2",
                "h3",
                "h4",
                "h5",
                "h6",
                "header",
                "ul",
                "ol",
                "table",
                "pre",
            ]
        )
        is not None
    )


def _emit_table(table) -> str:
    """Emit a GitHub-Flavoured Markdown table from a ``<table>`` element.

    The first row (whether it contains ``<th>`` or only ``<td>``) is treated
    as the header row; a separator row of ``| --- | --- |`` follows. This
    is an enhancement over the legacy ``T|...|`` shape (which is not valid
    Markdown). The comparison test asserts only on title/images/links and
    non-empty body, so the structural change is safe.
    """
    rows = table.find_all("tr")
    if not rows:
        return ""

    parsed_rows = []
    for row in rows:
        cells = row.find_all(["td", "th"])
        if cells:
            parsed_rows.append([cell.get_text().strip() for cell in cells])

    if not parsed_rows:
        return ""

    header = parsed_rows[0]
    width = len(header)
    lines = ["| " + " | ".join(header) + " |"]
    lines.append("| " + " | ".join(["---"] * width) + " |")
    for row in parsed_rows[1:]:
        # Normalise short rows to the header width so the table stays valid.
        if len(row) < width:
            row = row + [""] * (width - len(row))
        elif len(row) > width:
            row = row[:width]
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Image / link extraction (URL normalisation per content-extractor contract)
# ---------------------------------------------------------------------------


def _extract_images(content, base_url: str) -> list:
    """Extract images from ``content``, normalising relative URLs against ``base_url``."""
    images = []
    for img in content.find_all("img"):
        src = img.get("src", "")
        alt = img.get("alt", "Image")
        if src:
            # Convert relative URLs to absolute.
            if src.startswith("//"):
                src = "https:" + src
            elif src.startswith("/"):
                base = "/".join(base_url.split("/")[:3])
                src = base + src
            elif not src.startswith(("http://", "https://")):
                path = "/".join(base_url.split("/")[:-1])
                src = path + "/" + src

            images.append(f"![{alt}]({src})")

    return images


def _extract_links(content, base_url: str) -> list:
    """Extract links from ``content``, normalising relative URLs against ``base_url``.

    Anchors (``href`` starting with ``#``), ``javascript:`` and ``mailto:``
    links are skipped.
    """
    links = []
    for link in content.find_all("a"):
        href = link.get("href", "")
        text = link.get_text().strip() or href

        if href and not href.startswith(("javascript:", "#", "mailto:")):
            # Convert relative URLs to absolute.
            if href.startswith("//"):
                href = "https:" + href
            elif href.startswith("/"):
                base = "/".join(base_url.split("/")[:3])
                href = base + href
            elif not href.startswith(("http://", "https://")):
                path = "/".join(base_url.split("/")[:-1])
                href = path + "/" + href

            links.append(f"[{text}]({href})")

    return links
