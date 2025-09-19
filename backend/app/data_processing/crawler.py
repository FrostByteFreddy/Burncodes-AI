from crawl4ai import AsyncWebCrawler, BrowserConfig

browser_config = BrowserConfig(
    headless=True,
    verbose=False,
    user_agent_mode="random",
)

shared_crawler = AsyncWebCrawler(config=browser_config)
