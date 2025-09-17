import os
import asyncio
import re
import tempfile
import httpx
from datetime import datetime, timezone
from urllib.parse import urlparse, urldefrag
from uuid import UUID

from celery import shared_task
from app.database.supabase_client import supabase
from app.data_processing.processor import get_vectorstore, get_loader, smart_chunk_markdown, process_documents, SUPPORTED_FILE_EXTENSIONS

# --- Crawl4AI Imports ---
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

# --- LangChain Core Imports ---
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.prompts import PromptTemplate

DEBUG = os.getenv("DEBUG", "False").lower() == "true"
QUERY_GEMINI_MODEL = os.getenv("QUERY_GEMINI_MODEL", "gemini-1.5-flash")
CLEANUP_PROMPT_TEMPLATE = """
You are an expert data pre-processor. Your task is to clean and reformat raw markdown text extracted from a website so it is optimized for a Retrieval-Augmented Generation (RAG) system's vector database.

Follow these rules precisely:
1.  **Preserve Core Content:** Keep all meaningful paragraphs, headings, lists, and factual information.
2.  **Keep Important Links:** Preserve important inline markdown links `[like this](...)` that are part of a sentence's context.
3.  **Remove Noise:** Delete all of the following:
    * Repetitive navigation bars, headers, and footers.
    * Advertisements and promotional banners.
    * Cookie consent notices and legal disclaimers (e.g., Impressum, Datenschutz, AGB).
    * Image tags `![...](...)` and social media links.
    * Boilerplate text that doesn't add unique value.
4.  **Format Cleanly:** Ensure the output is clean, well-structured markdown with proper spacing. Do not add any commentary or explanation. Only output the cleaned markdown.

Here is the raw markdown text:
---
{raw_markdown}
---
"""

async def async_clean_markdown_with_llm(markdown_text: str) -> str:
    """Uses an LLM to clean and optimize raw markdown asynchronously."""
    print(f"🤖 Calling LLM to clean markdown ({len(markdown_text)} chars)...")
    cleanup_llm = ChatGoogleGenerativeAI(model=QUERY_GEMINI_MODEL, temperature=0.0)
    cleanup_prompt = PromptTemplate.from_template(CLEANUP_PROMPT_TEMPLATE)
    cleanup_chain = cleanup_prompt | cleanup_llm
    response = await cleanup_chain.ainvoke({"raw_markdown": markdown_text})
    print("✅ Markdown cleaned successfully.")
    return response.content

async def async_create_document_chunks_with_metadata(content: str, source: str, source_id: int) -> list[Document]:
    """Asynchronously cleans, chunks, and creates Document objects with metadata."""
    documents = []
    loop = asyncio.get_running_loop()
    try:
        await loop.run_in_executor(None, lambda: supabase.table('tenant_sources').update({"status": "PROCESSING"}).eq('id', source_id).execute())

        clean_content = await async_clean_markdown_with_llm(content)

        if DEBUG:
            try:
                os.makedirs('crawled_markdown', exist_ok=True)
                safe_filename = re.sub(r'https://?|www\.|\/|\?|\=|\&', '_', source) + ".md"
                filepath = os.path.join('crawled_markdown', safe_filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"# SOURCE: {source}\n\n{clean_content}")
                print(f"🕵️‍♂️ Saved CLEANED markdown for {source} to {filepath}")
            except Exception as e:
                print(f"❌ Could not save cleaned markdown file for {source}: {e}")

        chunks = smart_chunk_markdown(clean_content, max_len=1000)
        timestamp = datetime.now(timezone.utc).isoformat()
        for i, chunk in enumerate(chunks):
            doc = Document(
                page_content=chunk,
                metadata={"source": source, "source_id": source_id, "chunk": i, "last_updated": timestamp}
            )
            documents.append(doc)

        await loop.run_in_executor(None, lambda: supabase.table('tenant_sources').update({"status": "COMPLETED"}).eq('id', source_id).execute())
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

        # Directly chunk the raw content
        chunks = smart_chunk_markdown(content, max_len=1000)
        timestamp = datetime.now(timezone.utc).isoformat()
        for i, chunk in enumerate(chunks):
            doc = Document(
                page_content=chunk,
                metadata={"source": source, "source_id": source_id, "chunk": i, "last_updated": timestamp}
            )
            documents.append(doc)

        await loop.run_in_executor(None, lambda: supabase.table('tenant_sources').update({"status": "COMPLETED"}).eq('id', source_id).execute())
        print(f"✅ Created {len(documents)} chunks for structured file {source} (source_id: {source_id})")
        return documents
    except Exception as e:
        print(f"Error creating document chunks for structured source {source_id}: {e}")
        await loop.run_in_executor(None, lambda: supabase.table('tenant_sources').update({"status": "ERROR"}).eq('id', source_id).execute())
        return []

async def _get_document_chunks_from_content(content: str, source: str, source_id: int, ext: str) -> list[Document]:
    """Internal helper to decide which chunking strategy to use based on file extension."""
    structured_extensions = ['.csv', '.ics']
    if ext in structured_extensions:
        # Use the direct path for structured data
        return await async_create_document_chunks_for_structured_data(content, source, source_id)
    else:
        # Use the LLM cleaning path for unstructured data
        return await async_create_document_chunks_with_metadata(content, source, source_id)

@shared_task
def process_local_filepath(filepath: str, source_filename: str, source_id: int, tenant_id: UUID):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    docs = asyncio.run(async_process_local_filepath(filepath, source_filename, source_id))
    process_documents(docs, tenant_id, embeddings)
    os.remove(filepath)


async def async_process_local_filepath(filepath: str, source_filename: str, source_id: int) -> list[Document]:
    """Loads a local file and processes it into document chunks."""
    ext = os.path.splitext(source_filename)[1].lower()
    loader = get_loader(filepath)
    if not loader:
        print(f"⚠️ No loader found for extension {ext}, skipping file {source_filename}")
        return []

    docs_from_loader = loader.load()
    if not docs_from_loader:
        return []

    content = docs_from_loader[0].page_content
    return await _get_document_chunks_from_content(content, source_filename, source_id, ext)

@shared_task
def process_urls(urls: list[tuple[str, int]], tenant_id: UUID):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    docs = asyncio.run(process_urls_concurrently(urls, tenant_id))
    process_documents(docs, tenant_id, embeddings)

async def process_urls_concurrently(urls: list[tuple[str, int]], tenant_id: UUID) -> list[Document]:
    urls_to_crawl = []
    file_urls_to_process = []

    for url, source_id in urls:
        ext = os.path.splitext(urlparse(url).path)[1].lower()
        if ext in SUPPORTED_FILE_EXTENSIONS:
            file_urls_to_process.append((url, source_id))
        else:
            urls_to_crawl.append((url, source_id))

    tasks = []
    if urls_to_crawl:
        tasks.append(async_crawl_urls_for_content(urls_to_crawl))

    for file_url, source_id in file_urls_to_process:
        tasks.append(async_process_file_url(file_url, tenant_id, source_id))

    results = await asyncio.gather(*tasks)

    all_docs = []
    for result_list in results:
        all_docs.extend(result_list)

    return all_docs

async def async_crawl_urls_for_content(urls_to_process: list[tuple[str, int]]) -> list[Document]:
    """Crawls URLs and processes their content concurrently."""
    browser_config = BrowserConfig(headless=True, verbose=False)
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, stream=False)
    all_docs = []

    semaphore = asyncio.Semaphore(10)

    async def process_single_result(result, source_id):
        async with semaphore:
            if result.success and result.markdown:
                return await async_create_document_chunks_with_metadata(result.markdown, result.url, source_id)
        return []

    async with AsyncWebCrawler(config=browser_config) as crawler:
        url_to_source_id = {url: source_id for url, source_id in urls_to_process}
        results = await crawler.arun_many(urls=list(url_to_source_id.keys()), config=run_config)
        tasks = [process_single_result(result, url_to_source_id[result.url]) for result in results]
        processed_chunks_list = await asyncio.gather(*tasks)
        for doc_list in processed_chunks_list:
            all_docs.extend(doc_list)

    return all_docs

async def async_process_file_url(url: str, tenant_id: UUID, source_id: int) -> list[Document]:
    """Downloads a file from a URL and processes its content."""
    print(f"📄 Downloading and processing file: {url}")
    ext = os.path.splitext(urlparse(url).path)[1].lower()
    if not ext: return []

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, follow_redirects=True, timeout=60.0)
            response.raise_for_status()

        tenant_upload_path = os.path.join('uploads', str(tenant_id))
        os.makedirs(tenant_upload_path, exist_ok=True)

        with tempfile.NamedTemporaryFile(delete=False, suffix=ext, dir=tenant_upload_path) as tmp_file:
            tmp_file.write(response.content)
            tmp_filepath = tmp_file.name

        loader = get_loader(tmp_filepath)
        if not loader:
            print(f"⚠️ No loader found for extension {ext}, skipping file {url}")
            os.remove(tmp_filepath)
            return []

        docs_from_loader = loader.load()
        os.remove(tmp_filepath)

        if not docs_from_loader: return []

        content = docs_from_loader[0].page_content
        return await _get_document_chunks_from_content(content, url, source_id, ext)

    except Exception as e:
        print(f"❌ Error processing file URL {url}: {e}")
        if 'tmp_filepath' in locals() and os.path.exists(tmp_filepath):
            os.remove(tmp_filepath)
        return []

@shared_task
def crawl_links_task(start_url: str, max_depth: int = 3):
    return asyncio.run(crawl_recursive_for_links(start_url, max_depth))

async def crawl_recursive_for_links(start_url: str, max_depth: int = 3):
    """
    Uses crawl4ai to recursively discover all internal links from a starting URL,
    categorized by depth.
    """
    browser_config = BrowserConfig(headless=True, verbose=False)
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, stream=False)

    all_found_urls = set()
    links_by_depth = []

    def normalize_url(url):
        return urldefrag(url)[0].rstrip('/')

    current_urls_to_crawl = {normalize_url(start_url)}
    all_found_urls.add(normalize_url(start_url))

    async with AsyncWebCrawler(config=browser_config) as crawler:
        for depth in range(max_depth):
            if not current_urls_to_crawl:
                break

            print(f"Crawling depth {depth + 1} with {len(current_urls_to_crawl)} URLs...")

            depth_links = list(current_urls_to_crawl)
            links_by_depth.append(depth_links)

            results = await crawler.arun_many(urls=depth_links, config=run_config)

            next_level_urls = set()
            for result in results:
                if result.success:
                    for link in result.links.get("internal", []):
                        normalized_link = normalize_url(link["href"])
                        if normalized_link not in all_found_urls:
                            next_level_urls.add(normalized_link)
                            all_found_urls.add(normalized_link)

            current_urls_to_crawl = next_level_urls

    return links_by_depth
