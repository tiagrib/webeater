from abc import ABC


class HtmlRenderer(ABC):
    """
    A class to define the interface for web eating runtime operations in Webeater.
    """

    def __init__(self):
        pass

    async def shutdown(self):
        raise NotImplementedError("This method should be overridden in subclasses.")

    async def load(self, window_size_w=1920, window_size_h=1080):
        raise NotImplementedError("This method should be overridden in subclasses.")

    async def get_rendered_html(
        self, url: str, interact: bool = False, driver=None
    ) -> str:
        """
        Get rendered HTML content after JavaScript execution using Selenium.

        Args:
            url: The URL to render
            interact: Whether to interact with the page after loading

        Returns:
            Rendered HTML content with JavaScript executed
        """
        raise NotImplementedError("This method should be overridden in subclasses.")
