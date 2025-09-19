from crawl4ai import AsyncWebCrawler, BrowserConfig

browser_config = BrowserConfig(
    headless=True,
    verbose=False,
    # Set a long timeout to keep the browser alive
    playwright_browser_init_timeout=300,
)

shared_crawler = AsyncWebCrawler(config=browser_config)
