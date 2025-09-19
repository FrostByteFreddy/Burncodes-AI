import os
from crawl4ai import AsyncWebCrawler, BrowserConfig

CRAWL_CACHE_PATH = os.getenv("CRAWL_CACHE_PATH", "/data/crawl4ai_cache")

browser_config = BrowserConfig(
    headless=True,
    verbose=False,
    user_agent_mode="random",
    viewport_width=1920,
    viewport_height=1080,
    extra_args=['--disable-crash-reporter']
)

shared_crawler = AsyncWebCrawler(
    config=browser_config,
    base_directory=CRAWL_CACHE_PATH
)