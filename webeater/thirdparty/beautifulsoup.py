from webeater.util import cleanup_whitespace
from webeater.extracting import ContentExtractor
from webeater.log import getLog
from webeater.config import HintsConfig


class WebeaterBeautifulSoup(ContentExtractor):
    def __init__(self, hint_names: list = None, combined_hints: HintsConfig = None):
        super().__init__()
        self.log = getLog("weat-bs")

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
    ) -> str:
        """
        Enhanced BeautifulSoup extraction with smart content detection.
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

                # Remove by exact class name
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

            # Try to find main content areas

            main_content = None
            if hints and hints.main and hints.main.selectors:
                for selector in hints.main.selectors:
                    try:
                        found = soup.select(selector)
                        if found:
                            # Use the largest content area
                            main_content = max(found, key=lambda x: len(x.get_text()))
                            self.log.debug(
                                f"Found main content with hint selector: {selector}"
                            )
                            break
                    except Exception:
                        continue

            # If no main content found, use body but remove known noise
            if not main_content:
                main_content = soup.find("body") or soup
                self.log.info("Using full body content")

            # Extract text with better formatting
            text_content = []

            # Get title
            title = (
                soup.find("title").get_text().strip() if soup.find("title") else None
            )
            if title and not return_dict:
                text_content.append(f"# {title}\n")

            # Process main content
            content_text = _extract_structured_text(main_content)

            if content_text:
                content_text.replace("\n", ">>>")
                content_text = (
                    content_text.replace(">>><<<", "\n\n")
                    .replace(">>>", "\n")
                    .replace("<<<", "\n")
                    .replace(" < >>", "\n")
                    .replace("<", "")
                    .replace(">", "")
                )
                content_text = cleanup_whitespace(content_text)
                text_content.append(content_text)

            # Add images if requested
            if include_images:
                images = _extract_images(main_content, url)
                if images and not return_dict:
                    text_content.append("\n\n## Images\n\n" + "\n".join(images))

            # Add links if requested
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
            self.log.error(f"Enhanced BeautifulSoup extraction failed: {e}")
            return f"Failed to extract content: {str(e)}"


def _extract_structured_text(element) -> str:
    """
    Extract text while preserving some structure.
    """
    from bs4 import NavigableString

    if isinstance(element, NavigableString):
        return element.strip()

    if not element:
        return ""

    if not hasattr(element, "children") or not element.children:
        return element.get_text().strip()

    text_parts = []
    unique_parts = set()
    tag_name = None
    element_name = element.name.lower() if element.name else ""
    # Handle different elements differently
    for child in element.children:
        if hasattr(child, "children"):
            child_children = [c for c in child.children]
        else:
            child_children = []
        text = ""

        tag_name = child.name.lower() if child.name else ""

        # Headers
        if tag_name in ["header", "h1", "h2", "h3", "h4", "h5", "h6"]:
            if tag_name == "header":
                level = 0
            else:
                level = int(tag_name[1])
            text = child.get_text().strip()
            if text:
                if text not in unique_parts:
                    unique_parts.add(text)
                    text_parts.append(f"\n{'#' * level} {text}\n")

        # Paragraphs
        elif tag_name == "p":
            text = child.get_text().strip()
            if text:
                if text not in unique_parts:
                    unique_parts.add(text)
                    text_parts.append(f"\n{text}\n")

        # Lists
        elif tag_name in ["ul", "ol"]:
            items = child.find_all("li")
            if items:
                text_parts.append("\n")
                for item in items:
                    item_text = item.get_text().strip()
                    if item_text:
                        if item_text not in unique_parts:
                            unique_parts.add(item_text)
                            prefix = "- " if tag_name == "ul" else "1. "
                            text_parts.append(f"{prefix}{item_text}\n")

        # Tables
        elif tag_name == "table":
            table_text = _extract_table(child)
            if table_text:
                if table_text not in unique_parts:
                    unique_parts.add(table_text)
                    text_parts.append(f"\nT|{table_text}|\n")

        elif not child_children:
            if isinstance(child, NavigableString):
                text = child.strip()
            else:
                text = child.get_text().strip()
            if text.strip():
                text_parts.append(text + " ")

        if child_children:
            # If it has children, recurse
            for sub_child in child_children:
                sub_text = _extract_structured_text(sub_child).strip()
                if sub_text:
                    text_parts.append(sub_text)

    res = " ".join(text_parts).strip()
    res = f">{res}< "
    if element_name == "article":
        res = f"\n{res}\n"

    return res


def _extract_table(table) -> str:
    """
    Extract table content in a readable format.
    """
    rows = table.find_all("tr")
    if not rows:
        return ""

    table_lines = []
    for row in rows:
        cells = row.find_all(["td", "th"])
        if cells:
            cell_texts = [cell.get_text().strip() for cell in cells]
            table_lines.append(" | ".join(cell_texts))

    return "\n".join(table_lines)


def _extract_images(content, base_url: str) -> list:
    """Extract images from content."""
    images = []
    for img in content.find_all("img"):
        src = img.get("src", "")
        alt = img.get("alt", "Image")
        if src:
            # Convert relative URLs to absolute
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
    """Extract links from content."""
    links = []
    for link in content.find_all("a"):
        href = link.get("href", "")
        text = link.get_text().strip() or href

        if href and not href.startswith(("javascript:", "#", "mailto:")):
            # Convert relative URLs to absolute
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
