from flask import Blueprint, request, jsonify
from app.database.supabase_client import supabase
from app.logging_config import error_logger
from app.chat.tasks import chat_task
from app.billing.services import BillingService
from celery.result import AsyncResult
import uuid

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/<uuid:tenant_id>', methods=['POST'])
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

        # Check tenant owner's balance
        try:
            tenant_response = supabase.table('tenants').select('user_id').eq('id', str(tenant_id)).single().execute()
            if not tenant_response.data:
                return jsonify({"error": "Tenant not found"}), 404
            
            user_id = tenant_response.data['user_id']
            balance = BillingService.check_balance(user_id)
            
            if balance <= 0:
                return jsonify({"error": "Insufficient balance. Please recharge."}), 402
                
        except Exception as e:
            error_logger.error(f"Error checking balance for tenant {tenant_id}: {e}")
            return jsonify({"error": "Error checking billing status"}), 500

        task = chat_task.delay(str(tenant_id), query, chat_history_json, str(conversation_id), str(user_id))

        return jsonify({"task_id": task.id}), 202
    except Exception as e:
        error_logger.error(f"Error in chat handler for tenant {tenant_id}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@chat_bp.route('/task/<string:task_id>/status', methods=['GET'])
def get_task_status(task_id):
    task = AsyncResult(task_id)
    response = {
        "task_id": task_id,
        "state": task.state,
    }
    if task.state == 'FAILURE':
        response['result'] = str(task.info)  # Convert exception to string
    elif task.state == 'SUCCESS':
        response['result'] = task.result
    else:
        # For PENDING or other states, info might be a string or dict
        response['result'] = str(task.info)
    return jsonify(response)

from datetime import datetime, timedelta, timezone

@chat_bp.route('/<uuid:tenant_id>/analytics', methods=['GET'])
def get_chat_analytics(tenant_id):
    try:
        timeframe_hours = request.args.get('timeframe', 24, type=int)
        interval = request.args.get('interval', 'hour') # 'minute', 'hour', or 'day'
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(hours=timeframe_hours)

        response = supabase.table('chat_logs').select('created_at').eq('tenant_id', str(tenant_id)).gte('created_at', start_time.isoformat()).execute()

        if not hasattr(response, 'data'):
            error_logger.error(f"Supabase response for tenant {tenant_id} is missing 'data' attribute: {response}")
            return jsonify({"error": "Invalid response from database"}), 500

        time_format_map = {
            'minute': '%Y-%m-%dT%H:%M:00+00:00',
            'hour': '%Y-%m-%dT%H:00:00+00:00',
            'day': '%Y-%m-%dT00:00:00+00:00'
        }

        time_format = time_format_map.get(interval, '%Y-%m-%dT%H:00:00+00:00')

        counts = {}
        for log in response.data:
            created_at = datetime.fromisoformat(log['created_at'])
            time_bucket = created_at.strftime(time_format)
            counts[time_bucket] = counts.get(time_bucket, 0) + 1

        analytics_data = [{"time_bucket": bucket, "message_count": count} for bucket, count in counts.items()]
        analytics_data.sort(key=lambda x: x['time_bucket'])

        return jsonify(analytics_data)

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
