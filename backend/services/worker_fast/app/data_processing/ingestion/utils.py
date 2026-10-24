"""
ingestion/utils.py
Shared utilities for the ingestion pipeline.
"""
from urllib.parse import urldefrag


def normalize_url(url: str) -> str:
    """Normalizes a URL by removing fragment and trailing slash."""
    return urldefrag(url)[0].rstrip("/")
