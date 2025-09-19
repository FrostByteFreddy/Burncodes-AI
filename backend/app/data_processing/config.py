from crawl4ai import CrawlerRunConfig, CacheMode

# Centralized configuration for CrawlerRun
CRAWLER_RUN_CONFIG = CrawlerRunConfig(
    simulate_user=True,
    magic=True,
    page_timeout=30000,
    check_robots_txt=True,
    cache_mode=CacheMode.ENABLED,
    override_navigator=True,
    stream=False,  # Kept from original config as it seems important for the processing flow
)
