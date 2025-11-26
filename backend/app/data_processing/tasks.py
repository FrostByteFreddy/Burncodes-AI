import os
import asyncio
import re
from datetime import datetime, timezone
from uuid import UUID

from app.database.supabase_client import supabase
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from app.prompts import CLEANUP_PROMPT_TEMPLATES

DEBUG = os.getenv("DEBUG", "False").lower() == "true"
QUERY_GEMINI_MODEL = os.getenv("QUERY_GEMINI_MODEL", "gemini-2.5-flash")

async def async_clean_and_chunk_markdown_with_llm(markdown_text: str, doc_language: str = 'en', source_id: int = None, update_db: bool = True) -> str:
    """Uses an LLM to clean, optimize, and chunk raw markdown asynchronously."""
    print(f"🤖 Calling LLM to clean and chunk markdown ({len(markdown_text)} chars) with language '{doc_language}'...")

    # Select the appropriate prompt template based on the document language
    template = CLEANUP_PROMPT_TEMPLATES.get(doc_language, CLEANUP_PROMPT_TEMPLATES['en'])
    print(f"📄 Using doc_language: {doc_language}")

    cleanup_llm = ChatGoogleGenerativeAI(model=QUERY_GEMINI_MODEL, temperature=0.0, timeout=1200, max_retries=6)
    cleanup_prompt = PromptTemplate.from_template(template)
    cleanup_chain = cleanup_prompt | cleanup_llm
    response = await cleanup_chain.ainvoke({"raw_markdown": markdown_text})
    print("✅ Markdown cleaned and chunked successfully.")
    
    # Write the processed markdown to the "readme" column in tenant_sources
    if update_db and source_id:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, lambda: supabase.table('tenant_sources').update({"readme": response.content}).eq('id', source_id).execute())

    return response.content

async def async_create_document_chunks_with_metadata(content: str, source: str, source_id: int, tenant_id: UUID) -> list[Document]:
    """Asynchronously cleans, chunks, and creates Document objects with metadata."""
    documents = []
    loop = asyncio.get_running_loop()
    try:
        # Fetch tenant to get doc_language
        tenant_response = await loop.run_in_executor(None, lambda: supabase.table('tenants').select('doc_language').eq('id', str(tenant_id)).single().execute())
        doc_language = tenant_response.data.get('doc_language', 'en') if tenant_response.data else 'en'

        await loop.run_in_executor(None, lambda: supabase.table('tenant_sources').update({"status": "PROCESSING"}).eq('id', source_id).execute())

        # The LLM now returns a single string with chunks separated by a specific token.
        cleaned_and_chunked_content = await async_clean_and_chunk_markdown_with_llm(content, doc_language, source_id)
        chunks = [chunk.strip() for chunk in cleaned_and_chunked_content.split("---CHUNK_SEPARATOR---") if chunk.strip()]

        if DEBUG:
            try:
                os.makedirs('crawled_markdown', exist_ok=True)
                safe_filename = re.sub(r'https://?|www\.|\/|\?|\=|\&', '_', source) + ".md"
                filepath = os.path.join('crawled_markdown', safe_filename)
                # Save the raw, chunked output for inspection
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"# SOURCE: {source}\n\n{cleaned_and_chunked_content}")
                print(f"🕵️‍♂️ Saved CLEANED and CHUNKED markdown for {source} to {filepath}")
            except Exception as e:
                print(f"❌ Could not save cleaned markdown file for {source}: {e}")

        timestamp = datetime.now(timezone.utc).isoformat()
        for i, chunk in enumerate(chunks):
            doc = Document(
                page_content=chunk,
                metadata={"source": source, "source_id": source_id, "chunk": i, "last_updated": timestamp}
            )
            documents.append(doc)

        return documents
    except Exception as e:
        print(f"Error creating document chunks for source {source_id}: {e}")
        await loop.run_in_executor(None, lambda: supabase.table('tenant_sources').update({"status": "ERROR"}).eq('id', source_id).execute())
        return []

async def async_create_document_chunks_for_structured_data(content: str, source: str, source_id: int) -> list[Document]:
    """Asynchronously chunks and creates Document objects for structured data without LLM cleaning."""
    documents = []
    loop = asyncio.get_running_loop()
    try:
        # Note: This path skips the `async_clean_markdown_with_llm` step
        await loop.run_in_executor(None, lambda: supabase.table('tenant_sources').update({"status": "PROCESSING"}).eq('id', source_id).execute())

        # For structured data, create a single document with the entire content.
        timestamp = datetime.now(timezone.utc).isoformat()
        doc = Document(
            page_content=content,
            metadata={"source": source, "source_id": source_id, "chunk": 0, "last_updated": timestamp}
        )
        documents.append(doc)

        print(f"✅ Created 1 document for structured file {source} (source_id: {source_id})")
        return documents
    except Exception as e:
        print(f"Error creating document chunks for structured source {source_id}: {e}")
        await loop.run_in_executor(None, lambda: supabase.table('tenant_sources').update({"status": "ERROR"}).eq('id', source_id).execute())
        return []

async def _get_document_chunks_from_content(content: str, source: str, source_id: int, ext: str, tenant_id: UUID) -> list[Document]:
    """Internal helper to decide which chunking strategy to use based on file extension."""
    structured_extensions = ['.csv', '.ics']
    if ext in structured_extensions:
        # Use the direct path for structured data
        return await async_create_document_chunks_for_structured_data(content, source, source_id)
    else:
        # Use the LLM cleaning path for unstructured data
        return await async_create_document_chunks_with_metadata(content, source, source_id, tenant_id)
