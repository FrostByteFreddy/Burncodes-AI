"""
chunking/llm_chunker.py
LLM-powered markdown + PDF cleaning and semantic chunking.
"""
import os
import asyncio
from app.database.supabase_client import supabase
from app.billing.services import BillingService
from app.logging_config import error_logger
from app.prompts import CLEANUP_PROMPT_TEMPLATES, PDF_CLEANUP_PROMPT_TEMPLATES

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

INDEXING_GEMINI_MODEL = os.getenv("INDEXING_GEMINI_MODEL")
MIN_CONTENT_CHARS = 100


async def async_clean_and_chunk_markdown_with_llm(
    markdown_text: str, doc_language: str = "en", source_id: int = None
) -> tuple[str, int, int]:
    """Uses an LLM to clean, optimize, and chunk raw markdown. Returns (content, input_tokens, output_tokens)."""

    if len(markdown_text.strip()) < MIN_CONTENT_CHARS:
        error_logger.warning(
            "Skipping LLM chunking for source_id=%s: content too short (%d chars)",
            source_id, len(markdown_text.strip()),
        )
        return "", 0, 0

    error_logger.info(
        "Calling LLM to clean and chunk markdown (%d chars) lang='%s' source_id=%s",
        len(markdown_text), doc_language, source_id,
    )

    template = CLEANUP_PROMPT_TEMPLATES.get(doc_language, CLEANUP_PROMPT_TEMPLATES["en"])
    cleanup_llm = ChatGoogleGenerativeAI(model=INDEXING_GEMINI_MODEL, temperature=0.0, timeout=600)
    cleanup_prompt = PromptTemplate.from_template(template)
    cleanup_chain = cleanup_prompt | cleanup_llm

    input_tokens = len(markdown_text) // 4
    response = await cleanup_chain.ainvoke({"raw_markdown": markdown_text})
    error_logger.info("Markdown cleaned and chunked successfully for source_id=%s", source_id)
    output_tokens = len(response.content) // 4

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(
        None,
        lambda: supabase.table("tenant_sources").update({"readme": response.content}).eq("id", source_id).execute(),
    )
    return response.content, input_tokens, output_tokens


async def async_clean_pdf_text_with_llm(raw_text: str, doc_language: str = "en") -> tuple[str, int, int]:
    """Uses an LLM to clean and reconstruct PDF text into valid markdown."""
    error_logger.info("Calling LLM to clean PDF text chunk (%d chars) lang='%s'", len(raw_text), doc_language)

    template = PDF_CLEANUP_PROMPT_TEMPLATES.get(doc_language, PDF_CLEANUP_PROMPT_TEMPLATES["en"])
    cleanup_llm = ChatGoogleGenerativeAI(model=INDEXING_GEMINI_MODEL, temperature=0.0, timeout=600)
    cleanup_prompt = PromptTemplate.from_template(template)
    cleanup_chain = cleanup_prompt | cleanup_llm

    input_tokens = len(raw_text) // 4
    try:
        response = await cleanup_chain.ainvoke({"raw_text": raw_text})
        output_tokens = len(response.content) // 4
        return response.content, input_tokens, output_tokens
    except Exception as e:
        error_logger.warning("Error cleaning PDF text chunk (falling back to raw text): %s", e)
        return raw_text, input_tokens, 0
