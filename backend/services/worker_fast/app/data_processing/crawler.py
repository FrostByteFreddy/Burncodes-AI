"""
data_processing/crawler.py — stub for worker_fast.

The fast worker handles soup-mode URL processing only.
Playwright/crawl4ai crawling is routed to worker_heavy via the 'heavy' queue.
If this function is ever called, the crawl_mode was misconfigured.
"""


def get_crawler():
    raise RuntimeError(
        "worker_fast does not have crawl4ai/Playwright installed. "
        "Playwright crawls must be routed to the 'heavy' queue (worker_heavy)."
    )