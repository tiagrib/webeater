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

    def __init__(self, config_filename=DEFAULT_CONFIG_FILE):
        self.config = WeatConfig(filename=config_filename)
        self.log = getLog()
        self.log.info(f"WebeaterEngine initialized with config: {self.config}")

        self.html_renderer = SeleniumRuntime()
        self.context_extractor = WebeaterBeautifulSoup()

    async def _async_init(self):
        """Async initialization method"""
        self.log.info("Loading Selenium driver...")
        await self.html_renderer.load(
            self.config.window_size_w, self.config.window_size_h
        )
        self.log.info("Selenium driver loaded successfully.")

        self.log.info("Load BeautifulSoup extractor...")
        await self.context_extractor.load()
        self.log.info("BeautifulSoup extractor loaded successfully.")

        return self

    @classmethod
    async def create(cls):
        """Factory method to create and initialize WebeaterEngine"""
        instance = cls()
        await instance._async_init()
        return instance

    async def get(self, url):
        """
        Fetch content from the given URL using the engine.
        """
        self.log.info(f"Fetching content from {url}")
        start_time = datetime.now()
        try:
            html_content = await self.html_renderer.get_rendered_html(url)

        except Exception as e:
            self.log.error(f"JavaScript rendering failed: {e}")
            html_content = None

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
                render_time = datetime.now()
                content = await self.context_extractor.extract_content(
                    url, html_content
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
