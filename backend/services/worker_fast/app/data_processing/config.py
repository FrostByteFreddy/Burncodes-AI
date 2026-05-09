# data_processing/config.py — stub for worker_fast (no crawl4ai)
# CRAWLER_RUN_CONFIG is only used by the Playwright pipeline (worker_heavy).
# worker_fast uses soup mode only.

MAX_CONCURRENT_CRAWLS_PER_JOB = 15
CRAWLER_RUN_CONFIG = None  # Not used by worker_fast; Playwright routes to worker_heavy