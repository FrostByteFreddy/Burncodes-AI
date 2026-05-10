"""ingestion package."""
# Direct imports only — old url_ingester and file_ingester have been superseded.
# crawl_tasks.py imports directly from ingestion.utils and ingestion.soup_extractor.
from app.data_processing.ingestion.utils import normalize_url, resolve_crawl_mode

__all__ = ["normalize_url", "resolve_crawl_mode"]
