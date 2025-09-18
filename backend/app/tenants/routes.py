from flask import Blueprint, request, jsonify
from app.database.supabase_client import supabase
from app.auth.decorators import token_required
from app.models.database import Tenant, TenantFineTune, SourceType
from app.data_processing.tasks import process_local_filepath, process_urls, crawl_links_task
from app.logging_config import error_logger
from app import celery
from uuid import uuid4
import os

tenants_bp = Blueprint('tenants', __name__)

@tenants_bp.route('', methods=['POST'])
@token_required
def create_tenant(current_user):
    try:
        data = request.get_json()
        if not all(k in data for k in ['name', 'intro_message', 'system_persona', 'rag_prompt_template']):
            return jsonify({"error": "Missing required tenant fields"}), 400

        tenant_id = uuid4()
        tenant_data = {
            "id": str(tenant_id), "user_id": str(current_user.id), "name": data['name'],
            "intro_message": data['intro_message'], "system_persona": data['system_persona'],
            "rag_prompt_template": data['rag_prompt_template'], "doc_language": data.get('doc_language'),
            "doc_description": data.get('doc_description'), "source_description": data.get('source_description'),
            "last_updated_description": data.get('last_updated_description'), "translation_target": data.get('translation_target'),
        }
        supabase.table('tenants').insert(tenant_data).execute()

        fine_tune_rules = data.get('fine_tune_rules', [])
        if fine_tune_rules:
            rules_to_insert = [{"tenant_id": str(tenant_id), "trigger": r['trigger'], "instruction": r['instruction']} for r in fine_tune_rules]
            supabase.table('tenant_fine_tune').insert(rules_to_insert).execute()

        created_tenant = supabase.table('tenants').select("*, tenant_fine_tune(*)").eq('id', str(tenant_id)).single().execute()
        return jsonify(created_tenant.data), 201
    except Exception as e:
        error_logger.error(f"Error creating tenant for user {current_user.id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to create tenant", "details": str(e)}), 500

@tenants_bp.route('', methods=['GET'])
@token_required
def get_tenants(current_user):
    try:
        tenants = supabase.table('tenants').select("*, tenant_fine_tune(*), tenant_sources(*)").eq('user_id', current_user.id).execute()
        return jsonify(tenants.data), 200
    except Exception as e:
        error_logger.error(f"Error getting tenants for user {current_user.id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to retrieve tenants", "details": str(e)}), 500

@tenants_bp.route('/<uuid:tenant_id>', methods=['GET'])
@token_required
def get_tenant(current_user, tenant_id):
    try:
        tenant_id_str = str(tenant_id)
        tenant = supabase.table('tenants').select("*, tenant_fine_tune(*), tenant_sources(*)").eq('id', tenant_id_str).eq('user_id', current_user.id).single().execute()
        if not tenant.data:
            return jsonify({"error": "Tenant not found or access denied"}), 404
        return jsonify(tenant.data), 200
    except Exception as e:
        error_logger.error(f"Error getting tenant {tenant_id} for user {current_user.id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to retrieve tenant", "details": str(e)}), 500

@tenants_bp.route('/<uuid:tenant_id>', methods=['PUT'])
@token_required
def update_tenant(current_user, tenant_id):
    try:
        data = request.get_json()
        tenant_id_str = str(tenant_id)
        tenant_check = supabase.table('tenants').select("id").eq('id', tenant_id_str).eq('user_id', current_user.id).single().execute()
        if not tenant_check.data:
            return jsonify({"error": "Tenant not found or access denied"}), 404

        allowed_fields = ['name', 'intro_message', 'system_persona', 'rag_prompt_template', 'doc_language', 'doc_description', 'source_description', 'last_updated_description', 'translation_target']
        tenant_update_data = {k: v for k, v in data.items() if k in allowed_fields}
        if tenant_update_data:
            supabase.table('tenants').update(tenant_update_data).eq('id', tenant_id_str).execute()

        if 'fine_tune_rules' in data:
            supabase.table('tenant_fine_tune').delete().eq('tenant_id', tenant_id_str).execute()
            new_rules = data['fine_tune_rules']
            if new_rules:
                rules_to_insert = [{"tenant_id": tenant_id_str, "trigger": r['trigger'], "instruction": r['instruction']} for r in new_rules]
                supabase.table('tenant_fine_tune').insert(rules_to_insert).execute()

        updated_tenant = supabase.table('tenants').select("*, tenant_fine_tune(*)").eq('id', tenant_id_str).single().execute()
        return jsonify(updated_tenant.data), 200
    except Exception as e:
        error_logger.error(f"Error updating tenant {tenant_id} for user {current_user.id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to update tenant", "details": str(e)}), 500

@tenants_bp.route('/<uuid:tenant_id>', methods=['DELETE'])
@token_required
def delete_tenant(current_user, tenant_id):
    try:
        tenant_id_str = str(tenant_id)
        tenant_check = supabase.table('tenants').select("id").eq('id', tenant_id_str).eq('user_id', current_user.id).single().execute()
        if not tenant_check.data:
            return jsonify({"error": "Tenant not found or access denied"}), 404

        supabase.table('tenant_fine_tune').delete().eq('tenant_id', tenant_id_str).execute()
        supabase.table('tenant_sources').delete().eq('tenant_id', tenant_id_str).execute()
        supabase.table('tenants').delete().eq('id', tenant_id_str).execute()
        return jsonify({"message": "Tenant deleted successfully"}), 200
    except Exception as e:
        error_logger.error(f"Error deleting tenant {tenant_id} for user {current_user.id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to delete tenant", "details": str(e)}), 500

@tenants_bp.route('/<uuid:tenant_id>/sources', methods=['GET'])
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
        return jsonify({"error": "Failed to retrieve sources", "details": str(e)}), 500

@tenants_bp.route('/<uuid:tenant_id>/sources/upload', methods=['POST'])
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

    try:
        tenant_upload_path = os.path.join('uploads', tenant_id_str)
        os.makedirs(tenant_upload_path, exist_ok=True)
        filepath = os.path.join(tenant_upload_path, file.filename)
        file.save(filepath)

        source_data = {"tenant_id": tenant_id_str, "source_type": SourceType.FILE, "source_location": file.filename, "status": "QUEUED"}
        source_record = supabase.table('tenant_sources').insert(source_data).execute()
        source_id = source_record.data[0]['id']

        task = process_local_filepath.delay(filepath, file.filename, source_id, tenant_id_str)

        return jsonify({"task_id": task.id}), 202
    except Exception as e:
        error_logger.error(f"Error processing file upload for tenant {tenant_id_str}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": f"Failed to process file: {str(e)}"}), 500

@tenants_bp.route('/<uuid:tenant_id>/sources/crawl', methods=['POST'])
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

        sources_to_insert = [{"tenant_id": tenant_id_str, "source_type": SourceType.URL, "source_location": url, "status": "QUEUED"} for url in urls]
        source_records = supabase.table('tenant_sources').insert(sources_to_insert).execute()
        urls_with_ids = [(rec['source_location'], rec['id']) for rec in source_records.data]

        task = process_urls.delay(urls_with_ids, tenant_id_str)

        return jsonify({"task_id": task.id}), 202
    except Exception as e:
        error_logger.error(f"Error processing crawl for tenant {tenant_id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": f"Failed to process URLs: {str(e)}"}), 500

@tenants_bp.route('/<uuid:tenant_id>/sources/discover', methods=['POST'])
@token_required
def discover_links(current_user, tenant_id):
    try:
        data = request.get_json()
        start_url = data.get('url')
        tenant_id_str = str(tenant_id)
        if not start_url:
            return jsonify({"error": "URL is required"}), 400

        tenant_check = supabase.table('tenants').select("id").eq('id', tenant_id_str).eq('user_id', current_user.id).single().execute()
        if not tenant_check.data:
            return jsonify({"error": "Tenant not found or access denied"}), 404

        task = crawl_links_task.delay(start_url)

        return jsonify({"task_id": task.id}), 202
    except Exception as e:
        error_logger.error(f"Error discovering links for tenant {tenant_id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": f"Failed to discover links: {str(e)}"}), 500

@tenants_bp.route('/<uuid:tenant_id>/sources/<int:source_id>', methods=['DELETE'])
@token_required
def delete_source(current_user, tenant_id, source_id):
    try:
        tenant_id_str = str(tenant_id)
        tenant_check = supabase.table('tenants').select("id").eq('id', tenant_id_str).eq('user_id', current_user.id).single().execute()
        if not tenant_check.data:
            return jsonify({"error": "Tenant not found or access denied"}), 404

        source_check = supabase.table('tenant_sources').select("id").eq('id', source_id).eq('tenant_id', tenant_id_str).single().execute()
        if not source_check.data:
            return jsonify({"error": "Source not found or access denied"}), 404

        supabase.table('tenant_sources').delete().eq('id', source_id).execute()
        return jsonify({"message": "Source deleted successfully. Note: Vector data may still exist and will be cleaned up later."}), 200
    except Exception as e:
        error_logger.error(f"Error deleting source {source_id} for tenant {tenant_id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to delete source", "details": str(e)}), 500

@tenants_bp.route('/tasks/<string:task_id>', methods=['GET'])
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
        return jsonify({"error": "Failed to get task status", "details": str(e)}), 500
