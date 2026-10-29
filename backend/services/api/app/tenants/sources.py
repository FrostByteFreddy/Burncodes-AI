from flask import Blueprint, request, jsonify
from app.database.supabase_client import fetch_all, supabase
from app.auth.decorators import token_required
from app.models.database import SourceType
from app.data_processing.tasks import process_local_file, start_learning_task, crawl_links_task
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


def _document_names(source):
    """Every File Search document of a source (legacy single doc + per-section docs)."""
    names = list(source.get('gemini_document_names') or [])
    if source.get('gemini_document_name'):
        names.append(source['gemini_document_name'])
    return list(dict.fromkeys(names))


def _delete_documents(sources, context):
    from app.gemini_store.service import GeminiStoreService
    for src in sources:
        for name in _document_names(src):
            try:
                GeminiStoreService.delete_document(name)
            except Exception as err:
                error_logger.warning("%s: could not delete Gemini document %s: %s", context, name, err)


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
        from app.tenants.routes import SOURCE_COLUMNS
        sources = fetch_all(lambda: supabase.table('tenant_sources').select(SOURCE_COLUMNS).eq('tenant_id', tenant_id_str).order('id'))
        return jsonify(sources), 200
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

        # Each URL becomes a single-page crawl: scanned, estimated, then
        # learned after confirmation like any other crawl.
        task_ids = [
            crawl_links_task.delay(tenant_id=tenant_id_str, start_url=url, single_page_only=True).id
            for url in dict.fromkeys(urls)
        ]
        return jsonify({"task_ids": task_ids}), 202
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
        same_language = data.get('same_language', False)
        use_sitemap = data.get('use_sitemap', False)
        skip_funnel = data.get('skip_funnel', False)
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
            single_page_only=bool(single_page_only),
            excluded_urls=excluded_urls,
            same_language=bool(same_language),
            use_sitemap=bool(use_sitemap),
            skip_funnel=bool(skip_funnel),
            crawl_mode=crawl_mode,
        )

        return jsonify({"task_id": task.id}), 202
    except Exception as e:
        error_logger.error(f"Error discovering links for tenant {tenant_id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to discover links"}), 500

def _learn_done(job_id: int) -> int:
    """Sources this job has finished learning (learned or failed), counted in the database."""
    return supabase.table('crawl_job_log').select('id', count='exact') \
        .eq('job_id', job_id).in_('event', ['learned', 'learn_failed']).limit(1).execute().count or 0


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
        tasks = fetch_all(lambda: supabase.table('crawling_tasks').select("job_id,url,status").in_('job_id', job_ids).order('id'))
        tasks_by_job = defaultdict(list)
        all_crawled_urls = set()
        for t in tasks:
            tasks_by_job[t['job_id']].append(t)
            all_crawled_urls.add(t['url'])

        # Batch-fetch matching tenant_sources — fetch all for this tenant, filter in Python
        # (avoids httpx "URL component 'query' too long" when crawl jobs contain hundreds of URLs)
        sources_by_url = {}
        if all_crawled_urls:
            from app.tenants.routes import SOURCE_COLUMNS
            tenant_sources = fetch_all(lambda: supabase.table('tenant_sources').select(SOURCE_COLUMNS)
                                       .eq('tenant_id', tenant_id_str).order('id'))
            for s in tenant_sources:
                if s['source_location'] in all_crawled_urls:
                    sources_by_url[s['source_location']] = s

        # Attach sources + counts to each job
        for job in jobs:
            job_tasks = tasks_by_job.get(job['id'], [])
            job['sources'] = [sources_by_url[t['url']] for t in job_tasks if t['url'] in sources_by_url]
            job['task_count'] = len(job_tasks)
            if job.get('status') == 'INDEXING':
                job['learn_done'] = _learn_done(job['id'])

        return jsonify(jobs), 200
    except Exception as e:
        error_logger.error(f"Error getting crawling jobs for tenant {tenant_id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to retrieve crawling jobs"}), 500

@sources_bp.route('/<uuid:tenant_id>/crawling_jobs/<int:job_id>', methods=['GET'])
@token_required
def get_crawling_job(current_user, tenant_id, job_id):
    """One crawl job with its estimate and report (crawl detail page)."""
    try:
        tenant_id_str = str(tenant_id)
        tenant_check = supabase.table('tenants').select("id").eq('id', tenant_id_str).eq('user_id', current_user.id).limit(1).execute()
        if not tenant_check.data:
            return jsonify({"error": "Tenant not found or access denied"}), 404
        rows = supabase.table('crawling_jobs').select("*").eq('id', job_id).eq('tenant_id', tenant_id_str).limit(1).execute().data
        if not rows:
            return jsonify({"error": "Job not found or not part of this tenant"}), 404
        if rows[0].get('status') == 'INDEXING':
            rows[0]['learn_done'] = _learn_done(job_id)
        return jsonify(rows[0]), 200
    except Exception as e:
        error_logger.error(f"Error getting crawl job {job_id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to retrieve crawl job"}), 500


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

        task_rows = fetch_all(lambda: supabase.table('crawling_tasks').select('status').eq('job_id', job_id).order('id'))

        from collections import Counter
        status_list = [task['status'] for task in task_rows]
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

@sources_bp.route('/<uuid:tenant_id>/knowledge/overview', methods=['GET'])
@token_required
def get_knowledge_overview(current_user, tenant_id):
    """
    What the bot can answer right now: verified dates in the coming days and
    open issues across all sources (warnings from learning, failed sources).
    """
    try:
        from datetime import date, timedelta
        tenant_id_str = str(tenant_id)
        tenant_check = supabase.table('tenants').select("id").eq('id', tenant_id_str).eq('user_id', current_user.id).limit(1).execute()
        if not tenant_check.data:
            return jsonify({"error": "Tenant not found or access denied"}), 404
        try:
            days = max(1, min(int(request.args.get('days', 14)), 60))
        except ValueError:
            days = 14
        today = date.today()
        events = (
            supabase.table('tenant_events')
            .select("event_date, series, zone, is_exception, notes, source_id")
            .eq('tenant_id', tenant_id_str)
            .gte('event_date', today.isoformat())
            .lte('event_date', (today + timedelta(days=days - 1)).isoformat())
            .order('event_date').limit(500).execute()
        ).data or []
        from app.knowledge.calendar import dedupe_events
        events = dedupe_events(events)   # the same event read from several pages shows once
        # Series whose published dates ended — the bot can't answer "next" for them
        past = fetch_all(lambda: (
            supabase.table('tenant_events').select("series, zone, event_date")
            .eq('tenant_id', tenant_id_str).lt('event_date', today.isoformat())
            .order('event_date', desc=True).order('id')
        ), max_rows=10_000)
        future_keys = {
            (r['series'], r['zone']) for r in fetch_all(lambda: (
                supabase.table('tenant_events').select("series, zone")
                .eq('tenant_id', tenant_id_str).gte('event_date', today.isoformat()).order('id')
            ))
        }
        # Only recurring series count as "ended" (several dates spread over
        # months, e.g. a collection calendar) — one-off events that already
        # took place are expected, not something to fix.
        spans: dict[tuple, list[str]] = {}
        for r in past:
            key = (r['series'], r['zone'])
            if key not in future_keys:
                spans.setdefault(key, []).append(r['event_date'])
        ended = {}
        for key, dates in spans.items():
            first, last = min(dates), max(dates)
            if len(dates) >= 4 and (date.fromisoformat(last) - date.fromisoformat(first)).days >= 60:
                ended[key] = last

        sources = (
            supabase.table('tenant_sources')
            .select("id, source_location, title, status, status_code, warnings")
            .eq('tenant_id', tenant_id_str)
            .or_("status.eq.ERROR,warnings.neq.[]")
            .limit(500).execute()
        ).data or []
        from app.knowledge.jobs import issues_of
        issues = []
        for s in sources:
            for w in issues_of(s.get('warnings')):
                issues.append({"source_id": s['id'], "title": s.get('title') or s['source_location'],
                               "url": s['source_location'], **w})

        return jsonify({
            "today": today.isoformat(),
            "days": days,
            "upcoming": events,
            "ended": [{"series": k[0], "zone": k[1], "last": v} for k, v in sorted(ended.items())],
            "issues": issues,
            "failed": sum(1 for s in sources if s.get('status') == 'ERROR'),
        }), 200
    except Exception as e:
        error_logger.error(f"Error building knowledge overview for {tenant_id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to load overview"}), 500


@sources_bp.route('/<uuid:tenant_id>/crawling_jobs/<int:job_id>/log', methods=['GET'])
@token_required
def get_crawling_job_log(current_user, tenant_id, job_id):
    """Latest activity of a crawl job (oldest first). Live updates come via Realtime."""
    try:
        tenant_id_str = str(tenant_id)
        tenant_check = supabase.table('tenants').select("id").eq('id', tenant_id_str).eq('user_id', current_user.id).limit(1).execute()
        if not tenant_check.data:
            return jsonify({"error": "Tenant not found or access denied"}), 404
        try:
            limit = max(1, min(int(request.args.get('limit', 100)), 500))
        except ValueError:
            limit = 100
        rows = (
            supabase.table('crawl_job_log').select("id, event, data, created_at")
            .eq('job_id', job_id).eq('tenant_id', tenant_id_str)
            .order('id', desc=True).limit(limit).execute()
        ).data or []
        return jsonify(list(reversed(rows))), 200
    except Exception as e:
        error_logger.error(f"Error getting log for crawl job {job_id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to retrieve crawl log"}), 500


@sources_bp.route('/<uuid:tenant_id>/crawling_jobs/<int:job_id>/confirm', methods=['POST'])
@token_required
def confirm_crawling_job(current_user, tenant_id, job_id):
    """
    The user accepted the estimate of a scanned crawl: start learning.
    Requires the balance to cover the estimate (prepaid).
    """
    try:
        tenant_id_str = str(tenant_id)
        tenant_check = supabase.table('tenants').select("id").eq('id', tenant_id_str).eq('user_id', current_user.id).limit(1).execute()
        if not tenant_check.data:
            return jsonify({"error": "Tenant not found or access denied"}), 404

        job_rows = supabase.table('crawling_jobs').select("id, status, estimate").eq('id', job_id).eq('tenant_id', tenant_id_str).limit(1).execute().data
        if not job_rows:
            return jsonify({"error": "Job not found or not part of this tenant"}), 404
        job = job_rows[0]
        if job['status'] != 'SCANNED':
            return jsonify({"error": "This crawl is not waiting for confirmation", "status": job['status']}), 409

        estimate_chf = float((job.get('estimate') or {}).get('cost_chf') or 0)
        balance = BillingService.check_balance(current_user.id)
        if balance < estimate_chf:
            return jsonify({
                "error": "Insufficient balance for this crawl. Please recharge.",
                "balance_chf": balance, "estimate_chf": estimate_chf,
            }), 402

        start_learning_task.delay(job_id)
        return jsonify({"message": "Learning started"}), 202
    except Exception as e:
        error_logger.error(f"Error confirming crawl job {job_id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to confirm crawl job"}), 500


@sources_bp.route('/<uuid:tenant_id>/crawling_jobs/<int:job_id>/skipped', methods=['GET'])
@token_required
def list_skipped_sources(current_user, tenant_id, job_id):
    """What the sorting step set aside for this crawl, to review before learning."""
    try:
        tenant_id_str = str(tenant_id)
        if not supabase.table('tenants').select("id").eq('id', tenant_id_str).eq('user_id', current_user.id).limit(1).execute().data:
            return jsonify({"error": "Tenant not found or access denied"}), 404
        rows = fetch_all(lambda: (
            supabase.table('tenant_sources')
            .select("id, source_type, source_location, title, file_pages, skip_reason")
            .eq('tenant_id', tenant_id_str).eq('last_job_id', job_id).eq('status', 'SKIPPED').order('id')
        ))
        return jsonify(rows), 200
    except Exception as e:
        error_logger.error(f"Error listing skipped sources for job {job_id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to list sources"}), 500


@sources_bp.route('/<uuid:tenant_id>/crawling_jobs/<int:job_id>/selection', methods=['GET'])
@token_required
def get_selection(current_user, tenant_id, job_id):
    """Before learning: every source with its cost and folder, plus Gemini's savings suggestions."""
    try:
        from app.knowledge.selection import selection
        tenant_id_str = str(tenant_id)
        job = supabase.table('crawling_jobs').select("id, start_url, estimate").eq('id', job_id) \
            .eq('tenant_id', tenant_id_str).limit(1).execute().data
        owns = supabase.table('tenants').select("id").eq('id', tenant_id_str).eq('user_id', current_user.id).limit(1).execute().data
        if not job or not owns:
            return jsonify({"error": "Job not found or access denied"}), 404
        return jsonify({
            "items": selection(job[0]),
            "recommendations": (job[0].get('estimate') or {}).get('recommendations') or [],
        }), 200
    except Exception as e:
        error_logger.error(f"Error listing the selection for job {job_id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to list sources"}), 500


@sources_bp.route('/<uuid:tenant_id>/crawling_jobs/<int:job_id>/selection', methods=['POST'])
@token_required
def change_selection(current_user, tenant_id, job_id):
    """
    Before learning: tick or untick sources ({"include"/"exclude": [ids]}) or
    whole folders ({"include_folders"/"exclude_folders": ["/politik/…"]}).
    The choice is saved as rules on the tenant, so later crawls keep it.
    Returns the recomputed estimate and the rules.
    """
    try:
        from app.knowledge import jobs as knowledge_jobs
        from app.knowledge.selection import change_selection as apply_change
        tenant_id_str = str(tenant_id)
        job = supabase.table('crawling_jobs').select("id, status, tenant_id, start_url").eq('id', job_id) \
            .eq('tenant_id', tenant_id_str).limit(1).execute().data
        owns = supabase.table('tenants').select("id").eq('id', tenant_id_str).eq('user_id', current_user.id).limit(1).execute().data
        if not job or not owns:
            return jsonify({"error": "Job not found or access denied"}), 404
        if job[0]['status'] != 'SCANNED':
            return jsonify({"error": "The selection can only change before learning starts"}), 409
        data = request.get_json(silent=True) or {}
        folders = lambda key: [str(p) for p in data.get(key) or [] if str(p).startswith('/')]
        rules = apply_change(
            job[0],
            include=[int(i) for i in data.get('include') or []],
            exclude=[int(i) for i in data.get('exclude') or []],
            include_folders=folders('include_folders'),
            exclude_folders=folders('exclude_folders'),
            restore_folders=folders('restore_folders'),
        )
        return jsonify({"estimate": knowledge_jobs.refresh_estimate(job_id), "rules": rules}), 200
    except (TypeError, ValueError):
        return jsonify({"error": "include/exclude must be lists of source ids"}), 400
    except Exception as e:
        error_logger.error(f"Error changing selection for job {job_id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to change the selection"}), 500


@sources_bp.route('/<uuid:tenant_id>/crawling_jobs/<int:job_id>/resume', methods=['POST'])
@token_required
def resume_crawling_job(current_user, tenant_id, job_id):
    """Continues a stopped crawl where it stopped (learning, scanning or the estimate)."""
    try:
        from app.knowledge import jobs as knowledge_jobs
        tenant_id_str = str(tenant_id)
        owns = supabase.table('tenants').select("id").eq('id', tenant_id_str).eq('user_id', current_user.id).limit(1).execute().data
        job = supabase.table('crawling_jobs').select("*").eq('id', job_id).eq('tenant_id', tenant_id_str).limit(1).execute().data
        if not owns or not job:
            return jsonify({"error": "Job not found or access denied"}), 404
        running = supabase.table('crawling_jobs').select("id").eq('tenant_id', tenant_id_str) \
            .in_('status', ['IN_PROGRESS', 'SCANNED', 'INDEXING']).neq('id', job_id).limit(1).execute().data
        if running:
            return jsonify({"error": "Another crawl of this chatbot is still running", "code": "busy"}), 409
        phase = knowledge_jobs.resume_job(job[0])
        if not phase:
            return jsonify({"error": "Nothing left to continue", "code": "nothing_to_resume"}), 409
        return jsonify({"phase": phase}), 202
    except Exception as e:
        error_logger.error(f"Error resuming crawl job {job_id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to resume the crawl"}), 500


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
        # Sources still waiting to be learned keep their previous index state;
        # they're picked up again by the next crawl.

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
        if job_status in (CrawlingStatus.IN_PROGRESS.value, CrawlingStatus.SCANNED.value, CrawlingStatus.INDEXING.value):
            supabase.table('crawling_tasks') \
                .update({"status": CrawlingStatus.FAILED.value}) \
                .eq('job_id', job_id) \
                .in_('status', [CrawlingStatus.PENDING.value, CrawlingStatus.IN_PROGRESS.value]) \
                .execute()
            supabase.table('crawling_jobs').update({"status": CrawlingStatus.FAILED.value}).eq('id', job_id).execute()

        # 2. Collect all URLs that this job crawled
        crawled_urls = [t['url'] for t in fetch_all(
            lambda: supabase.table('crawling_tasks').select("url").eq('job_id', job_id).order('id'))]

        # 3. Find + delete matching tenant_sources rows in batches
        deleted_source_ids = []
        if crawled_urls:
            from app.gemini_store.service import GeminiStoreService
            
            # Batch size of 100 prevents "URL component 'query' too long" in Supabase
            batch_size = 100
            for i in range(0, len(crawled_urls), batch_size):
                url_batch = crawled_urls[i:i + batch_size]
                
                sources_resp = supabase.table('tenant_sources') \
                    .select("id, gemini_document_name, gemini_document_names") \
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
                _delete_documents(batch_sources, f"delete_job {job_id}")

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

        # Delete its documents from the Gemini File Search Store
        _delete_documents([source], f"delete_source {source_id}")

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
