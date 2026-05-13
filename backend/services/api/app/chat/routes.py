from flask import Blueprint, request, jsonify
from app.database.supabase_client import supabase
from app.logging_config import error_logger
from app.chat.tasks import chat_task
from app.billing.services import BillingService
from app import limiter
from celery.result import AsyncResult
import uuid

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/<uuid:tenant_id>', methods=['POST'])
@limiter.limit("30 per minute")
def handle_chat(tenant_id):
    try:
        data = request.get_json()
        query = data.get('query')
        chat_history_json = data.get('chat_history', [])
        conversation_id_str = data.get('conversation_id')

        if not query:
            return jsonify({"error": "No query provided"}), 400

        if not conversation_id_str:
            return jsonify({"error": "No conversation_id provided"}), 400

        try:
            conversation_id = uuid.UUID(conversation_id_str)
        except ValueError:
            return jsonify({"error": "Invalid conversation_id format"}), 400

        # Check tenant owner's balance — retry up to 2 times on transient Supabase timeouts
        import time as _time
        user_id = None
        for attempt in range(3):
            try:
                tenant_response = supabase.table('tenants').select('user_id').eq('id', str(tenant_id)).single().execute()
                if not tenant_response.data:
                    return jsonify({"error": "Tenant not found"}), 404
                user_id = tenant_response.data['user_id']
                balance = BillingService.check_balance(user_id)
                if balance <= 0:
                    return jsonify({"error": "Insufficient balance. Please recharge."}), 402
                break  # success
            except Exception as e:
                if attempt < 2:
                    error_logger.warning(f"Billing check attempt {attempt+1} failed for tenant {tenant_id}: {e} — retrying")
                    _time.sleep(0.5)
                else:
                    # All retries exhausted — log and allow through rather than blocking on a transient error
                    error_logger.error(f"Billing check failed after 3 attempts for tenant {tenant_id}: {e}", exc_info=True)

        task = chat_task.delay(str(tenant_id), query, chat_history_json, str(conversation_id), str(user_id))

        return jsonify({"task_id": task.id}), 202
    except Exception as e:
        error_logger.error(f"Error in chat handler for tenant {tenant_id}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@chat_bp.route('/task/<string:task_id>/status', methods=['GET'])
def get_task_status(task_id):
    task = AsyncResult(task_id)
    timeout = min(int(request.args.get('timeout', 25)), 30)  # cap at 30s

    # Long poll: hold the connection until the task finishes or we time out
    import time
    deadline = time.time() + timeout
    while not task.ready() and time.time() < deadline:
        time.sleep(0.5)

    response = {
        "task_id": task_id,
        "state": task.state,
    }
    if task.state == 'FAILURE':
        response['result'] = str(task.info)
    elif task.state == 'SUCCESS':
        response['result'] = task.result
    else:
        response['result'] = str(task.info)
    return jsonify(response)

from datetime import datetime, timedelta, timezone

@chat_bp.route('/<uuid:tenant_id>/analytics', methods=['GET'])
def get_chat_analytics(tenant_id):
    try:
        timeframe_hours = request.args.get('timeframe', 24, type=int)
        interval = request.args.get('interval', 'hour')  # 'minute', '5-minute', 'hour', or 'day'
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(hours=timeframe_hours)

        # Map frontend interval names to SQL-compatible values
        interval_map = {
            'minute': 'minute',
            '5-minute': '5 minutes',
            'hour': '1 hour',
            'day': '1 day',
        }
        sql_interval = interval_map.get(interval, '1 hour')

        response = supabase.rpc('analytics_time_buckets', {
            'p_tenant_id': str(tenant_id),
            'p_start_time': start_time.isoformat(),
            'p_interval': sql_interval,
        }).execute()

        return jsonify(response.data or [])

    except Exception as e:
        error_logger.error(f"Error in chat analytics for tenant {tenant_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@chat_bp.route('/<uuid:tenant_id>/conversations', methods=['GET'])
def get_conversations(tenant_id):
    try:
        response = supabase.table('chat_logs').select('conversation_id, created_at, user_message, cost_chf').eq('tenant_id', str(tenant_id)).order('created_at', desc=True).execute()

        if not hasattr(response, 'data'):
            error_logger.error(f"Supabase response for tenant {tenant_id} is missing 'data' attribute: {response}")
            return jsonify({"error": "Invalid response from database"}), 500

        # Aggregate conversation data
        conversations = {}
        for log in response.data:
            c_id = log['conversation_id']
            if c_id not in conversations:
                conversations[c_id] = {
                    'conversation_id': c_id,
                    'last_active': log['created_at'],
                    'message_count': 0,
                    'total_cost': 0.0,
                    'first_message': log['user_message']
                }
            
            conversations[c_id]['message_count'] += 1
            conversations[c_id]['total_cost'] += (log.get('cost_chf') or 0)
            # Since we iterate in descending order, the last assignment will be the first message
            if log['user_message']:
                conversations[c_id]['first_message'] = log['user_message']

        return jsonify(list(conversations.values()))

    except Exception as e:
        error_logger.error(f"Error in get_conversations for tenant {tenant_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@chat_bp.route('/<uuid:tenant_id>/conversation/<uuid:conversation_id>', methods=['GET'])
def get_conversation_logs(tenant_id, conversation_id):
    try:
        response = supabase.table('chat_logs').select('*').eq('tenant_id', str(tenant_id)).eq('conversation_id', str(conversation_id)).order('created_at').execute()

        if not hasattr(response, 'data'):
            error_logger.error(f"Supabase response for tenant {tenant_id} is missing 'data' attribute: {response}")
            return jsonify({"error": "Invalid response from database"}), 500

        return jsonify(response.data)

    except Exception as e:
        error_logger.error(f"Error in get_conversation_logs for tenant {tenant_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@chat_bp.route('/<uuid:tenant_id>/intro', methods=['GET'])
def get_intro_message(tenant_id):
    try:
        tenant = supabase.table('tenants').select("intro_message").eq('id', str(tenant_id)).single().execute()
        if not tenant.data:
            return jsonify({"error": f"Tenant '{tenant_id}' not found"}), 404
        return jsonify({"intro_message": tenant.data['intro_message']})
    except Exception as e:
        error_logger.error(f"Error getting intro message for tenant {tenant_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500


# ── Share endpoints ────────────────────────────────────────────────────────────

@chat_bp.route('/<uuid:tenant_id>/conversation/<uuid:conversation_id>/share', methods=['POST'])
@limiter.limit("10 per minute")
def create_share_link(tenant_id, conversation_id):
    """
    Public endpoint — no auth required (end-users have no account token).
    Validates the conversation exists for this tenant, then upserts a share row.
    Idempotent: sharing the same conversation twice returns the same link.
    """
    try:
        tenant_id_str = str(tenant_id)
        conversation_id_str = str(conversation_id)

        # Validate conversation belongs to this tenant (prevents UUID guessing)
        check = (
            supabase.table('chat_logs')
            .select('conversation_id')
            .eq('tenant_id', tenant_id_str)
            .eq('conversation_id', conversation_id_str)
            .limit(1)
            .execute()
        )
        if not check.data:
            return jsonify({"error": "Conversation not found"}), 404

        # Upsert — if already shared, refresh the expiry and return the existing row
        result = (
            supabase.table('shared_conversations')
            .upsert(
                {
                    "conversation_id": conversation_id_str,
                    "tenant_id": tenant_id_str,
                    # expires_at: DB default is now() + 24h, but on conflict we want to
                    # reset the expiry so re-sharing extends the link lifetime.
                },
                on_conflict="conversation_id",
                returning="representation",
            )
            .execute()
        )
        row = result.data[0]
        return jsonify({"share_id": row["id"], "expires_at": row["expires_at"]}), 200

    except Exception as e:
        error_logger.error(f"Error creating share link for conversation {conversation_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to create share link"}), 500


@chat_bp.route('/shared/<uuid:share_id>', methods=['GET'])
def get_shared_conversation(share_id):
    """
    Public endpoint — fetches a shared conversation by its share UUID.
    Returns 410 Gone if the link has expired.
    """
    try:
        from datetime import datetime, timezone
        share_id_str = str(share_id)

        # Look up the share row
        share_resp = (
            supabase.table('shared_conversations')
            .select('*')
            .eq('id', share_id_str)
            .maybe_single()
            .execute()
        )
        if not share_resp.data:
            return jsonify({"error": "Share link not found"}), 404

        share = share_resp.data
        # Check expiry
        expires_at = datetime.fromisoformat(share['expires_at'].replace('Z', '+00:00'))
        if datetime.now(timezone.utc) > expires_at:
            return jsonify({"error": "This share link has expired"}), 410

        conversation_id = share['conversation_id']
        tenant_id = share['tenant_id']

        # Fetch the conversation messages
        logs_resp = (
            supabase.table('chat_logs')
            .select('user_message, ai_message, created_at')
            .eq('tenant_id', tenant_id)
            .eq('conversation_id', conversation_id)
            .order('created_at')
            .execute()
        )

        # Fetch tenant public config for branding
        tenant_resp = (
            supabase.table('tenants')
            .select('widget_config')
            .eq('id', tenant_id)
            .single()
            .execute()
        )
        widget_config = (tenant_resp.data or {}).get('widget_config', {})

        return jsonify({
            "messages":      logs_resp.data or [],
            "widget_config": widget_config,
            "tenant_id":     tenant_id,
            "expires_at":    share['expires_at'],
        }), 200

    except Exception as e:
        error_logger.error(f"Error fetching shared conversation {share_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch shared conversation"}), 500
