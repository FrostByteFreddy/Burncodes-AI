import json
from flask import Blueprint, request, jsonify
from app.database.supabase_client import fetch_all, supabase
from app.auth.decorators import token_required
from app.models.database import Tenant, TenantFineTune
from app.logging_config import error_logger
from app import limiter
from app.knowledge.audience import AUDIENCES
from uuid import uuid4
import os

tenants_bp = Blueprint('tenants', __name__)

SOURCE_COLUMNS = ("id, tenant_id, source_type, source_location, status, status_code, created_at, title, summary, page_type, importance, importance_reason, warnings, last_seen_at, last_changed_at, cost_chf, last_job_id, learned_job_id, indexed_chunks")

@tenants_bp.route('', methods=['POST'])
@token_required
def create_tenant(current_user):
    try:
        data = request.get_json()
        if not all(k in data for k in ['name', 'intro_message', 'system_persona', 'rag_prompt_template']):
            return jsonify({"error": "Missing required tenant fields"}), 400

        tenant_id = uuid4()
        tenant_data = {
            "id": str(tenant_id),
            "user_id": str(current_user.id),
            "name": data['name'],
            "intro_message": data['intro_message'],
            "system_persona": data['system_persona'],
            "rag_prompt_template": data['rag_prompt_template'],
            "doc_language": data.get('doc_language'),
            "translation_target": data.get('translation_target'),
            "crawl_mode": data.get('crawl_mode', 'playwright_llm'),
        }
        if data.get('audience') in AUDIENCES:
            tenant_data['audience'] = data['audience']
        supabase.table('tenants').insert(tenant_data).execute()

        # Fine-tune rules are stored in DB only — injected into the system
        # prompt at chat time. No vector embedding needed.
        fine_tune_rules_data = data.get('fine_tune_rules', [])
        if fine_tune_rules_data:
            rules_to_insert = [
                {"tenant_id": str(tenant_id), "trigger": r['trigger'], "instruction": r['instruction']}
                for r in fine_tune_rules_data
            ]
            supabase.table('tenant_fine_tune').insert(rules_to_insert).execute()

        return jsonify({"message": "Tenant created successfully", "id": str(tenant_id)}), 201
    except Exception as e:
        error_logger.error(f"Error creating tenant for user {current_user.id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to create tenant"}), 500

@tenants_bp.route('', methods=['GET'])
@token_required
def get_tenants(current_user):
    try:
        tenants = supabase.table('tenants').select("*, tenant_sources(count)").eq('user_id', current_user.id).execute()
        for tenant in tenants.data:
            tenant['test_protected'] = bool(tenant.pop('test_password_hash', None))
            counts = tenant.pop('tenant_sources', None) or [{}]
            tenant['source_count'] = counts[0].get('count', 0)
        return jsonify(tenants.data), 200
    except Exception as e:
        error_logger.error(f"Error fetching tenants for user {current_user.id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to fetch tenants"}), 500

@tenants_bp.route('/<uuid:tenant_id>', methods=['GET'])
@token_required
def get_tenant(current_user, tenant_id):
    try:
        tenant = supabase.table('tenants').select("*").eq('id', str(tenant_id)).eq('user_id', current_user.id).single().execute()
        if not tenant.data:
            return jsonify({"error": "Tenant not found"}), 404

        fine_tune_rules = supabase.table('tenant_fine_tune').select("*").eq('tenant_id', str(tenant_id)).execute()
        tenant.data['fine_tune_rules'] = fine_tune_rules.data
        tenant.data['test_protected'] = bool(tenant.data.pop('test_password_hash', None))

        # Not "*": sources carry their scanned Markdown, which the dashboard never needs.
        tenant.data['tenant_sources'] = fetch_all(
            lambda: supabase.table('tenant_sources').select(SOURCE_COLUMNS).eq('tenant_id', str(tenant_id)).order('id'))

        return jsonify(tenant.data), 200
    except Exception as e:
        error_logger.error(f"Error fetching tenant {tenant_id} for user {current_user.id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to fetch tenant"}), 500

@tenants_bp.route('/<uuid:tenant_id>/public', methods=['GET'])
def get_public_tenant(tenant_id):
    try:
        tenant = supabase.table('tenants').select("name, intro_message, widget_config, is_active, test_password_hash").eq('id', str(tenant_id)).single().execute()
        if not tenant.data:
            return jsonify({"error": "Tenant not found"}), 404
        if tenant.data.get('is_active') is False:
            # Switched off: nothing to render. widget_enabled=false also stops
            # widget.js copies cached before the is_active check existed.
            return jsonify({"is_active": False, "widget_config": {"widget_enabled": False}}), 200
        protected = bool(tenant.data.pop('test_password_hash', None))
        if protected:
            # the look is fine to show; the content waits for the password
            tenant.data.pop('intro_message', None)
        tenant.data['protected'] = protected
        return jsonify(tenant.data), 200
    except Exception as e:
        error_logger.error(f"Error fetching public tenant info for {tenant_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch tenant info"}), 500

@tenants_bp.route('/<uuid:tenant_id>', methods=['PUT'])
@token_required
def update_tenant(current_user, tenant_id):
    try:
        tenant_id_str = str(tenant_id)
        data = request.get_json()

        tenant_check = supabase.table('tenants').select("id").eq('id', tenant_id_str).eq('user_id', current_user.id).single().execute()
        if not tenant_check.data:
            return jsonify({"error": "Tenant not found or access denied"}), 404

        tenant_update_data = {}
        allowed_fields = ['name', 'intro_message', 'system_persona', 'rag_prompt_template',
                          'doc_language', 'translation_target', 'widget_config', 'crawl_mode', 'auto_recrawl']
        for field in allowed_fields:
            if field in data:
                tenant_update_data[field] = data[field]
        if 'auto_recrawl' in tenant_update_data:
            tenant_update_data['auto_recrawl'] = bool(tenant_update_data['auto_recrawl'])
        if 'is_active' in data:
            tenant_update_data['is_active'] = bool(data['is_active'])
        if 'test_password' in data:
            # empty / null removes the protection
            password = data['test_password'] or ''
            if password and len(password) < 6:
                return jsonify({"error": "The password needs at least 6 characters"}), 400
            from app.chat.access import hash_password
            tenant_update_data['test_password_hash'] = hash_password(password) if password else None
        if 'calendar_feeds' in data:
            tenant_update_data['calendar_feeds'] = bool(data['calendar_feeds'])
        if 'learning_model' in data:
            from app.ai_models import LEARNING_MODELS
            if data['learning_model'] not in LEARNING_MODELS:
                return jsonify({"error": f"learning_model must be one of {', '.join(LEARNING_MODELS)}"}), 400
            tenant_update_data['learning_model'] = data['learning_model']
        if 'audience' in data:
            if data['audience'] not in AUDIENCES:
                return jsonify({"error": f"audience must be one of {', '.join(AUDIENCES)}"}), 400
            tenant_update_data['audience'] = data['audience']
        if 'crawl_exclusions' in data:
            # the settings only remove rules; new ones come from the crawl's selection
            current = supabase.table('tenants').select('crawl_exclusions').eq('id', tenant_id_str).limit(1).execute().data
            keep = {json.dumps(r, sort_keys=True) for r in (data['crawl_exclusions'] or []) if isinstance(r, dict)}
            tenant_update_data['crawl_exclusions'] = [
                r for r in ((current[0].get('crawl_exclusions') if current else None) or [])
                if json.dumps(r, sort_keys=True) in keep
            ]
        if 'review_chats' in data:
            tenant_update_data['review_chats'] = bool(data['review_chats'])
        if 'review_interval_days' in data:
            if data['review_interval_days'] not in (1, 7):
                return jsonify({"error": "review_interval_days must be 1 or 7"}), 400
            tenant_update_data['review_interval_days'] = data['review_interval_days']
        if 'recrawl_interval_days' in data:
            try:
                days = int(data['recrawl_interval_days'])
            except (TypeError, ValueError):
                return jsonify({"error": "recrawl_interval_days must be a number"}), 400
            if not 1 <= days <= 90:
                return jsonify({"error": "recrawl_interval_days must be between 1 and 90"}), 400
            tenant_update_data['recrawl_interval_days'] = days

        if tenant_update_data:
            supabase.table('tenants').update(tenant_update_data).eq('id', tenant_id_str).execute()

        if 'fine_tune_rules' in data:
            # Replace all fine-tune rules — no vector store involved, just DB rows
            supabase.table('tenant_fine_tune').delete().eq('tenant_id', tenant_id_str).execute()
            new_rules_data = data['fine_tune_rules']
            if new_rules_data:
                rules_to_insert = [
                    {"tenant_id": tenant_id_str, "trigger": r['trigger'], "instruction": r['instruction']}
                    for r in new_rules_data
                ]
                supabase.table('tenant_fine_tune').insert(rules_to_insert).execute()

        return jsonify({"message": "Tenant updated successfully"}), 200
    except Exception as e:
        error_logger.error(f"Error updating tenant {tenant_id} for user {current_user.id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to update tenant"}), 500

@tenants_bp.route('/<uuid:tenant_id>', methods=['DELETE'])
@token_required
def delete_tenant(current_user, tenant_id):
    try:
        tenant_id_str = str(tenant_id)
        tenant_resp = supabase.table('tenants').select("*").eq('id', tenant_id_str).eq('user_id', current_user.id).single().execute()
        if not tenant_resp.data:
            return jsonify({"error": "Tenant not found or access denied"}), 404

        # Delete the Gemini File Search Store (and all its documents) if it exists
        # Gemini first: the chatbot is only deleted once its store is gone, so
        # nothing it learned is left behind without a way to delete it
        store_name = (tenant_resp.data or {}).get('gemini_file_store_name')
        if store_name:
            from app.gemini_store.service import GeminiStoreService
            if not GeminiStoreService.delete_store(store_name):
                return jsonify({"error": "The chatbot's knowledge could not be removed from Gemini. Nothing was deleted; please try again.",
                                "code": "gemini_failed"}), 502

        supabase.table('tenant_fine_tune').delete().eq('tenant_id', tenant_id_str).execute()
        supabase.table('tenant_sources').delete().eq('tenant_id', tenant_id_str).execute()
        # runs, their logs, chats, reviews, facts and dates go with the chatbot (ON DELETE CASCADE);
        # its spending stays in the billing ledger under its name
        supabase.table('tenants').delete().eq('id', tenant_id_str).execute()

        # files uploaded by hand live on disk, not in the database
        from app.tenants.sources import UPLOADS_DIR
        import shutil
        upload_dir = os.path.join(UPLOADS_DIR, tenant_id_str)
        if os.path.realpath(upload_dir).startswith(os.path.realpath(UPLOADS_DIR) + os.sep):
            shutil.rmtree(upload_dir, ignore_errors=True)
        return jsonify({"message": "Tenant deleted successfully"}), 200
    except Exception as e:
        error_logger.error(f"Error deleting tenant {tenant_id} for user {current_user.id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to delete tenant"}), 500


def _automation(tenant, jobs, now):
    """When the scheduled tasks last ran and will run next, for the dashboard."""
    from datetime import datetime, timedelta
    from app.ai_models import RATES

    def at(iso):
        return datetime.fromisoformat(iso.replace('Z', '+00:00')) if iso else None

    scheduled = [j for j in jobs if j.get('trigger') == 'scheduled']
    last_crawl = at(jobs[0]['created_at']) if jobs else None
    recrawl_days = tenant.get('recrawl_interval_days') or 7
    review_days = tenant.get('review_interval_days') or 1
    last_review = at(tenant.get('last_review_at'))
    # reviews run nightly at 03:00 UTC (see services/beat/celery_beat.py)
    next_night = (now + timedelta(days=1 if now.hour >= 3 else 0)).replace(hour=3, minute=0, second=0, microsecond=0)
    next_review = next_night
    if last_review:
        while next_review < last_review + timedelta(days=review_days) - timedelta(hours=1):
            next_review += timedelta(days=1)
    rate = RATES.get("review", RATES["chat"])
    return {
        "recrawl": {
            "enabled": bool(tenant.get('auto_recrawl')),
            "interval_days": recrawl_days,
            "last_run": scheduled[0]['created_at'] if scheduled else None,
            "next_run": ((last_crawl + timedelta(days=recrawl_days)).isoformat() if last_crawl else None)
                        if tenant.get('auto_recrawl') else None,
            "has_websites": bool(jobs),
        },
        "review": {
            "enabled": bool(tenant.get('review_chats')),
            "interval_days": review_days,
            "last_run": tenant.get('last_review_at'),
            "next_run": next_review.isoformat() if tenant.get('review_chats') else None,
            "est_chf_per_conversation": round(2000 / 1_000_000 * rate["input"] + 200 / 1_000_000 * rate["output"], 4),
        },
    }


@tenants_bp.route('/<uuid:tenant_id>/overview', methods=['GET'])
@token_required
def get_tenant_overview(current_user, tenant_id):
    """
    The dashboard's first page: is the bot on, how much is it used, what did
    it cost, and is its knowledge current. Compares with the previous period.
    """
    from datetime import date, datetime, timedelta, timezone
    try:
        tenant_id_str = str(tenant_id)
        tenant = (
            supabase.table('tenants')
            .select("id, name, is_active, widget_config, auto_recrawl, recrawl_interval_days, review_chats, review_interval_days, last_review_at")
            .eq('id', tenant_id_str).eq('user_id', current_user.id).limit(1).execute()
        ).data
        if not tenant:
            return jsonify({"error": "Tenant not found or access denied"}), 404
        tenant = tenant[0]
        try:
            days = max(1, min(int(request.args.get('days', 30)), 365))
        except ValueError:
            days = 30
        now = datetime.now(timezone.utc)
        since = now - timedelta(days=days)
        prev_since = since - timedelta(days=days)

        logs = fetch_all(lambda: (
            supabase.table('chat_logs')
            .select("conversation_id, user_message, cost_chf, created_at")
            .eq('tenant_id', tenant_id_str).gte('created_at', prev_since.isoformat())
            .order('created_at', desc=True).order('id', desc=True)
        ))
        current = [r for r in logs if r['created_at'] >= since.isoformat()]
        previous = [r for r in logs if r['created_at'] < since.isoformat()]

        # Questions per day for the sparkline, oldest first
        per_day = {}
        for r in current:
            per_day[r['created_at'][:10]] = per_day.get(r['created_at'][:10], 0) + 1
        today = now.date()
        series = [{"date": (today - timedelta(days=i)).isoformat(),
                   "questions": per_day.get((today - timedelta(days=i)).isoformat(), 0)}
                  for i in range(days - 1, -1, -1)]

        jobs = (
            supabase.table('crawling_jobs')
            .select("id, start_url, status, created_at, finished_at, report, estimate, trigger")
            .eq('tenant_id', tenant_id_str).order('created_at', desc=True).limit(200).execute()
        ).data or []
        # spending in both periods, as booked in the ledger
        booked = fetch_all(lambda: (
            supabase.table('billing_ledger').select('kind, amount_chf, created_at')
            .eq('tenant_id', tenant_id_str).gte('created_at', prev_since.isoformat()).order('id')))

        def spent(kind, current_period=True):
            return round(-sum(float(r['amount_chf']) for r in booked if r['kind'] == kind
                              and (r['created_at'] >= since.isoformat()) == current_period), 4)
        last = jobs[0] if jobs else None

        from app.knowledge.jobs import issues_of
        sources = fetch_all(lambda: (
            supabase.table('tenant_sources')
            .select("source_type, status, indexed_chunks, warnings")
            .eq('tenant_id', tenant_id_str).order('id')
        ))
        from app.knowledge.calendar import dedupe_events
        upcoming = len(dedupe_events(
            supabase.table('tenant_events').select("series, zone, event_date")
            .eq('tenant_id', tenant_id_str)
            .gte('event_date', date.today().isoformat())
            .lte('event_date', (date.today() + timedelta(days=13)).isoformat())
            .limit(1000).execute().data or []
        ))
        open_findings = (
            supabase.table('chat_findings').select("id", count="exact")
            .eq('tenant_id', tenant_id_str).eq('status', 'open').limit(1).execute()
        ).count or 0
        balance = (
            supabase.table('user_billing').select("balance_chf")
            .eq('user_id', current_user.id).limit(1).execute()
        ).data

        return jsonify({
            "days": days,
            "is_active": tenant.get('is_active') is not False,
            "widget_enabled": (tenant.get('widget_config') or {}).get('widget_enabled') is not False,
            "auto_recrawl": bool(tenant.get('auto_recrawl')),
            "recrawl_interval_days": tenant.get('recrawl_interval_days'),
            "automation": _automation(tenant, jobs, now),
            "usage": {
                "conversations": len({r['conversation_id'] for r in current}),
                "conversations_prev": len({r['conversation_id'] for r in previous}),
                "questions": len(current),
                "questions_prev": len(previous),
                "series": series,
                "latest": [{"question": (r['user_message'] or '')[:160], "at": r['created_at']} for r in current[:5]],
                "open_findings": open_findings,
            },
            "costs": {
                "chat_chf": spent('answer'),
                "chat_prev_chf": spent('answer', current_period=False),
                "learning_chf": spent('learning'),
                "review_chf": spent('review'),
                "balance_chf": float(balance[0]['balance_chf']) if balance else 0.0,
            },
            "knowledge": {
                "pages": sum(1 for s in sources if s['source_type'] == 'URL'),
                "files": sum(1 for s in sources if s['source_type'] != 'URL'),
                "sections": sum(int(s.get('indexed_chunks') or 0) for s in sources),
                "needs_attention": sum(1 for s in sources if s.get('status') == 'ERROR' or issues_of(s.get('warnings'))),
                "upcoming_dates": upcoming,
            },
            "last_crawl": last and {
                "id": last['id'], "start_url": last['start_url'], "status": last['status'],
                "created_at": last['created_at'], "finished_at": last.get('finished_at'),
                "trigger": last.get('trigger'),
                "counts": (last.get('report') or {}).get('counts'),
            },
        }), 200
    except Exception as e:
        error_logger.error(f"Error building tenant overview for {tenant_id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to load overview"}), 500


# ── Conversation review findings (Insights) ──────────────────────────────────

def _owned(tenant_id, user_id, columns="id"):
    rows = supabase.table('tenants').select(columns).eq('id', str(tenant_id)).eq('user_id', user_id).limit(1).execute().data
    return rows[0] if rows else None


@tenants_bp.route('/<uuid:tenant_id>/insights/findings', methods=['GET'])
@token_required
def list_findings(current_user, tenant_id):
    """What the conversation review found, newest first, plus review status."""
    from datetime import datetime, timedelta, timezone
    try:
        tenant = _owned(tenant_id, current_user.id, "id, review_chats, review_interval_days")
        if not tenant:
            return jsonify({"error": "Tenant not found or access denied"}), 404
        status = request.args.get('status', 'open')
        query = (supabase.table('chat_findings')
                 .select("id, conversation_id, log_id, kind, question, topic, problem, suggestion, status, created_at, resolved_at")
                 .eq('tenant_id', str(tenant_id)))
        if status in ('open', 'resolved', 'dismissed'):
            query = query.eq('status', status)
        findings = query.order('created_at', desc=True).limit(500).execute().data or []

        counts = {}
        for st in ('open', 'resolved', 'dismissed'):
            counts[st] = (supabase.table('chat_findings').select("id", count="exact")
                          .eq('tenant_id', str(tenant_id)).eq('status', st).limit(1).execute()).count or 0
        since = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        reviews = fetch_all(lambda: (supabase.table('chat_reviews').select("reviewed_at, cost_chf")
                                     .eq('tenant_id', str(tenant_id)).gte('reviewed_at', since)
                                     .order('reviewed_at', desc=True).order('conversation_id')))
        from app.ai_models import RATES
        rate = RATES.get("review", RATES["chat"])
        return jsonify({
            "findings": findings,
            "counts": counts,
            "review": {
                "enabled": bool(tenant.get('review_chats')),
                "interval_days": tenant.get('review_interval_days') or 1,
                "last_run": reviews[0]['reviewed_at'] if reviews else None,
                "reviewed_30d": len(reviews),
                "cost_30d_chf": round(sum(float(r.get('cost_chf') or 0) for r in reviews), 4),
                "est_chf_per_conversation": round(2000 / 1_000_000 * rate["input"] + 200 / 1_000_000 * rate["output"], 4),
            },
        }), 200
    except Exception as e:
        error_logger.error(f"Error listing findings for {tenant_id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to load findings"}), 500


@tenants_bp.route('/<uuid:tenant_id>/insights/findings/<int:finding_id>', methods=['PATCH'])
@token_required
def update_finding(current_user, tenant_id, finding_id):
    from datetime import datetime, timezone
    try:
        if not _owned(tenant_id, current_user.id):
            return jsonify({"error": "Tenant not found or access denied"}), 404
        status = (request.get_json(silent=True) or {}).get('status')
        if status not in ('open', 'resolved', 'dismissed'):
            return jsonify({"error": "status must be open, resolved or dismissed"}), 400
        resp = (supabase.table('chat_findings')
                .update({"status": status, "resolved_at": None if status == 'open' else datetime.now(timezone.utc).isoformat()})
                .eq('id', finding_id).eq('tenant_id', str(tenant_id)).execute())
        if not resp.data:
            return jsonify({"error": "Finding not found"}), 404
        return jsonify(resp.data[0]), 200
    except Exception as e:
        error_logger.error(f"Error updating finding {finding_id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to update finding"}), 500


@tenants_bp.route('/<uuid:tenant_id>/insights/review', methods=['POST'])
@token_required
def run_review_now(current_user, tenant_id):
    """Reviews this chatbot's finished conversations now instead of at the next hourly run."""
    try:
        tenant = _owned(tenant_id, current_user.id, "id, review_chats")
        if not tenant:
            return jsonify({"error": "Tenant not found or access denied"}), 404
        if not tenant.get('review_chats'):
            return jsonify({"error": "Conversation review is switched off"}), 409
        from app.data_processing.tasks import review_conversations_task
        review_conversations_task.delay(tenant_id=str(tenant_id))
        return jsonify({"status": "queued"}), 202
    except Exception as e:
        error_logger.error(f"Error starting review for {tenant_id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to start review"}), 500


# ── Look of the widget, taken from the customer's website ────────────────────

@tenants_bp.route('/<uuid:tenant_id>/branding', methods=['POST'])
@limiter.limit("10 per minute")
@token_required
def suggest_branding(current_user, tenant_id):
    """
    Reads brand colours, logo and name from the start page of the chatbot's
    latest website crawl (or the given url). Nothing is saved: the
    configurator applies it for the customer to review.
    """
    from app.knowledge.branding import read_branding
    from app.security.url_guard import is_public_url

    if not _owned(tenant_id, current_user.id):
        return jsonify({"error": "Tenant not found or access denied"}), 404
    url = ((request.get_json(silent=True) or {}).get('url') or '').strip()
    if not url:
        jobs = supabase.table('crawling_jobs').select('start_url, single_page_only') \
            .eq('tenant_id', str(tenant_id)).order('created_at', desc=True).limit(50).execute().data or []
        # a whole-site crawl starts at the home page; a single page is only a fallback
        job = next((j for j in jobs if not j.get('single_page_only')), jobs[0] if jobs else None)
        url = job['start_url'] if job else ''
    if not url:
        return jsonify({"error": "no_website"}), 404
    if not is_public_url(url):
        return jsonify({"error": "Only public http(s) URLs can be read"}), 400
    try:
        return jsonify(read_branding(url)), 200
    except Exception as e:
        error_logger.warning(f"Reading the look of {url} for tenant {tenant_id} failed: {e}")
        return jsonify({"error": "unreadable", "url": url}), 422
