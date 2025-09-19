from crawl4ai import AsyncWebCrawler, BrowserConfig

browser_config = BrowserConfig(
    headless=True,
    verbose=False,
)

shared_crawler = AsyncWebCrawler(config=browser_config)
