from datetime import datetime
from weat.config import DEFAULT_CONFIG_FILE, WeatConfig
from weat.thirdparty.beautifulsoup import WebeaterBeautifulSoup
from weat.thirdparty.selenium import SeleniumRuntime
from weat.log import getLog


class Webeater:
    """
    WebeaterEngine is the main class for the webeater module.
    It provides methods to initialize the engine, load configurations,
    and perform actions related to web content extraction.
    """

    def __init__(self, config: WeatConfig):
        self.config = config
        self.log = getLog()
        self.log.info(f"WebeaterEngine initialized with config: {self.config}")

        self.html_renderer = SeleniumRuntime()
        # Use the pre-combined hints from config
        self.content_extraction_hints = self.config.get_combined_hints()
        self.context_extractor = WebeaterBeautifulSoup()

    async def _async_init(self):
        """Async initialization method"""
        self.log.debug("Loading Selenium driver...")
        await self.html_renderer.load(
            self.config.window_size_w, self.config.window_size_h
        )
        self.log.debug("Selenium driver loaded successfully.")

        self.log.debug("Load BeautifulSoup extractor...")
        await self.context_extractor.load()
        self.log.debug("BeautifulSoup extractor loaded successfully.")

        return self

    @classmethod
    async def create(cls, config: WeatConfig):
        """Factory method to create and initialize WebeaterEngine"""
        instance = cls(config=config)
        await instance._async_init()
        return instance

    async def get(self, url, hints=None, return_dict=False, content_only=False):
        """
        Fetch content from the given URL using the engine.
        """
        self.log.info(
            f"Fetching content {'only ' if content_only else ''}{'as JSON ' if return_dict else ''}from {url}"
        )
        start_time = datetime.now()
        try:
            html_content = await self.html_renderer.get_rendered_html(url)

        except Exception as e:
            self.log.error(f"JavaScript rendering failed: {e}")
            html_content = None
            await self.html_renderer.reload()

        if html_content:
            self.log.info(
                f"Successfully rendered HTML content of '{len(html_content)}' characters in {datetime.now() - start_time}s."
            )

            if self.context_extractor is None:
                self.log.error(
                    "Content extractor not set. Please set a content extractor before fetching content."
                )
                content = html_content
            else:
                if hints is None:
                    hints = self.content_extraction_hints

                render_time = datetime.now()
                content = await self.context_extractor.extract_content(
                    url,
                    html_content,
                    hints=hints,
                    return_dict=return_dict,
                    include_images=not content_only,
                    include_links=not content_only,
                )
                self.log.info(
                    f"Content extracted from {url} in {render_time - start_time}s. Total eating time: {datetime.now() - start_time}s."
                )
        else:
            self.log.error(f"Failed to fetch content from {url}.")
            content = None

        return content

    async def shutdown(self):
        """Shutdown the engine and clean up resources."""
        if self.html_renderer:
            await self.html_renderer.shutdown()
