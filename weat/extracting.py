from abc import ABC


class ContentExtractor(ABC):
    """
    A class to define the interface for content extraction operations in Webeater.
    """

    def __init__(self):
        pass

    async def shutdown(self):
        raise NotImplementedError("This method should be overridden in subclasses.")

    async def load():
        raise NotImplementedError("This method should be overridden in subclasses.")

    async def extract_content(self, html: str) -> str:
        """
        Get the text content from the HTML.
        """
        raise NotImplementedError("This method should be overridden in subclasses.")
