import os
import asyncio
import re
import tempfile
import shutil
import chromadb
import httpx
from datetime import datetime, timezone
from urllib.parse import urlparse, urldefrag
from uuid import UUID

# --- Crawl4AI & ChromaDB Imports ---
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from langchain_community.vectorstores import Chroma

# --- LangChain Core Imports ---
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader, CSVLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document

from app.database.supabase_client import supabase

# --- CONFIGURATION ---
UPLOAD_FOLDER_BASE = 'uploads'
VECTOR_STORE_PATH_BASE = 'chromadb'
os.makedirs(UPLOAD_FOLDER_BASE, exist_ok=True)
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

# --- DOCUMENT LOADERS ---
SUPPORTED_FILE_EXTENSIONS = ['.pdf', '.docx', '.txt', '.csv']
def get_loader(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.pdf': return PyPDFLoader(filepath)
    elif ext == '.docx': return Docx2txtLoader(filepath)
    elif ext == '.txt': return TextLoader(filepath, encoding='utf-8')
    elif ext == '.csv': return CSVLoader(filepath, encoding='utf-8')
    return None

# --- ASYNC CHROMA & CRAWLING HELPERS ---
def get_vectorstore(tenant_id: UUID):
    """Initializes and returns a tenant-specific Chroma vector store instance."""
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    tenant_id_str = str(tenant_id)
    tenant_db_path = os.path.join(VECTOR_STORE_PATH_BASE, tenant_id_str)

    client_settings = chromadb.Settings(
        is_persistent=True,
        persist_directory=tenant_db_path,
        anonymized_telemetry=False
    )
    vectorstore = Chroma(
        collection_name=f"content_{tenant_id_str}",
        embedding_function=embeddings,
        client_settings=client_settings,
        persist_directory=tenant_db_path
    )
    print(f"✅ ChromaDB vector store initialized for tenant: {tenant_id_str}")
    return vectorstore

async def async_clean_markdown_with_llm(markdown_text: str) -> str:
    """Uses an LLM to clean and optimize raw markdown asynchronously."""
    print(f"🤖 Calling LLM to clean markdown ({len(markdown_text)} chars)...")
    cleanup_llm = ChatGoogleGenerativeAI(model=QUERY_GEMINI_MODEL, temperature=0.0)
    cleanup_prompt = PromptTemplate.from_template(CLEANUP_PROMPT_TEMPLATE)
    cleanup_chain = cleanup_prompt | cleanup_llm
    response = await cleanup_chain.ainvoke({"raw_markdown": markdown_text})
    print("✅ Markdown cleaned successfully.")
    return response.content

def smart_chunk_markdown(markdown: str, max_len: int = 1000) -> list[str]:
    def split_by_header(md, header_pattern):
        indices = [m.start() for m in re.finditer(header_pattern, md, re.MULTILINE)]
        indices.append(len(md))
        return [md[indices[i]:indices[i+1]].strip() for i in range(len(indices)-1) if md[indices[i]:indices[i+1]].strip()]
    chunks = []
    h1_split = split_by_header(markdown, r'^# .+$')
    if not h1_split: h1_split = [markdown]
    for h1 in h1_split:
        if len(h1) > max_len:
            h2_split = split_by_header(h1, r'^## .+$')
            if not h2_split: h2_split = [h1]
            for h2 in h2_split:
                if len(h2) > max_len:
                    h3_split = split_by_header(h2, r'^### .+$')
                    if not h3_split: h3_split = [h2]
                    for h3 in h3_split:
                        if len(h3) > max_len:
                            for i in range(0, len(h3), max_len): chunks.append(h3[i:i+max_len].strip())
                        else: chunks.append(h3)
                else: chunks.append(h2)
        else: chunks.append(h1)
    final_chunks = [c for c in chunks if c and len(c) <= max_len]
    return final_chunks

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


def process_documents(docs: list[Document], tenant_id: UUID):
    if not docs:
        print("No documents to process")
        return
    db = get_vectorstore(tenant_id)
    db.add_documents(docs)
    print(f"✅ Added {len(docs)} document chunks to ChromaDB for tenant: {tenant_id}.")

async def async_process_file_url(url: str, tenant_id: UUID, source_id: int) -> list[Document]:
    """Downloads a file from a URL and processes its content."""
    print(f"📄 Downloading and processing file: {url}")
    ext = os.path.splitext(urlparse(url).path)[1].lower()
    if not ext: return []

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, follow_redirects=True, timeout=60.0)
            response.raise_for_status()

        tenant_upload_path = os.path.join(UPLOAD_FOLDER_BASE, str(tenant_id))
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
        return await async_create_document_chunks_with_metadata(content, url, source_id)

    except Exception as e:
        print(f"❌ Error processing file URL {url}: {e}")
        if 'tmp_filepath' in locals() and os.path.exists(tmp_filepath):
            os.remove(tmp_filepath)
        return []

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
        # Create a dictionary to map URL to source_id
        url_to_source_id = {url: source_id for url, source_id in urls_to_process}

        results = await crawler.arun_many(urls=list(url_to_source_id.keys()), config=run_config)

        tasks = [process_single_result(result, url_to_source_id[result.url]) for result in results]
        processed_chunks_list = await asyncio.gather(*tasks)

        for doc_list in processed_chunks_list:
            all_docs.extend(doc_list)

    return all_docs

async def crawl_recursive_for_links(start_url: str, max_depth: int = 4):
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

            # Add current level's URLs to the results
            depth_links = list(current_urls_to_crawl)
            links_by_depth.append(depth_links)

            # Crawl and find links for the next level
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
