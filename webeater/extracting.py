from __future__ import annotations

from abc import ABC

from webeater.config import HintsConfig


class ContentExtractor(ABC):
    """
    A class to define the interface for content extraction operations in Webeater.
    """

    def __init__(self):
        pass

    async def shutdown(self):
        raise NotImplementedError("This method should be overridden in subclasses.")

    async def load(self):
        raise NotImplementedError("This method should be overridden in subclasses.")

    async def extract_content(
        self,
        url: str,
        html: str,
        include_images: bool = True,
        include_links: bool = True,
        hints: HintsConfig = None,
        return_dict: bool = True,
    ) -> str | dict:
        """
        Extract content from the rendered HTML.

        See ``metak-shared/api-contracts/content-extractor.md`` for the full
        contract. Implementations must accept this wide signature; the narrow
        ``extract_content(self, html)`` signature that previously lived here
        was a documentation bug.
        """
        raise NotImplementedError("This method should be overridden in subclasses.")
