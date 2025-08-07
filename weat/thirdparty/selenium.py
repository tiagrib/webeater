async def load_selenium_driver(window_size_w, window_size_h):
    # Import Selenium components only when needed
    import asyncio
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    # Configure Chrome options for headless operation
    options = Options()
    options.add_argument("--headless")  # Run in headless mode (no UI)
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    options.add_argument(
        f"--window-size={window_size_w},{window_size_h}"
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

    # Additional performance optimizations
    options.add_argument("--disable-images")  # Don't load images for faster loading
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

    # Create a new Chrome driver
    driver = await asyncio.to_thread(webdriver.Chrome, options=options)
    return driver
