import os
from crawl4ai import AsyncWebCrawler, BrowserConfig

# Define a writable cache path within the persistent /data volume.
# This is configurable via environment variables for flexibility.
CRAWL_CACHE_PATH = os.getenv("CRAWL_CACHE_PATH", "/data/crawl4ai_cache")

browser_config = BrowserConfig(
    headless=True,
    verbose=False,
    user_agent_mode="random",
    viewport_width=1920,
    viewport_height=1080,
    check_robots_txt=True,
    enable_stealth=True
)

# Pass the base_directory to the crawler to ensure it uses a writable path.
shared_crawler = AsyncWebCrawler(
    config=browser_config,
    base_directory=CRAWL_CACHE_PATH
)