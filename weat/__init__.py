import asyncio


from weat.config import DEFAULT_CONFIG_FILE, WeatConfig
from weat.thirdparty.selenium import load_selenium_driver
from weat.log import getLog


class WebeaterEngine:
    """
    WebeaterEngine is the main class for the webeater module.
    It provides methods to initialize the engine, load configurations,
    and perform actions related to web content extraction.
    """

    def __init__(self, config_filename=DEFAULT_CONFIG_FILE):
        self.config = WeatConfig(filename=config_filename)
        self.log = getLog()
        self.log.info(f"WebeaterEngine initialized with config: {self.config}")

        self.selenium = None

    async def _async_init(self):
        """Async initialization method"""
        self.log.info("Loading Selenium driver...")
        self.selenium = await load_selenium_driver(
            self.config.window_size_w, self.config.window_size_h
        )
        self.log.info("Selenium driver loaded successfully.")
        return self

    @classmethod
    async def create(cls):
        """Factory method to create and initialize WebeaterEngine"""
        instance = cls()
        await instance._async_init()
        return instance

    async def get(self, url):
        """
        Get the content of the specified URL using Selenium.

        :param url: The URL to fetch content from.
        :return: The content of the page.
        """
        self.log.info(f"Fetching content from {url}")
        # Placeholder for actual content fetching logic
        pass

    async def shutdown(self):
        """Shutdown the engine and clean up resources."""
        if self.selenium:
            self.log.info("Shutting down Selenium driver...")
            await asyncio.to_thread(self.selenium.quit)
            self.log.info("Selenium driver shut down successfully.")
        else:
            self.log.warning("No Selenium driver to shut down.")
