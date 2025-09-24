import os
from crawl4ai import AsyncWebCrawler, BrowserConfig

CRAWL_CACHE_PATH = os.getenv("CRAWL_CACHE_PATH", "/data/crawl4ai_cache")

browser_config = BrowserConfig(
    headless=True,
    extra_args=[
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--no-zygote',
        '--disable-web-security',
        '--disable-features=VizDisplayCompositor',
    ]
)

def get_crawler():
    """Creates and returns a new AsyncWebCrawler instance."""
    return AsyncWebCrawler(
        config=browser_config,
        base_directory=CRAWL_CACHE_PATH
    )