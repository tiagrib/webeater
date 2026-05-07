"""
WebeaterFastBS — a ``ContentExtractor`` implementation that mirrors
``WebeaterBeautifulSoup`` for hint application, title/image/link extraction
and output assembly, but replaces the fragile hand-rolled
``_extract_structured_text`` walker with ``html2text`` for the Markdown body.

Contract: see ``metak-shared/api-contracts/content-extractor.md``.
"""

from webeater.util import cleanup_whitespace
from webeater.extracting import ContentExtractor
from webeater.log import getLog
from webeater.config import HintsConfig


class WebeaterFastBS(ContentExtractor):
    """Fast BeautifulSoup + html2text content extractor.

    Drop-in equivalent of ``WebeaterBeautifulSoup`` for the contracted fields
    (title, images, links, dict shape). The body Markdown is produced by
    ``html2text.HTML2Text`` rather than the legacy structured-text walker.
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
        in everything except the body-text generation step.
        """
        try:
            import html2text

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

            # Body markdown via html2text. We strip its own image/link output
            # because we re-attach our own ``## Images`` / ``## Links`` blocks
            # and our own ``images`` / ``links`` dict keys.
            converter = html2text.HTML2Text()
            converter.body_width = 0  # don't hard-wrap
            converter.ignore_links = True  # we re-attach our own list
            converter.ignore_images = True  # we re-attach our own list
            converter.skip_internal_links = True
            content_text = converter.handle(str(main_content))
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
