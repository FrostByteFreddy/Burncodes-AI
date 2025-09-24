from flask import Blueprint, request, jsonify
from app.database.supabase_client import supabase
from app.logging_config import error_logger
from app.chat.tasks import chat_task
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

        task = chat_task.delay(str(tenant_id), query, chat_history_json, str(conversation_id))

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
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(hours=timeframe_hours)

        # Fetch the raw chat logs from the database
        response = supabase.table('chat_logs').select('created_at').eq('tenant_id', str(tenant_id)).gte('created_at', start_time.isoformat()).execute()

        if not hasattr(response, 'data'):
            error_logger.error(f"Supabase response for tenant {tenant_id} is missing 'data' attribute: {response}")
            return jsonify({"error": "Invalid response from database"}), 500

        # Process the data in Python
        hourly_counts = {}
        for log in response.data:
            created_at = datetime.fromisoformat(log['created_at'])
            hour_bucket = created_at.strftime('%Y-%m-%dT%H:00:00+00:00')
            hourly_counts[hour_bucket] = hourly_counts.get(hour_bucket, 0) + 1

        # Format the result into a JSON array
        analytics_data = [{"time_bucket": hour, "message_count": count} for hour, count in hourly_counts.items()]
        analytics_data.sort(key=lambda x: x['time_bucket'])

        return jsonify(analytics_data)

    except Exception as e:
        error_logger.error(f"Error in chat analytics for tenant {tenant_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

@chat_bp.route('/<uuid:tenant_id>/conversations', methods=['GET'])
def get_conversations(tenant_id):
    try:
        response = supabase.table('chat_logs').select('conversation_id, created_at').eq('tenant_id', str(tenant_id)).order('created_at', desc=True).execute()

        if not hasattr(response, 'data'):
            error_logger.error(f"Supabase response for tenant {tenant_id} is missing 'data' attribute: {response}")
            return jsonify({"error": "Invalid response from database"}), 500

        # Get unique conversations
        conversations = {}
        for log in response.data:
            if log['conversation_id'] not in conversations:
                conversations[log['conversation_id']] = log['created_at']

        return jsonify([{'conversation_id': k, 'created_at': v} for k, v in conversations.items()])

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
