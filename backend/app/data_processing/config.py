from crawl4ai import CrawlerRunConfig, CacheMode

# Centralized configuration for CrawlerRun
CRAWLER_RUN_CONFIG = CrawlerRunConfig(
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