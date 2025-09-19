import os
from crawl4ai import AsyncWebCrawler, BrowserConfig
from app.data_processing.config import CRAWLER_RUN_CONFIG

CRAWL_CACHE_PATH = os.getenv("CRAWL_CACHE_PATH", "/data/crawl4ai_cache")

shared_crawler = AsyncWebCrawler(
    config=CRAWLER_RUN_CONFIG,
    base_directory=CRAWL_CACHE_PATH
)