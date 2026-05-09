"""
ingestion/utils.py
Shared utilities for the ingestion pipeline.
"""
import asyncio
from uuid import UUID
from urllib.parse import urldefrag

from app.database.supabase_client import supabase
from app.logging_config import error_logger


def normalize_url(url: str) -> str:
    """Normalizes a URL by removing fragment and trailing slash."""
    return urldefrag(url)[0].rstrip("/")


async def resolve_crawl_mode(tenant_id: UUID) -> str:
    """Returns the tenant's crawl_mode from the DB. Defaults to 'playwright_llm'."""
    loop = asyncio.get_running_loop()
    try:
        response = await loop.run_in_executor(
            None,
            lambda: supabase.table("tenants").select("crawl_mode").eq("id", str(tenant_id)).single().execute(),
        )
        return (response.data or {}).get("crawl_mode") or "playwright_llm"
    except Exception:
        return "playwright_llm"
