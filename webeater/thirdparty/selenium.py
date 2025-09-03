import asyncio
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime
from io import StringIO
import subprocess
from webeater.log import getLog
from webeater.rendering import HtmlRenderer

WINDOW_SIZE_W = 1920
WINDOW_SIZE_H = 3000
MAX_WINDOW_HEIGHT = 3000

SCROLL_DOWN_PAUSE = 1.0
SCROLL_UP_PAUSE = 0.5
FINAL_SCROLL_PAUSE = 2.0

TAB_BUTTON_CLICK_PRE_PAUSE = 0.1
TAB_BUTTON_CLICK_POST_PAUSE = 0.2

PAGINATION_PRE_PAUSE = TAB_BUTTON_CLICK_PRE_PAUSE
PAGINATION_POST_PAUSE = TAB_BUTTON_CLICK_POST_PAUSE

SCROLL_STEP = 3000  # Scroll down in smaller steps
SCROLL_END_MARGIN = 1000  # Stop scrolling when close to bottom


class SeleniumRuntime(HtmlRenderer):
    """
    A class to handle Selenium operations with optimized settings for performance.
    """

    def __init__(self):
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        self.log = getLog("webeater-selenium")

        self.By = By
        self.WebDriverWait = WebDriverWait
        self.EC = EC
        self.Driver = None
        self.window_size_w = WINDOW_SIZE_W
        self.window_size_h = WINDOW_SIZE_H

    async def shutdown(self):
        self.log.debug("Shutting down Selenium driver...")
        await asyncio.to_thread(self.Driver.quit)
        self.log.debug("Selenium driver shut down successfully.")

    async def reload(self):
        self.log.debug("Reloading Selenium driver...")
        if self.Driver:
            await asyncio.to_thread(self.Driver.quit)
            self.Driver = None
        await self.load()
        self.log.debug("Selenium driver reloaded successfully.")

    async def load(self, window_size_w=None, window_size_h=None, is_reload=False):
        """
        Load the Selenium WebDriver with optimized settings.
        """
        if not self.Driver:
            if self.window_size_w is None:
                if window_size_w is None:
                    self.window_size_w = WINDOW_SIZE_W
                else:
                    self.window_size_w = window_size_w
            elif window_size_w is not None:
                self.window_size_w = window_size_w

            if self.window_size_h is None:
                if window_size_h is None:
                    self.window_size_h = WINDOW_SIZE_H
                else:
                    self.window_size_h = window_size_h
            elif window_size_h is not None:
                self.window_size_h = window_size_h

            if not is_reload:
                # Import Selenium components only when needed
                from selenium import webdriver
                from selenium.webdriver.chrome.options import Options
                from selenium.webdriver.chrome.service import Service

            # Configure Chrome options for headless operation
            options = Options()
            options.add_argument("--headless")  # Run in headless mode (no UI)
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-extensions")
            options.add_argument(
                f"--window-size={self.window_size_w},{self.window_size_h}"
            )  # Set window size

            options.add_argument("--disable-background-networking")
            options.add_argument("--disable-background-timer-throttling")
            options.add_argument("--disable-backgrounding-occluded-windows")
            options.add_argument("--disable-renderer-backgrounding")
            options.add_argument("--disable-features=TranslateUI")
            options.add_argument("--disable-sync")
            options.add_argument("--disable-default-apps")
            options.add_argument("--disable-notifications")
            options.add_argument("--disable-push-messaging")
            options.add_argument("--disable-logging")
            options.add_argument("--log-level=3")
            options.add_argument("--silent")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument(
                "--remote-debugging-port=0"
            )  # Disable remote debugging to suppress DevTools message
            options.add_experimental_option("excludeSwitches", ["enable-logging"])
            options.add_experimental_option("useAutomationExtension", False)

            # Additional performance optimizations
            options.add_argument(
                "--disable-images"
            )  # Don't load images for faster loading
            # options.add_argument("--disable-javascript")  # Disable JS initially, enable after navigation if needed
            options.add_argument("--disable-plugins")
            options.add_argument("--disable-java")
            options.add_argument("--disable-web-security")
            options.add_argument("--disable-features=VizDisplayCompositor")
            options.add_argument("--disable-ipc-flooding-protection")
            options.add_argument("--disable-component-extensions-with-background-pages")
            options.add_argument("--disable-background-tasks")
            options.add_argument("--disable-site-isolation-trials")
            options.add_argument("--disable-features=TranslateUI,BlinkGenPropertyTrees")

            # Network optimizations
            options.add_argument("--aggressive-cache-discard")
            options.add_argument("--memory-pressure-off")
            options.add_argument("--max_old_space_size=4096")

            options.page_load_strategy = "eager"  # Options: 'normal', 'eager', 'none'

            # Set timeouts programmatically
            prefs = {
                "profile.default_content_setting_values": {
                    "notifications": 2,  # Block notifications
                    "media_stream": 2,  # Block camera/microphone
                    "geolocation": 2,  # Block location requests
                },
                "profile.managed_default_content_settings": {
                    "images": 2  # Block images
                },
            }
            options.add_experimental_option("prefs", prefs)

            # Create a Chrome service with suppressed output
            service = Service()
            service.creation_flags = (
                subprocess.CREATE_NO_WINDOW
                if hasattr(subprocess, "CREATE_NO_WINDOW")
                else 0
            )

            # Create a new Chrome driver with suppressed output
            # Redirect stdout/stderr to suppress DevTools message
            devnull = StringIO()
            with redirect_stdout(devnull), redirect_stderr(devnull):
                self.Driver = await asyncio.to_thread(
                    webdriver.Chrome, service=service, options=options
                )

        return self.Driver

    async def get_rendered_html(self, url: str, interact: bool = False) -> str:
        """
        Get rendered HTML content after JavaScript execution using Selenium.

        Args:
            url: The URL to render

        Returns:
            Rendered HTML content with JavaScript executed
        """
        try:
            start_time = datetime.now()
            if self.Driver is None:
                await self.load()
                self.log.debug(
                    f"Started Selenium driver @ {datetime.now() - start_time}"
                )

            try:
                # Set explicit timeouts for faster failure/success
                await asyncio.to_thread(
                    self.Driver.set_page_load_timeout, 5
                )  # 5 second timeout instead of default 30
                await asyncio.to_thread(
                    self.Driver.implicitly_wait, 2
                )  # 2 second implicit wait

                # Navigate to the URL
                await asyncio.to_thread(self.Driver.get, url)
                self.log.debug(f"Finished initial GET @ {datetime.now() - start_time}")

                # Wait for initial page load
                try:
                    await asyncio.to_thread(
                        self.WebDriverWait(self.Driver, 2).until,
                        self.EC.presence_of_element_located((self.By.TAG_NAME, "body")),
                    )
                except Exception:
                    pass
                self.log.debug(f"Page loaded @ {datetime.now() - start_time}")

                # Additional wait for ajax calls
                # await asyncio.to_thread(time.sleep, 1)  # Simple wait approach

                # Scroll to trigger any lazy loading
                await self.scroll_page()
                self.log.debug(f"Scroll complete @ {datetime.now() - start_time}")

                if interact:
                    #   TO DO:
                    #     # Try to interact with tabs to get more content
                    #     await _interact_with_tabs(driver)
                    #     self.log.debug(
                    #         f"Interaction complete @ {datetime.now() - self.start_time}"
                    #     )
                    raise NotImplementedError(
                        "Interaction with page elements is not implemented yet."
                    )

                # Get the rendered page source
                html = await asyncio.to_thread(lambda: self.Driver.page_source)
                self.log.debug(
                    f"Rendered HTML content length: {len(html)} characters @ {datetime.now() - start_time}"
                )
                return html
            except Exception as e:
                self.log.error(f"Error during page rendering: {str(e)}")
                raise e
            finally:
                # Always quit the driver to free resources
                # await asyncio.to_thread(driver.quit)
                pass

        except Exception as e:
            self.log.error(f"Error rendering JavaScript with Selenium: {str(e)}")
            if self.Driver:
                try:
                    await asyncio.to_thread(self.Driver.quit)
                except Exception:
                    pass
            raise

    async def scroll_page(self):
        """
        Aggressively scroll the page to trigger all lazy loading.
        """
        try:
            # Get initial page height
            height = await asyncio.to_thread(
                self.Driver.execute_script, "return document.body.scrollHeight"
            )

            # Scroll down in smaller chunks with longer pauses
            scroll_step = SCROLL_STEP  # Smaller steps
            scroll_height = 0
            scroll_height_end = WINDOW_SIZE_H

            self.log.debug(f"Starting page scroll, initial height: {height}")

            # First pass - scroll to bottom
            while (
                scroll_height < height - SCROLL_END_MARGIN
                and scroll_height_end < MAX_WINDOW_HEIGHT
            ):
                scroll_height += scroll_step
                scroll_height_end = min(scroll_height + WINDOW_SIZE_H, height)
                self.log.debug(f"Scrolling down: {scroll_height}/{height}")
                await asyncio.to_thread(
                    self.Driver.execute_script, f"window.scrollTo(0, {scroll_height});"
                )
                await asyncio.sleep(SCROLL_DOWN_PAUSE)

                # Check for new content
                new_height = await asyncio.to_thread(
                    self.Driver.execute_script, "return document.body.scrollHeight"
                )
                if new_height > height:
                    height = new_height
                    self.log.debug(f"Page expanded to {height} pixels")

            # Second pass - scroll back to top slowly
            while scroll_height > 0:
                scroll_height -= scroll_step * 2  # Go back faster
                scroll_height = 0  # max(0, scroll_height)
                await asyncio.to_thread(
                    self.Driver.execute_script, f"window.scrollTo(0, {scroll_height});"
                )
                self.log.debug(f"Scrolling up: {scroll_height}/{height}")
                await asyncio.sleep(SCROLL_UP_PAUSE)

            # Final wait at top
            await asyncio.sleep(FINAL_SCROLL_PAUSE)

            self.log.debug("Page scrolling completed")

        except Exception as e:
            self.log.warning(f"Error during page scrolling: {e}")
