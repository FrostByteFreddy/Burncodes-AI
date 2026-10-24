from flask import Blueprint, request, jsonify
from app.database.supabase_client import supabase
from app.auth.decorators import token_required
from app.models.database import SourceType
from app.data_processing.tasks import process_local_file, process_urls, crawl_links_task
from app.logging_config import error_logger
from app.billing.services import BillingService
from app.security.url_guard import is_public_url
from app import celery
from uuid import uuid4
from werkzeug.utils import secure_filename
import os

UPLOADS_DIR = os.environ.get("UPLOADS_DIR", "/app/data/uploads")

sources_bp = Blueprint('sources', __name__)


def _insufficient_balance(user_id):
    """Returns a 402 response if the user can't pay for indexing, else None."""
    if BillingService.check_balance(user_id) <= 0:
        return jsonify({"error": "Insufficient balance. Please recharge."}), 402
    return None


def _invalid_urls(urls):
    """Returns the subset of urls that must not be fetched (non-http(s) or non-public hosts)."""
    return [u for u in urls if not isinstance(u, str) or not is_public_url(u)]

@sources_bp.route('/<uuid:tenant_id>/sources', methods=['GET'])
@token_required
def get_sources(current_user, tenant_id):
    try:
        tenant_id_str = str(tenant_id)
        tenant_check = supabase.table('tenants').select("id").eq('id', tenant_id_str).eq('user_id', current_user.id).single().execute()
        if not tenant_check.data:
            return jsonify({"error": "Tenant not found or access denied"}), 404
        sources = supabase.table('tenant_sources').select("*").eq('tenant_id', tenant_id_str).execute()
        return jsonify(sources.data), 200
    except Exception as e:
        error_logger.error(f"Error getting sources for tenant {tenant_id} for user {current_user.id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to retrieve sources"}), 500

@sources_bp.route('/<uuid:tenant_id>/sources/upload', methods=['POST'])
@token_required
def upload_source(current_user, tenant_id):
    tenant_id_str = str(tenant_id)
    tenant_check = supabase.table('tenants').select("id").eq('id', tenant_id_str).eq('user_id', current_user.id).single().execute()
    if not tenant_check.data:
        return jsonify({"error": "Tenant not found or access denied"}), 404

    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if (resp := _insufficient_balance(current_user.id)):
        return resp

    # Save to local filesystem: /app/data/uploads/{tenant_id}/{uuid}_{filename}.
    # The client-supplied filename is never used as a path: secure_filename
    # strips separators and "..", the uuid prefix avoids collisions, and the
    # realpath check is a final guard against escaping the tenant directory.
    display_name = os.path.basename(file.filename.replace("\\", "/")) or "upload"
    safe_name = f"{uuid4().hex}_{secure_filename(display_name) or 'upload'}"
    tenant_upload_dir = os.path.join(UPLOADS_DIR, tenant_id_str)
    os.makedirs(tenant_upload_dir, exist_ok=True)
    local_path = os.path.join(tenant_upload_dir, safe_name)
    if not os.path.realpath(local_path).startswith(os.path.realpath(tenant_upload_dir) + os.sep):
        return jsonify({"error": "Invalid filename"}), 400

    try:
        file.save(local_path)

        source_data = {"tenant_id": tenant_id_str, "source_type": SourceType.FILE, "source_location": local_path, "status": "QUEUED"}
        source_record = supabase.table('tenant_sources').insert(source_data).execute()
        source_id = source_record.data[0]['id']

        task = process_local_file.delay(local_path, display_name, source_id, tenant_id_str)

        return jsonify({"task_id": task.id}), 202
    except Exception as e:
        error_logger.error(f"Error processing file upload for tenant {tenant_id_str}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        try:
            if os.path.exists(local_path):
                os.remove(local_path)
        except Exception as cleanup_e:
            error_logger.error(f"Failed to clean up file {local_path} after an error: {cleanup_e}", extra={'user_id': current_user.id})
        return jsonify({"error": "Failed to process file"}), 500

@sources_bp.route('/<uuid:tenant_id>/sources/crawl', methods=['POST'])
@token_required
def crawl_sources(current_user, tenant_id):
    try:
        data = request.get_json()
        urls = data.get('urls')
        tenant_id_str = str(tenant_id)
        if not urls or not isinstance(urls, list):
            return jsonify({"error": "A list of URLs is required"}), 400

        tenant_check = supabase.table('tenants').select("id").eq('id', tenant_id_str).eq('user_id', current_user.id).single().execute()
        if not tenant_check.data:
            return jsonify({"error": "Tenant not found or access denied"}), 404

        rejected = _invalid_urls(urls)
        if rejected:
            return jsonify({"error": "Only public http(s) URLs can be added", "rejected": rejected}), 400
        if (resp := _insufficient_balance(current_user.id)):
            return resp

        sources_to_insert = [{"tenant_id": tenant_id_str, "source_type": SourceType.URL, "source_location": url, "status": "QUEUED"} for url in urls]
        source_records = supabase.table('tenant_sources').insert(sources_to_insert).execute()
        urls_with_ids = [(rec['source_location'], rec['id']) for rec in source_records.data]

        task = process_urls.delay(urls_with_ids, tenant_id_str)

        return jsonify({"task_id": task.id}), 202
    except Exception as e:
        error_logger.error(f"Error processing crawl for tenant {tenant_id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to process URLs"}), 500

@sources_bp.route('/<uuid:tenant_id>/sources/discover', methods=['POST'])
@token_required
def discover_links(current_user, tenant_id):
    try:
        data = request.get_json()
        start_url = data.get('url')
        single_page_only = data.get('single_page_only', False)
        excluded_urls = data.get('excluded_urls', [])
        crawl_mode = data.get('crawl_mode', 'playwright_llm')
        tenant_id_str = str(tenant_id)

        if not start_url:
            return jsonify({"error": "URL is required"}), 400

        tenant_check = supabase.table('tenants').select("id").eq('id', tenant_id_str).eq('user_id', current_user.id).single().execute()
        if not tenant_check.data:
            return jsonify({"error": "Tenant not found or access denied"}), 404

        if _invalid_urls([start_url]):
            return jsonify({"error": "Only public http(s) URLs can be crawled"}), 400
        if (resp := _insufficient_balance(current_user.id)):
            return resp

        # Persist the selected crawl_mode so all worker tasks pick it up from the DB
        valid_modes = {'soup', 'playwright', 'playwright_llm'}
        if crawl_mode not in valid_modes:
            crawl_mode = 'playwright_llm'
        supabase.table('tenants').update({'crawl_mode': crawl_mode}).eq('id', tenant_id_str).execute()

        task = crawl_links_task.delay(
            tenant_id=tenant_id,
            start_url=start_url,
            single_page_only=single_page_only,
            excluded_urls=excluded_urls
        )

        return jsonify({"task_id": task.id}), 202
    except Exception as e:
        error_logger.error(f"Error discovering links for tenant {tenant_id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to discover links"}), 500

@sources_bp.route('/<uuid:tenant_id>/crawling_jobs', methods=['GET'])
@token_required
def get_crawling_jobs(current_user, tenant_id):
    try:
        from collections import defaultdict
        tenant_id_str = str(tenant_id)
        tenant_check = supabase.table('tenants').select("id").eq('id', tenant_id_str).eq('user_id', current_user.id).single().execute()
        if not tenant_check.data:
            return jsonify({"error": "Tenant not found or access denied"}), 404

        jobs_resp = supabase.table('crawling_jobs').select("*").eq('tenant_id', tenant_id_str).order('created_at', desc=True).execute()
        jobs = jobs_resp.data or []
        if not jobs:
            return jsonify([]), 200

        job_ids = [j['id'] for j in jobs]

        # Batch-fetch tasks — one query for all jobs
        # NOTE: Supabase default row limit is 1000 — raise it explicitly so large
        # crawls (3000+ pages) are not silently truncated in the job stats display.
        tasks_resp = supabase.table('crawling_tasks').select("job_id,url,status").in_('job_id', job_ids).limit(10000).execute()
        tasks_by_job = defaultdict(list)
        all_crawled_urls = set()
        for t in (tasks_resp.data or []):
            tasks_by_job[t['job_id']].append(t)
            all_crawled_urls.add(t['url'])

        # Batch-fetch matching tenant_sources — fetch all for this tenant, filter in Python
        # (avoids httpx "URL component 'query' too long" when crawl jobs contain hundreds of URLs)
        sources_by_url = {}
        if all_crawled_urls:
            sources_resp = supabase.table('tenant_sources').select("*") \
                .eq('tenant_id', tenant_id_str) \
                .limit(10000) \
                .execute()
            for s in (sources_resp.data or []):
                if s['source_location'] in all_crawled_urls:
                    sources_by_url[s['source_location']] = s

        # Attach sources + counts to each job
        for job in jobs:
            job_tasks = tasks_by_job.get(job['id'], [])
            job['sources'] = [sources_by_url[t['url']] for t in job_tasks if t['url'] in sources_by_url]
            job['task_count'] = len(job_tasks)

        return jsonify(jobs), 200
    except Exception as e:
        error_logger.error(f"Error getting crawling jobs for tenant {tenant_id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to retrieve crawling jobs"}), 500

@sources_bp.route('/<uuid:tenant_id>/crawling_jobs/<int:job_id>/progress', methods=['GET'])
@token_required
def get_crawling_job_progress(current_user, tenant_id, job_id):
    try:
        from app.models.database import CrawlingStatus
        tenant_id_str = str(tenant_id)

        tenant_check = supabase.table('tenants').select("id").eq('id', tenant_id_str).eq('user_id', current_user.id).single().execute()
        if not tenant_check.data:
            return jsonify({"error": "Tenant not found or access denied"}), 404

        job_check = supabase.table('crawling_jobs').select("id").eq('id', job_id).eq('tenant_id', tenant_id_str).maybe_single().execute()
        if not job_check.data:
            return jsonify({"error": "Job not found or not part of this tenant"}), 404

        tasks_response = supabase.table('crawling_tasks').select('status').eq('job_id', job_id).limit(10000).execute()

        from collections import Counter
        status_list = [task['status'] for task in tasks_response.data]
        db_counts = Counter(status_list)

        counts = {status.value: 0 for status in CrawlingStatus}
        for status_str, count in db_counts.items():
            if status_str in counts:
                counts[status_str] = count

        progress = {
            "total": sum(counts.values()),
            "completed": counts.get(CrawlingStatus.COMPLETED.value, 0),
            "pending": counts.get(CrawlingStatus.PENDING.value, 0),
            "in_progress": counts.get(CrawlingStatus.IN_PROGRESS.value, 0),
            "failed": counts.get(CrawlingStatus.FAILED.value, 0)
        }

        return jsonify(progress), 200
    except Exception as e:
        error_logger.error(f"Error getting job progress for job {job_id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to retrieve job progress"}), 500

@sources_bp.route('/<uuid:tenant_id>/crawling_jobs/<int:job_id>/cancel', methods=['POST'])
@token_required
def cancel_crawling_job(current_user, tenant_id, job_id):
    """
    Soft-cancel a crawl job.
    Marks the job and all its PENDING / IN_PROGRESS tasks as FAILED so the
    Celery scheduler stops picking up new pages for this job.
    Already-running worker tasks will complete their current URL but will not
    enqueue further sub-pages because the job status check will see FAILED.
    """
    try:
        from app.models.database import CrawlingStatus
        tenant_id_str = str(tenant_id)

        # Auth check
        tenant_check = supabase.table('tenants').select("id").eq('id', tenant_id_str).eq('user_id', current_user.id).single().execute()
        if not tenant_check.data:
            return jsonify({"error": "Tenant not found or access denied"}), 404

        # Ownership check
        job_check = supabase.table('crawling_jobs').select("id", "status").eq('id', job_id).eq('tenant_id', tenant_id_str).single().execute()
        if not job_check.data:
            return jsonify({"error": "Job not found or not part of this tenant"}), 404

        job_status = job_check.data.get('status')
        if job_status in (CrawlingStatus.COMPLETED.value, CrawlingStatus.FAILED.value):
            return jsonify({"message": "Job is already finished.", "status": job_status}), 200

        # 1. Mark ALL pending/in-progress tasks as FAILED — this prevents the
        #    Celery scheduler from picking them up.
        supabase.table('crawling_tasks') \
            .update({"status": CrawlingStatus.FAILED.value}) \
            .eq('job_id', job_id) \
            .in_('status', [CrawlingStatus.PENDING.value, CrawlingStatus.IN_PROGRESS.value]) \
            .execute()

        # 2. Mark the job itself as FAILED
        supabase.table('crawling_jobs') \
            .update({"status": CrawlingStatus.FAILED.value}) \
            .eq('id', job_id) \
            .execute()

        error_logger.info("Crawl job %s cancelled by user %s", job_id, current_user.id)
        return jsonify({"message": "Crawl job cancelled successfully."}), 200

    except Exception as e:
        error_logger.error(f"Error cancelling crawl job {job_id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to cancel crawl job"}), 500


@sources_bp.route('/<uuid:tenant_id>/crawling_jobs/<int:job_id>', methods=['DELETE'])
@token_required
def delete_crawling_job(current_user, tenant_id, job_id):
    """
    Delete a crawl job and ALL data it produced:
      1. Cancel any in-flight tasks (mark FAILED so workers stop)
      2. Bulk-delete every tenant_sources row whose source_location was
         crawled by this job (identified via crawling_tasks.url)
      3. Delete those vectors from ChromaDB
      4. Delete crawling_tasks rows
      5. Delete the crawling_jobs row
    """
    try:
        from app.models.database import CrawlingStatus
        tenant_id_str = str(tenant_id)

        tenant_check = supabase.table('tenants').select("id").eq('id', tenant_id_str).eq('user_id', current_user.id).single().execute()
        if not tenant_check.data:
            return jsonify({"error": "Tenant not found or access denied"}), 404

        job_check = supabase.table('crawling_jobs').select("id", "status").eq('id', job_id).eq('tenant_id', tenant_id_str).single().execute()
        if not job_check.data:
            return jsonify({"error": "Job not found or not part of this tenant"}), 404

        # 1. Stop any in-flight tasks
        job_status = job_check.data.get('status')
        if job_status == CrawlingStatus.IN_PROGRESS.value:
            supabase.table('crawling_tasks') \
                .update({"status": CrawlingStatus.FAILED.value}) \
                .eq('job_id', job_id) \
                .in_('status', [CrawlingStatus.PENDING.value, CrawlingStatus.IN_PROGRESS.value]) \
                .execute()
            supabase.table('crawling_jobs').update({"status": CrawlingStatus.FAILED.value}).eq('id', job_id).execute()

        # 2. Collect all URLs that this job crawled
        tasks_resp = supabase.table('crawling_tasks').select("url").eq('job_id', job_id).execute()
        crawled_urls = [t['url'] for t in (tasks_resp.data or [])]

        # 3. Find + delete matching tenant_sources rows in batches
        deleted_source_ids = []
        if crawled_urls:
            from app.gemini_store.service import GeminiStoreService
            
            # Batch size of 100 prevents "URL component 'query' too long" in Supabase
            batch_size = 100
            for i in range(0, len(crawled_urls), batch_size):
                url_batch = crawled_urls[i:i + batch_size]
                
                sources_resp = supabase.table('tenant_sources') \
                    .select("id, gemini_document_name") \
                    .eq('tenant_id', tenant_id_str) \
                    .in_('source_location', url_batch) \
                    .execute()
                    
                batch_sources = sources_resp.data or []
                if not batch_sources:
                    continue
                    
                batch_ids = [s['id'] for s in batch_sources]
                deleted_source_ids.extend(batch_ids)
                
                # Delete the sources from Supabase
                supabase.table('tenant_sources').delete().in_('id', batch_ids).execute()
                
                # Delete from Gemini Store
                for src in batch_sources:
                    doc_name = src.get('gemini_document_name')
                    if doc_name:
                        try:
                            GeminiStoreService.delete_document(doc_name)
                        except Exception as vec_err:
                            error_logger.warning("delete_job: Gemini store cleanup partial failure for job %s: %s", job_id, vec_err)

            error_logger.info("delete_job: purged %d Gemini document(s) for job %s", len(deleted_source_ids), job_id)

        # 5. Delete crawling_tasks + job row
        supabase.table('crawling_tasks').delete().eq('job_id', job_id).execute()
        supabase.table('crawling_jobs').delete().eq('id', job_id).execute()

        error_logger.info(
            "Crawl job %s deleted by user %s — removed %d source(s)",
            job_id, current_user.id, len(deleted_source_ids)
        )
        return jsonify({
            "message": "Crawl job and all associated data deleted.",
            "deleted_sources": len(deleted_source_ids)
        }), 200

    except Exception as e:
        error_logger.error(f"Error deleting crawl job {job_id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to delete crawl job"}), 500


@sources_bp.route('/<uuid:tenant_id>/sources/<int:source_id>', methods=['DELETE'])
@token_required
def delete_source(current_user, tenant_id, source_id):
    try:
        tenant_id_str = str(tenant_id)
        tenant_check = supabase.table('tenants').select("id").eq('id', tenant_id_str).eq('user_id', current_user.id).single().execute()
        if not tenant_check.data:
            return jsonify({"error": "Tenant not found or access denied"}), 404

        source_resp = supabase.table('tenant_sources').select("*").eq('id', source_id).eq('tenant_id', tenant_id_str).single().execute()
        if not source_resp.data:
            return jsonify({"error": "Source not found or access denied"}), 404

        source = source_resp.data

        # Delete the document from the Gemini File Search Store
        gemini_doc_name = source.get('gemini_document_name')
        if gemini_doc_name:
            try:
                from app.gemini_store.service import GeminiStoreService
                GeminiStoreService.delete_document(gemini_doc_name)
            except Exception as vec_err:
                error_logger.error(
                    "Soft failure: could not delete Gemini document %s for source %s: %s",
                    gemini_doc_name, source_id, vec_err
                )

        # Delete the local file if this was a user upload
        if source.get('source_type') == 'FILE':
            local_path = source.get('source_location')
            if local_path and os.path.exists(local_path):
                try:
                    os.remove(local_path)
                    error_logger.info("Deleted local file %s for source %s", local_path, source_id)
                except OSError as file_err:
                    error_logger.error("Could not delete local file %s: %s", local_path, file_err)

        supabase.table('tenant_sources').delete().eq('id', source_id).execute()
        return jsonify({"message": "Source deleted successfully."}), 200

    except Exception as e:
        error_logger.error(f"Error deleting source {source_id} for tenant {tenant_id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to delete source"}), 500


@sources_bp.route('/<uuid:tenant_id>/sources', methods=['DELETE'])
@token_required
def delete_all_sources(current_user, tenant_id):
    """
    Nukes ALL knowledge for a tenant:
      1. Deletes the entire Gemini File Search Store (all documents in one shot)
      2. Clears gemini_file_store_name on the tenant (fresh store on next upload)
      3. Deletes all tenant_sources rows
      4. Deletes all crawling_jobs + crawling_tasks rows
      5. Removes all uploaded files from disk
    """
    try:
        tenant_id_str = str(tenant_id)
        tenant_resp = (
            supabase.table('tenants')
            .select("id, gemini_file_store_name")
            .eq('id', tenant_id_str)
            .eq('user_id', current_user.id)
            .single()
            .execute()
        )
        if not tenant_resp.data:
            return jsonify({"error": "Tenant not found or access denied"}), 404

        # 1. Delete the Gemini File Search Store (drops all indexed documents at once)
        store_name = (tenant_resp.data or {}).get('gemini_file_store_name')
        if store_name:
            try:
                from app.gemini_store.service import GeminiStoreService
                GeminiStoreService.delete_store(store_name)
                error_logger.info("delete_all: deleted Gemini store %s for tenant %s", store_name, tenant_id_str)
            except Exception as store_err:
                error_logger.warning(
                    "delete_all: soft failure deleting Gemini store %s: %s",
                    store_name, store_err
                )

        # 2. Clear the store reference on the tenant so a fresh one is created next upload
        supabase.table('tenants') \
            .update({"gemini_file_store_name": None}) \
            .eq('id', tenant_id_str) \
            .execute()

        # 3. Delete all source records
        supabase.table('tenant_sources').delete().eq('tenant_id', tenant_id_str).execute()

        # 4. Delete crawling jobs + tasks
        jobs_resp = supabase.table('crawling_jobs').select("id").eq('tenant_id', tenant_id_str).execute()
        job_ids = [j['id'] for j in (jobs_resp.data or [])]
        if job_ids:
            supabase.table('crawling_tasks').delete().in_('job_id', job_ids).execute()
        supabase.table('crawling_jobs').delete().eq('tenant_id', tenant_id_str).execute()

        # 5. Remove uploaded files from disk
        tenant_upload_dir = os.path.join(UPLOADS_DIR, tenant_id_str)
        if os.path.isdir(tenant_upload_dir):
            import shutil
            shutil.rmtree(tenant_upload_dir, ignore_errors=True)

        error_logger.info(
            "delete_all: tenant %s knowledge fully cleared by user %s",
            tenant_id_str, current_user.id
        )
        return jsonify({"message": "All knowledge deleted successfully."}), 200

    except Exception as e:
        error_logger.error(
            f"Error deleting all sources for tenant {tenant_id}: {e}",
            extra={'user_id': current_user.id}, exc_info=True
        )
        return jsonify({"error": "Failed to delete all knowledge"}), 500

@sources_bp.route('/tasks/<string:task_id>', methods=['GET'])
@token_required
def get_task_status(current_user, task_id):
    try:
        task = celery.AsyncResult(task_id)
        if task.state == 'PENDING':
            response = {
                'state': task.state,
                'status': 'Pending...'
            }
        elif task.state != 'FAILURE':
            response = {
                'state': task.state,
                'status': task.info.get('status', ''),
                'result': task.info.get('result', {})
            }
            if 'result' in task.info:
                response['result'] = task.info['result']
        else:
            response = {
                'state': task.state,
                'status': str(task.info),
            }
        return jsonify(response)
    except Exception as e:
        error_logger.error(f"Error getting task status for task {task_id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to get task status"}), 500


@sources_bp.route('/<uuid:tenant_id>/store-stats', methods=['GET'])
@token_required
def get_store_stats(current_user, tenant_id):
    """
    Returns real stats from the tenant's Gemini File Search Store:
      - document_count   total documents indexed in the store
      - active_count     documents with state ACTIVE
      - indexing_count   documents still being processed
      - failed_count     documents that failed indexing
      - has_store        whether a store exists yet
    Falls back gracefully if the store hasn't been created yet.
    """
    try:
        tenant_id_str = str(tenant_id)
        tenant_resp = (
            supabase.table('tenants')
            .select("gemini_file_store_name")
            .eq('id', tenant_id_str)
            .eq('user_id', current_user.id)
            .single()
            .execute()
        )
        if not tenant_resp.data:
            return jsonify({"error": "Tenant not found or access denied"}), 404

        store_name = (tenant_resp.data or {}).get('gemini_file_store_name')
        if not store_name:
            return jsonify({
                "has_store": False,
                "document_count": 0,
                "active_count": 0,
                "indexing_count": 0,
                "failed_count": 0,
            }), 200

        from google import genai
        client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

        # List all documents in the store and aggregate their states
        docs = list(client.file_search_stores.documents.list(parent=store_name))

        active   = sum(1 for d in docs if str(getattr(d, 'state', '')).upper() in ('ACTIVE', 'STATE_ACTIVE'))
        indexing = sum(1 for d in docs if str(getattr(d, 'state', '')).upper() in ('INDEXING', 'STATE_INDEXING', 'PROCESSING'))
        failed   = sum(1 for d in docs if str(getattr(d, 'state', '')).upper() in ('FAILED', 'STATE_FAILED', 'ERROR'))

        return jsonify({
            "has_store": True,
            "document_count": len(docs),
            "active_count":   active,
            "indexing_count": indexing,
            "failed_count":   failed,
        }), 200

    except Exception as e:
        error_logger.error(
            f"Error fetching store stats for tenant {tenant_id}: {e}",
            extra={'user_id': current_user.id}, exc_info=True
        )
        return jsonify({"error": "Failed to fetch store stats"}), 500
