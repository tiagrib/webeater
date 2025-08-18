from weat.util import cleanup_whitespace
from weat.extracting import ContentExtractor
from weat.log import getLog


class WebeaterBeautifulSoup(ContentExtractor):
    def __init__(self):
        super().__init__()
        self.log = getLog("weat-bs")

    async def load(self):
        from bs4 import BeautifulSoup  # type: ignore

        self._BSCLASS = BeautifulSoup

        # Remove unwanted elements
        self.unwanted_tags = [
            "script",
            "style",
            "nav",
            "footer",
            "aside",
            "advertisement",
            "ads",
        ]
        self.unwanted_classes = [
            "menu",
            "footer",
            "ad",
            "advertisement",
            "cookie",
            "popup",
        ]
        self.unwanted_ids = ["menu", "footer", "ad", "advertisement"]
        self.main_content_selectors = [
            "main",
            ".container-fluid",
            '[role="main"]',
            "#main",
            ".main",
            "#content",
            ".content",
            ".main-content",
            "article",
            ".article",
            "#article",
            ".page-content",
        ]

        sports_main_content_selectors = [
            '[class*="calendar"]',
            '[class*="schedule"]',
            '[class*="fixture"]',
        ]

    async def extract_content(
        self,
        url: str,
        html: str,
        include_images: bool = False,
        include_links: bool = False,
    ) -> str:
        """
        Enhanced BeautifulSoup extraction with smart content detection.
        """
        try:
            soup = self._BSCLASS(html, "html.parser")

            # Remove by tag
            for tag in self.unwanted_tags:
                for element in soup.find_all(tag):
                    self.log.debug(f"Removing element with tag: {tag}")
                    element.decompose()

            # Remove by exact class name
            for class_name in self.unwanted_classes:
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
            for id_name in self.unwanted_ids:
                for element in soup.find_all(
                    lambda tag: tag.has_attr("id") and tag.get("id", "") == id_name
                ):
                    self.log.debug(f"Removing element with id: {id_name}")
                    element.decompose()

            # Try to find main content areas

            main_content = None
            for selector in self.main_content_selectors:
                try:
                    found = soup.select(selector)
                    if found:
                        # Use the largest content area
                        main_content = max(found, key=lambda x: len(x.get_text()))
                        self.log.info(f"Found main content with selector: {selector}")
                        break
                except Exception:
                    continue

            # If no main content found, use body but remove known noise
            if not main_content:
                main_content = soup.find("body") or soup
                self.log.info("Using full body content")

            # Extract text with better formatting
            text_parts = []

            # Get title
            title = soup.find("title")
            if title:
                text_parts.append(f"# {title.get_text().strip()}\n")

            # Process main content
            content_text = _extract_structured_text(main_content)

            if content_text:
                content_text.replace("\n", ">>>")
                content_text = content_text.replace(">>><<<", "\n\n").replace(">>>", "\n").replace("<<<", "\n").replace(" < >>", "\n").replace("<", "").replace(">", "")
                

            text_parts.append(content_text)

            # Add images if requested
            if include_images:
                images = _extract_images(main_content, url)
                if images:
                    text_parts.append("\n\n## Images\n\n" + "\n".join(images))

            # Add links if requested
            if include_links:
                links = _extract_links(main_content, url)
                if links:
                    text_parts.append("\n\n## Links\n\n" + "\n".join(links))

            result = "\n".join(text_parts).strip()
            if result:
                result = cleanup_whitespace(result)

            return result.strip() or "No content found"

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
                    # printf"Grab header: {text} (level {level})")
                    text_parts.append(f"\n{'#' * level} {text}\n")
                else:
                    # printf"Duplicate1: {text")
                    pass

        # Paragraphs
        elif tag_name == "p":
            text = child.get_text().strip()
            if text:
                if text not in unique_parts:
                    unique_parts.add(text)
                    # printf"Grab paragraph: {text}")
                    text_parts.append(f"\n{text}\n")
                else:
                    # printf"Duplicate2: {text}")
                    pass

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
                            # printf"Grab list item: {item_text}")
                            text_parts.append(f"{prefix}{item_text}\n")
                        else:
                            # printf"Duplicate3: {item_text}")
                            pass

        # Tables
        elif tag_name == "table":
            table_text = _extract_table(child)
            if table_text:
                if table_text not in unique_parts:
                    unique_parts.add(table_text)
                    # printf"Grab table content: {table_text}")
                    text_parts.append(f"\nT|{table_text}|\n")
                else:
                    # printf"Duplicate4: {table_text}")
                    pass

        elif not child_children:
            if isinstance(child, NavigableString):
                text = child.strip()
            else:
                text = child.get_text().strip()
                # printf"Grab text from {tag_name}: {text}")
            if text.strip():
                text_parts.append(text + " ")

        if child_children:
            # If it has children, recurse
            for sub_child in child_children:
                # printf"Processing child: {sub_child.name if hasattr(sub_child, 'name') else 'N/A'} of {tag_name}")
                sub_text = _extract_structured_text(sub_child).strip()
                if sub_text:
                    text_parts.append(sub_text)
        else:
            # printf"Text without children - {tag_name}: {text}")
            pass

    tag_name = element.name.lower() if element.name else ""
    tag_pref = {
        "article": "\n",
    }.get(tag_name, " ")

    res = " ".join(text_parts).strip()
    res = f"{tag_pref}>{res}< "
    if tag_name not in ["div", "section"]:
        # printf"Final extracted content[{tag_name}]: {res}")
        pass
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
