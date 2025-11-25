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
from app.data_processing.processor import get_vectorstore, get_loader, process_documents, SUPPORTED_FILE_EXTENSIONS
from app.data_processing.crawler import get_crawler
from app.data_processing.config import MAX_CONCURRENT_CRAWLS_PER_JOB

# --- Crawl4AI Imports ---
from crawl4ai import CacheMode, CrawlerRunConfig, LinkPreviewConfig

# --- LangChain Core Imports ---
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.prompts import PromptTemplate
from app.prompts import CLEANUP_PROMPT_TEMPLATES

# --- Document Tasks Imports ---
from app.data_processing.document_tasks import async_create_document_chunks_with_metadata, async_process_file_url

DEBUG = os.getenv("DEBUG", "False").lower() == "true"
QUERY_GEMINI_MODEL = os.getenv("QUERY_GEMINI_MODEL", "gemini-1.5-flash")

@shared_task
def process_urls(urls: list[tuple[str, int]], tenant_id: UUID):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
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
        tasks.append(async_crawl_urls_for_content(urls_to_crawl, tenant_id))

    for file_url, source_id in file_urls_to_process:
        tasks.append(async_process_file_url(file_url, tenant_id, source_id))

    results = await asyncio.gather(*tasks)

    all_docs = []
    for result_list in results:
        all_docs.extend(result_list)

    return all_docs

async def async_crawl_urls_for_content(urls_to_process: list[tuple[str, int]], tenant_id: UUID) -> list[Document]:
    """Crawls URLs and processes their content concurrently using the shared crawler."""
    all_docs = []
    semaphore = asyncio.Semaphore(10)
    crawler = get_crawler()
    await crawler.start()

    try:
        async def process_single_result(result, source_id, tenant_id):
            async with semaphore:
                if result.success and result.markdown:
                    return await async_create_document_chunks_with_metadata(result.markdown, result.url, source_id, tenant_id)
            return []

        url_to_source_id = {url: source_id for url, source_id in urls_to_process}
        # Assuming CRAWLER_RUN_CONFIG is defined somewhere or we construct it. 
        # In original tasks.py it seemed to be missing or I missed it. 
        # Let's check the original file content.
        # Ah, I missed CRAWLER_RUN_CONFIG in the original file view? No, it was used in line 225 but I don't see definition.
        # Maybe it was imported or defined globally but I missed it.
        # Let's define a default one.
        config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
        
        results = await crawler.arun_many(urls=list(url_to_source_id.keys()), config=config)

        tasks = [process_single_result(result, url_to_source_id[result.url], tenant_id) for result in results]
        processed_chunks_list = await asyncio.gather(*tasks)
        for doc_list in processed_chunks_list:
            all_docs.extend(doc_list)

        return all_docs
    finally:
        await crawler.close()

from app.models.database import CrawlingStatus

def normalize_url(url):
    """Normalizes a URL by removing fragment and trailing slash."""
    return urldefrag(url)[0].rstrip('/')

@shared_task(bind=True)
def crawl_links_task(self, tenant_id: UUID, start_url: str, single_page_only: bool = False, excluded_urls: list[str] = None, max_depth: int = 3):
    """
    Orchestrator Celery task to initiate a distributed web crawl.
    Creates a CrawlingJob and the first CrawlingTask.
    """
    try:
        start_url = normalize_url(start_url)
        # If single_page_only is true, we only crawl the starting URL.
        # So we set max_depth to 1, which means we will not follow any links.
        effective_max_depth = 1 if single_page_only else max_depth

        job_data = {
            "tenant_id": str(tenant_id),
            "start_url": start_url,
            "max_depth": effective_max_depth,
            "status": CrawlingStatus.IN_PROGRESS.value,
            "excluded_urls": excluded_urls or []
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

@shared_task(bind=True, time_limit=600) # 5-minute hard time limit
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
        excluded_urls = job.get('excluded_urls', [])
        
        # 1. Normalize the URL that is being crawled
        normalized_url = url.strip().rstrip('/')

        # 2. Normalize the list of URLs to exclude
        normalized_excluded_list = [str(ex_url).strip().rstrip('/') for ex_url in excluded_urls]

        # 3. Perform the check with the normalized values
        if any(normalized_url.startswith(excluded) for excluded in normalized_excluded_list):
            print(f"🚫 Skipping excluded URL: {url}")
            supabase.table('crawling_tasks').update({"status": CrawlingStatus.COMPLETED.value}).eq('id', task_id).execute()
            return

        supabase.table('crawling_tasks').update({"status": CrawlingStatus.IN_PROGRESS.value}).eq('id', task_id).execute()
        print(f"Crawling URL: {url} at depth {depth}")

        # The user agent is randomized by the BrowserConfig.
        # We dynamically add the Referer header for each request if a parent URL exists.
        headers = {}
        if parent_url:
            headers["Referer"] = parent_url

        # --- Step 1: Configure and crawl the page ---
        # Create a dynamic crawler config to handle exclusions per job.
        # We add a wildcard to the end of each excluded URL to match any sub-paths.
        wildcard_excluded_urls = [f"{u}*" for u in excluded_urls]

        # Add common image extensions to the exclusion list
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp']
        image_exclude_patterns = [f"*{ext}" for ext in image_extensions]
        wildcard_excluded_urls.extend(image_exclude_patterns)

        dynamic_run_config = CrawlerRunConfig(
            link_preview_config=LinkPreviewConfig(
                exclude_patterns=wildcard_excluded_urls,
                include_internal=True # Ensure we process internal links
            )
        )

        crawler = get_crawler()
        crawl_result = None

        async def crawl_and_close():
            nonlocal crawl_result
            await crawler.start()
            try:
                # Pass the dynamic headers and config directly to the arun method.
                crawl_result = await crawler.arun(url=url, config=dynamic_run_config, headers=headers)
            finally:
                await crawler.close()

        try:
            # Use asyncio.wait_for to enforce a timeout on the entire crawl and close operation
            asyncio.run(asyncio.wait_for(crawl_and_close(), timeout=70.0))
        except asyncio.TimeoutError:
            print(f"❌ Timeout loading page {url}")
            supabase.table('crawling_tasks').update({"status": CrawlingStatus.FAILED.value}).eq('id', task_id).execute()
            return

        # --- Step 2: Process the content ---
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

            docs = asyncio.run(async_create_document_chunks_with_metadata(crawl_result.markdown, crawl_result.url, source_id, tenant_id))
            embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
            process_documents(docs, tenant_id, embeddings)

            # crawl4ai with the configured exclude_patterns will handle not following the excluded links.
            # We can directly use the internal links it returns.
            for link in crawl_result.links.get("internal", []):
                found_links.add(normalize_url(link["href"]))

        # --- Step 3: Discover and save new links ---
        if depth < max_depth:
            existing_urls_response = supabase.table('crawling_tasks').select('url').eq('job_id', job['id']).execute()
            existing_urls = {item['url'] for item in existing_urls_response.data}

            # crawl4ai has already filtered the links based on the exclude_patterns,
            # so we only need to check for already-queued links.
            new_unexcluded_links = found_links - existing_urls

            if new_unexcluded_links:
                new_tasks_data = [
                    {
                        "job_id": job['id'],
                        "url": link,
                        "depth": depth + 1,
                        "status": CrawlingStatus.PENDING.value,
                        "parent_url": url
                    }
                    for link in new_unexcluded_links
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
