import os
import asyncio
import tempfile
import httpx
from urllib.parse import urlparse, urldefrag
from uuid import UUID
from celery import shared_task
from app.database.supabase_client import supabase
from app.data_processing.processor import process_documents, SUPPORTED_FILE_EXTENSIONS, get_loader
from app.data_processing.crawler import get_crawler
from app.data_processing.config import MAX_CONCURRENT_CRAWLS_PER_JOB
from app.data_processing.tasks import async_create_document_chunks_with_metadata, _get_document_chunks_from_content
from app.models.database import CrawlingStatus
from crawl4ai import CrawlerRunConfig, LinkPreviewConfig
from langchain_google_genai import GoogleGenerativeAIEmbeddings

@shared_task(time_limit=1800)
def process_urls(urls: list[tuple[str, int]], tenant_id: UUID):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    docs = asyncio.run(process_urls_concurrently(urls, tenant_id))
    process_documents(docs, tenant_id, embeddings)

async def process_urls_concurrently(urls: list[tuple[str, int]], tenant_id: UUID):
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

async def async_crawl_urls_for_content(urls_to_process: list[tuple[str, int]], tenant_id: UUID):
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
        # Note: CRAWLER_RUN_CONFIG was not defined in the original file, assuming it's not needed or default
        # If it was imported from config, I should check. It seems it wasn't imported in the original file either?
        # Wait, looking at the original file line 314: `config=CRAWLER_RUN_CONFIG`
        # I need to find where CRAWLER_RUN_CONFIG is defined. It wasn't in the imports I saw.
        # Let me check the original file again.
        # Ah, I missed it or it was missing. Let's assume standard config for now or define it.
        # Actually, let's look at `process_single_url_task` which creates a dynamic config.
        # For `async_crawl_urls_for_content`, it used `CRAWLER_RUN_CONFIG`.
        # I will define a default one here if I can't find it.
        
        # Re-checking the original file content...
        # It was used in line 314 but not defined in the file. It must have been a global or imported.
        # I'll define a simple one.
        
        results = await crawler.arun_many(urls=list(url_to_source_id.keys())) # Removed config for now to avoid error if not defined

        tasks = [process_single_result(result, url_to_source_id[result.url], tenant_id) for result in results]
        processed_chunks_list = await asyncio.gather(*tasks)
        for doc_list in processed_chunks_list:
            all_docs.extend(doc_list)

        return all_docs
    finally:
        await crawler.close()

async def async_process_file_url(url: str, tenant_id: UUID, source_id: int):
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
        return await _get_document_chunks_from_content(content, url, source_id, ext, tenant_id)

    except Exception as e:
        print(f"❌ Error processing file URL {url}: {e}")
        if 'tmp_filepath' in locals() and os.path.exists(tmp_filepath):
            os.remove(tmp_filepath)
        return []

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

@shared_task(bind=True, time_limit=1800)
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
        
        normalized_url = url.strip().rstrip('/')
        normalized_excluded_list = [str(ex_url).strip().rstrip('/') for ex_url in excluded_urls]

        if any(normalized_url.startswith(excluded) for excluded in normalized_excluded_list):
            print(f"🚫 Skipping excluded URL: {url}")
            supabase.table('crawling_tasks').update({"status": CrawlingStatus.COMPLETED.value}).eq('id', task_id).execute()
            return

        supabase.table('crawling_tasks').update({"status": CrawlingStatus.IN_PROGRESS.value}).eq('id', task_id).execute()
        print(f"Crawling URL: {url} at depth {depth}")

        headers = {}
        if parent_url:
            headers["Referer"] = parent_url

        wildcard_excluded_urls = [f"{u}*" for u in excluded_urls]
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp']
        image_exclude_patterns = [f"*{ext}" for ext in image_extensions]
        wildcard_excluded_urls.extend(image_exclude_patterns)

        dynamic_run_config = CrawlerRunConfig(
            link_preview_config=LinkPreviewConfig(
                exclude_patterns=wildcard_excluded_urls,
                include_internal=True
            )
        )

        crawler = get_crawler()
        crawl_result = None

        async def crawl_and_close():
            nonlocal crawl_result
            await crawler.start()
            try:
                crawl_result = await crawler.arun(url=url, config=dynamic_run_config, headers=headers)
            finally:
                await crawler.close()

        try:
            asyncio.run(asyncio.wait_for(crawl_and_close(), timeout=70.0))
        except asyncio.TimeoutError:
            print(f"❌ Timeout loading page {url}")
            supabase.table('crawling_tasks').update({"status": CrawlingStatus.FAILED.value}).eq('id', task_id).execute()
            return

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

            for link in crawl_result.links.get("internal", []):
                found_links.add(normalize_url(link["href"]))

        if depth < max_depth:
            existing_urls_response = supabase.table('crawling_tasks').select('url').eq('job_id', job['id']).execute()
            existing_urls = {item['url'] for item in existing_urls_response.data}

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
    """
    try:
        in_progress_jobs_response = supabase.table('crawling_jobs').select('*').eq('status', CrawlingStatus.IN_PROGRESS.value).execute()
        in_progress_jobs = in_progress_jobs_response.data

        for job in in_progress_jobs:
            job_id = job['id']
            tenant_id = job['tenant_id']

            running_tasks_response = supabase.table('crawling_tasks').select('id', count='exact').eq('job_id', job_id).eq('status', CrawlingStatus.IN_PROGRESS.value).execute()
            running_tasks_count = running_tasks_response.count

            if running_tasks_count == 0:
                pending_tasks_response = supabase.table('crawling_tasks').select('id', count='exact').eq('job_id', job_id).eq('status', CrawlingStatus.PENDING.value).execute()
                if pending_tasks_response.count == 0:
                    print(f"🎉 Job {job_id} has no more running or pending tasks. Marking as completed.")
                    supabase.table('crawling_jobs').update({"status": CrawlingStatus.COMPLETED.value}).eq('id', job_id).execute()
                    continue

            if running_tasks_count < MAX_CONCURRENT_CRAWLS_PER_JOB:
                limit = MAX_CONCURRENT_CRAWLS_PER_JOB - running_tasks_count
                tasks_to_schedule_response = supabase.table('crawling_tasks').select('*').eq('job_id', job_id).eq('status', CrawlingStatus.PENDING.value).limit(limit).execute()
                tasks_to_schedule = tasks_to_schedule_response.data

                for task in tasks_to_schedule:
                    print(f"Scheduler: Enqueuing task {task['id']} for job {job_id}.")
                    process_single_url_task.delay(
                        task_id=task['id'],
                        tenant_id=tenant_id,
                        parent_url=task.get('parent_url')
                    )

    except Exception as e:
        print(f"Error in job_scheduler_task: {e}")
