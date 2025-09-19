from crawl4ai import CrawlerRunConfig, CacheMode

# Maximum number of concurrent crawling tasks allowed per job.
# This helps to control resource usage and prevent overloading the system.
MAX_CONCURRENT_CRAWLS_PER_JOB = 1

# Centralized configuration for CrawlerRun
CRAWLER_RUN_CONFIG = CrawlerRunConfig(
    
)