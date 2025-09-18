from flask import Blueprint, request, jsonify
from app.database.supabase_client import supabase
from app.logging_config import error_logger
from app.chat.tasks import chat_task
from celery.result import AsyncResult

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/<uuid:tenant_id>', methods=['POST'])
def handle_chat(tenant_id):
    try:
        data = request.get_json()
        query = data.get('query')
        chat_history_json = data.get('chat_history', [])

        if not query:
            return jsonify({"error": "No query provided"}), 400

        task = chat_task.delay(str(tenant_id), query, chat_history_json)

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
