import os
from crawl4ai import AsyncWebCrawler, BrowserConfig

CRAWL_CACHE_PATH = os.getenv("CRAWL_CACHE_PATH", "/data/crawl4ai_cache")

browser_config = BrowserConfig(
    headless=True,
    extra_args=['--no-sandbox', '--disable-setuid-sandbox','--disable-gpu','--single-process']
)

shared_crawler = AsyncWebCrawler(
    config=browser_config,
    base_directory=CRAWL_CACHE_PATH
)