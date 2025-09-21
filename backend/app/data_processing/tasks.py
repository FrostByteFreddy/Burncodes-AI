import os
import asyncio
import re
import random
import tempfile
import httpx
from datetime import datetime, timezone
from urllib.parse import urlparse, urldefrag
from uuid import UUID

from celery import shared_task
from app.database.supabase_client import supabase, bucket_name
from app.data_processing.processor import get_vectorstore, get_loader, smart_chunk_markdown, process_documents, SUPPORTED_FILE_EXTENSIONS
from app.data_processing.crawler import shared_crawler
from app.data_processing.config import CRAWLER_RUN_CONFIG, MAX_CONCURRENT_CRAWLS_PER_JOB

# --- Crawl4AI Imports ---
from crawl4ai import CacheMode # CrawlerRunConfig is now imported from config

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
def process_s3_file(s3_path: str, source_filename: str, source_id: int, tenant_id: UUID):
    """Celery task to process a file stored in Supabase S3."""
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    docs = asyncio.run(async_process_s3_file(s3_path, source_filename, source_id))
    process_documents(docs, tenant_id, embeddings)
    # The temporary file is handled within async_process_s3_file, so no need to remove it here.

async def async_process_s3_file(s3_path: str, source_filename: str, source_id: int) -> list[Document]:
    """
    Downloads a file from S3, processes it into document chunks, and cleans up the temporary file.
    """
    ext = os.path.splitext(source_filename)[1].lower()
    tmp_filepath = None
    try:
        # Download file from S3
        file_content = supabase.storage.from_(bucket_name).download(s3_path)
        if file_content is None:
            raise FileNotFoundError(f"File not found in S3 at path: {s3_path}")

        # Create a temporary file to store the content
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
            tmp_file.write(file_content)
            tmp_filepath = tmp_file.name

        # Get the appropriate loader for the file extension
        loader = get_loader(tmp_filepath)
        if not loader:
            print(f"⚠️ No loader found for extension {ext}, skipping file {source_filename}")
            return []

        # Load and process the document
        docs_from_loader = loader.load()
        if not docs_from_loader:
            return []

        content = docs_from_loader[0].page_content
        return await _get_document_chunks_from_content(content, source_filename, source_id, ext)

    except Exception as e:
        print(f"❌ Error processing S3 file {s3_path}: {e}")
        # Mark the source as errored
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, lambda: supabase.table('tenant_sources').update({"status": "ERROR"}).eq('id', source_id).execute())
        return []
    finally:
        # Clean up the temporary file
        if tmp_filepath and os.path.exists(tmp_filepath):
            os.remove(tmp_filepath)
        # Clean up the S3 file after processing, regardless of success or failure
        # try:
        #     supabase.storage.from_(bucket_name).remove([s3_path])
        # except Exception as e:
        #     print(f"Failed to remove S3 file {s3_path} after processing: {e}")

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
    """Crawls URLs and processes their content concurrently using the shared crawler."""
    all_docs = []
    semaphore = asyncio.Semaphore(10)

    async def process_single_result(result, source_id):
        async with semaphore:
            if result.success and result.markdown:
                return await async_create_document_chunks_with_metadata(result.markdown, result.url, source_id)
        return []

    # Use the shared crawler instance
    url_to_source_id = {url: source_id for url, source_id in urls_to_process}
    results = await shared_crawler.arun_many(urls=list(url_to_source_id.keys()), config=CRAWLER_RUN_CONFIG)

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

from app.models.database import CrawlingStatus

def normalize_url(url):
    """Normalizes a URL by removing fragment and trailing slash."""
    return urldefrag(url)[0].rstrip('/')

@shared_task(bind=True)
def crawl_links_task(self, tenant_id: UUID, start_url: str, max_depth: int = 3):
    """
    Orchestrator Celery task to initiate a distributed web crawl.
    Creates a CrawlingJob and the first CrawlingTask.
    """
    try:
        start_url = normalize_url(start_url)
        job_data = {
            "tenant_id": str(tenant_id),
            "start_url": start_url,
            "max_depth": max_depth,
            "status": CrawlingStatus.IN_PROGRESS.value
        }
        job_response = supabase.table('crawling_jobs').insert(job_data).execute()
        job = job_response.data[0]
        job_id = job['id']

        self.update_state(state='PROGRESS', meta={'job_id': job_id, 'status': 'Job created'})

        task_data = {
            "job_id": job_id,
            "url": start_url,
            "depth": 1,
            "status": CrawlingStatus.PENDING.value
        }
        task_response = supabase.table('crawling_tasks').insert(task_data).execute()
        task = task_response.data[0]
        task_id = task['id']

        process_single_url_task.delay(task_id=task_id, tenant_id=tenant_id)

        return {'status': 'Crawl initiated', 'job_id': job_id}

    except Exception as e:
        error_message = f"Failed to initiate crawl: {e}"
        print(error_message)
        if 'job_id' in locals():
            supabase.table('crawling_jobs').update({"status": CrawlingStatus.FAILED.value}).eq('id', job_id).execute()
        self.update_state(state='FAILURE', meta={'status': error_message})
        raise e

@shared_task(bind=True, time_limit=300) # 5-minute hard time limit
def process_single_url_task(self, task_id: int, tenant_id: UUID, parent_url: str = None):
    """
    Worker Celery task to crawl a single URL, process its content, and discover new links.
    """
    task_details = {}
    try:
        task_response = supabase.table('crawling_tasks').select('*, crawling_jobs(*)').eq('id', task_id).single().execute()
        task_details = task_response.data
        if not task_details:
            raise Exception(f"Task with id {task_id} not found.")

        job = task_details['crawling_jobs']
        url = task_details['url']
        depth = task_details['depth']
        max_depth = job['max_depth']

        supabase.table('crawling_tasks').update({"status": CrawlingStatus.IN_PROGRESS.value}).eq('id', task_id).execute()
        print(f"Crawling URL: {url} at depth {depth}")

        # The user agent is randomized by the BrowserConfig.
        # We dynamically add the Referer header for each request if a parent URL exists.
        headers = {}
        if parent_url:
            headers["Referer"] = parent_url

        # --- Step 1: Crawl the page with a specific timeout ---
        async def crawl_page_only():
            # Pass the dynamic headers directly to the arun method.
            return await shared_crawler.arun(url=url, config=CRAWLER_RUN_CONFIG, headers=headers)

        crawl_result = None
        try:
            # Use asyncio.wait_for to enforce a timeout on the crawl
            crawl_result = asyncio.run(asyncio.wait_for(crawl_page_only(), timeout=60.0))
        except asyncio.TimeoutError:
            print(f"❌ Timeout loading page {url}")
            supabase.table('crawling_tasks').update({"status": CrawlingStatus.FAILED.value}).eq('id', task_id).execute()
            return

        # --- Step 2: Process the content (outside the page load timeout) ---
        found_links = set()
        if crawl_result and crawl_result.success and crawl_result.markdown:
            source_data = {
                "tenant_id": str(tenant_id),
                "source_type": "URL",
                "source_location": url,
                "status": "PROCESSING"
            }
            source_response = supabase.table('tenant_sources').insert(source_data).execute()
            source_id = source_response.data[0]['id']

            # This part can take a long time, especially the LLM call
            docs = asyncio.run(async_create_document_chunks_with_metadata(crawl_result.markdown, crawl_result.url, source_id))
            embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
            process_documents(docs, tenant_id, embeddings)

            for link in crawl_result.links.get("internal", []):
                found_links.add(normalize_url(link["href"]))

        # --- Step 3: Discover and save new links ---
        if depth < max_depth:
            existing_urls_response = supabase.table('crawling_tasks').select('url').eq('job_id', job['id']).execute()
            existing_urls = {item['url'] for item in existing_urls_response.data}
            new_unique_links = found_links - existing_urls

            if new_unique_links:
                new_tasks_data = [
                    {
                        "job_id": job['id'],
                        "url": link,
                        "depth": depth + 1,
                        "status": CrawlingStatus.PENDING.value,
                        "parent_url": url  # Add the current URL as the parent
                    }
                    for link in new_unique_links
                ]
                supabase.table('crawling_tasks').insert(new_tasks_data).execute()

        supabase.table('crawling_tasks').update({"status": CrawlingStatus.COMPLETED.value}).eq('id', task_id).execute()
        print(f"✅ Completed processing URL: {url}")

    except Exception as e:
        error_message = f"Error processing URL {task_details.get('url', 'unknown')}: {e}"
        print(f"❌ {error_message}")
        supabase.table('crawling_tasks').update({"status": CrawlingStatus.FAILED.value}).eq('id', task_id).execute()

@shared_task(bind=True)
def job_scheduler_task(self):
    """
    Periodic task to schedule new crawling tasks and check for job completion.
    This task acts as a central orchestrator to control concurrency per job.
    """
    try:
        in_progress_jobs_response = supabase.table('crawling_jobs').select('*').eq('status', CrawlingStatus.IN_PROGRESS.value).execute()
        in_progress_jobs = in_progress_jobs_response.data

        for job in in_progress_jobs:
            job_id = job['id']
            tenant_id = job['tenant_id']

            # Count currently running tasks for this job
            running_tasks_response = supabase.table('crawling_tasks').select('id', count='exact').eq('job_id', job_id).eq('status', CrawlingStatus.IN_PROGRESS.value).execute()
            running_tasks_count = running_tasks_response.count

            # --- Job Completion Check ---
            # If no tasks are currently running, check if there are any pending tasks left.
            if running_tasks_count == 0:
                pending_tasks_response = supabase.table('crawling_tasks').select('id', count='exact').eq('job_id', job_id).eq('status', CrawlingStatus.PENDING.value).execute()
                if pending_tasks_response.count == 0:
                    print(f"🎉 Job {job_id} has no more running or pending tasks. Marking as completed.")
                    supabase.table('crawling_jobs').update({"status": CrawlingStatus.COMPLETED.value}).eq('id', job_id).execute()
                    continue  # Proceed to the next job

            # --- New Task Scheduling ---
            # If the number of running tasks is below the concurrency limit, enqueue more.
            if running_tasks_count < MAX_CONCURRENT_CRAWLS_PER_JOB:
                # Calculate how many new tasks we can schedule
                limit = MAX_CONCURRENT_CRAWLS_PER_JOB - running_tasks_count

                # Fetch pending tasks to schedule
                tasks_to_schedule_response = supabase.table('crawling_tasks').select('*').eq('job_id', job_id).eq('status', CrawlingStatus.PENDING.value).limit(limit).execute()
                tasks_to_schedule = tasks_to_schedule_response.data

                for task in tasks_to_schedule:
                    print(f"Scheduler: Enqueuing task {task['id']} for job {job_id}.")
                    process_single_url_task.delay(
                        task_id=task['id'],
                        tenant_id=tenant_id,
                        parent_url=task.get('parent_url')  # Pass the parent_url
                    )

    except Exception as e:
        print(f"Error in job_scheduler_task: {e}")
