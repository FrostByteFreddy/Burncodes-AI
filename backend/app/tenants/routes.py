from flask import Blueprint, request, jsonify, Response
from app.database.supabase_client import supabase, bucket_name
from app.auth.decorators import token_required
from app.models.database import Tenant, TenantFineTune, SourceType
from app.data_processing.document_tasks import process_s3_file
from app.data_processing.crawling_tasks import process_urls, crawl_links_task
from app.data_processing.processor import process_fine_tune_rules, delete_fine_tune_vectors
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.logging_config import error_logger
from app import celery
from uuid import uuid4
import os
from typing import List

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
            "id": str(tenant_id), 
            "user_id": str(current_user.id), 
            "name": data['name'],
            "intro_message": data['intro_message'], 
            "system_persona": data['system_persona'],
            "rag_prompt_template": data['rag_prompt_template'], 
            "doc_language": data.get('doc_language'),
            "translation_target": data.get('translation_target'),
        }
        supabase.table('tenants').insert(tenant_data).execute()

        fine_tune_rules_data = data.get('fine_tune_rules', [])
        if fine_tune_rules_data:
            rules_to_insert = [{"tenant_id": str(tenant_id), "trigger": r['trigger'], "instruction": r['instruction']} for r in fine_tune_rules_data]
            inserted_rules_response = supabase.table('tenant_fine_tune').insert(rules_to_insert).execute()

            inserted_rules = inserted_rules_response.data

            # Convert dicts to TenantFineTune objects
            fine_tune_rules_models = [TenantFineTune(**rule) for rule in inserted_rules]

            # Initialize embeddings
            embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

            # Process rules and get vector IDs
            vector_ids = process_fine_tune_rules(fine_tune_rules_models, tenant_id, embeddings)

            if vector_ids and len(vector_ids) == len(inserted_rules):
                updates = [{"id": rule['id'], "vector_id": vec_id} for rule, vec_id in zip(inserted_rules, vector_ids)]
                for update in updates:
                    supabase.table('tenant_fine_tune').update({"vector_id": update["vector_id"]}).eq('id', update["id"]).execute()

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

@tenants_bp.route('/<uuid:tenant_id>/public', methods=['GET'])
def get_public_tenant(tenant_id):
    try:
        tenant_id_str = str(tenant_id)
        tenant = supabase.table('tenants').select("name, widget_config").eq('id', tenant_id_str).single().execute()
        if not tenant.data:
            return jsonify({"error": "Tenant not found"}), 404
        return jsonify(tenant.data), 200
    except Exception as e:
        error_logger.error(f"Error getting public tenant {tenant_id}: {e}", exc_info=True)
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

        allowed_fields = ['name', 'intro_message', 'system_persona', 'rag_prompt_template', 'doc_language', 'translation_target', 'widget_config']
        tenant_update_data = {k: v for k, v in data.items() if k in allowed_fields}
        if tenant_update_data:
            supabase.table('tenants').update(tenant_update_data).eq('id', tenant_id_str).execute()

        if 'fine_tune_rules' in data:
            # Get existing fine_tune rules to extract vector_ids for deletion
            existing_rules_response = supabase.table('tenant_fine_tune').select('id, vector_id').eq('tenant_id', tenant_id_str).execute()
            existing_rules = existing_rules_response.data
            vector_ids_to_delete = [rule['vector_id'] for rule in existing_rules if rule.get('vector_id')]

            # Initialize embeddings for potential deletion/creation
            embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

            if vector_ids_to_delete:
                delete_fine_tune_vectors(vector_ids_to_delete, tenant_id, embeddings)

            # Delete old rules from the database
            supabase.table('tenant_fine_tune').delete().eq('tenant_id', tenant_id_str).execute()

            # Insert new rules and process them for vectorization
            new_rules_data = data.get('fine_tune_rules', [])
            if new_rules_data:
                rules_to_insert = [{"tenant_id": tenant_id_str, "trigger": r['trigger'], "instruction": r['instruction']} for r in new_rules_data]
                inserted_rules_response = supabase.table('tenant_fine_tune').insert(rules_to_insert).execute()
                inserted_rules = inserted_rules_response.data

                fine_tune_rules_models = [TenantFineTune(**rule) for rule in inserted_rules]

                vector_ids = process_fine_tune_rules(fine_tune_rules_models, tenant_id, embeddings)

                if vector_ids and len(vector_ids) == len(inserted_rules):
                    updates = [{"id": rule['id'], "vector_id": vec_id} for rule, vec_id in zip(inserted_rules, vector_ids)]
                    for update in updates:
                        supabase.table('tenant_fine_tune').update({"vector_id": update["vector_id"]}).eq('id', update["id"]).execute()

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

        # First, get the fine-tuning rules to find the vector IDs
        existing_rules_response = supabase.table('tenant_fine_tune').select('id, vector_id').eq('tenant_id', tenant_id_str).execute()
        existing_rules = existing_rules_response.data
        vector_ids_to_delete = [rule['vector_id'] for rule in existing_rules if rule.get('vector_id')]

        if vector_ids_to_delete:
            embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
            delete_fine_tune_vectors(vector_ids_to_delete, tenant_id, embeddings)

        # Now, delete the records from the database
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

    s3_path = f"{tenant_id_str}/{file.filename}"
    try:
        # Upload the file to Supabase Storage.
        # We don't need to check the response object.
        # If this fails, it will raise an exception.
        supabase.storage.from_(bucket_name).upload(
            path=s3_path,
            file=file.read(),
            file_options={"content-type": file.content_type}
        )

        # The source_location will now be the S3 path
        source_data = {"tenant_id": tenant_id_str, "source_type": SourceType.FILE, "source_location": s3_path, "status": "QUEUED"}
        source_record = supabase.table('tenant_sources').insert(source_data).execute()
        source_id = source_record.data[0]['id']

        # Call the new Celery task with the S3 path
        task = process_s3_file.delay(s3_path, file.filename, source_id, tenant_id_str)

        return jsonify({"task_id": task.id}), 202
    except Exception as e:
        error_logger.error(f"Error processing file upload for tenant {tenant_id_str}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        # Attempt to clean up the uploaded file if an error occurs
        try:
            supabase.storage.from_(bucket_name).remove([s3_path])
        except Exception as cleanup_e:
            error_logger.error(f"Failed to clean up S3 file {s3_path} after an error: {cleanup_e}", extra={'user_id': current_user.id})
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
        single_page_only = data.get('single_page_only', False)
        excluded_urls = data.get('excluded_urls', [])
        tenant_id_str = str(tenant_id)

        if not start_url:
            return jsonify({"error": "URL is required"}), 400

        tenant_check = supabase.table('tenants').select("id").eq('id', tenant_id_str).eq('user_id', current_user.id).single().execute()
        if not tenant_check.data:
            return jsonify({"error": "Tenant not found or access denied"}), 404

        task = crawl_links_task.delay(
            tenant_id=tenant_id,
            start_url=start_url,
            single_page_only=single_page_only,
            excluded_urls=excluded_urls
        )

        return jsonify({"task_id": task.id}), 202
    except Exception as e:
        error_logger.error(f"Error discovering links for tenant {tenant_id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": f"Failed to discover links: {str(e)}"}), 500

@tenants_bp.route('/<uuid:tenant_id>/crawling_jobs', methods=['GET'])
@token_required
def get_crawling_jobs(current_user, tenant_id):
    try:
        tenant_id_str = str(tenant_id)
        tenant_check = supabase.table('tenants').select("id").eq('id', tenant_id_str).eq('user_id', current_user.id).single().execute()
        if not tenant_check.data:
            return jsonify({"error": "Tenant not found or access denied"}), 404

        jobs = supabase.table('crawling_jobs').select("*").eq('tenant_id', tenant_id_str).order('created_at', desc=True).execute()
        return jsonify(jobs.data), 200
    except Exception as e:
        error_logger.error(f"Error getting crawling jobs for tenant {tenant_id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to retrieve crawling jobs", "details": str(e)}), 500

@tenants_bp.route('/<uuid:tenant_id>/crawling_jobs/<int:job_id>/progress', methods=['GET'])
@token_required
def get_crawling_job_progress(current_user, tenant_id, job_id):
    try:
        from app.models.database import CrawlingStatus
        tenant_id_str = str(tenant_id)

        # Security check Step 1: Verify the user owns the tenant specified in the URL
        tenant_check = supabase.table('tenants').select("id").eq('id', tenant_id_str).eq('user_id', current_user.id).single().execute()
        if not tenant_check.data:
            return jsonify({"error": "Tenant not found or access denied"}), 404

        # Security check Step 2: Verify the job belongs to that tenant
        job_check = supabase.table('crawling_jobs').select("id").eq('id', job_id).eq('tenant_id', tenant_id_str).single().execute()
        if not job_check.data:
            return jsonify({"error": "Job not found or not part of this tenant"}), 404

        # Fetch all task statuses for the job
        tasks_response = supabase.table('crawling_tasks').select('status').eq('job_id', job_id).execute()

        from collections import Counter
        # Count the statuses in Python
        status_list = [task['status'] for task in tasks_response.data]
        db_counts = Counter(status_list)

        # Initialize counts for all possible statuses and merge the db counts
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
        return jsonify({"error": "Failed to retrieve job progress", "details": str(e)}), 500

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

@tenants_bp.route('/widget.js', methods=['GET'])
def get_widget_script():
    try:
        # Get API and Frontend URLs from environment variables
        api_base_url = os.environ.get('API_BASE_URL', 'http://localhost:5000')
        frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')

        js_content = f"""
(function() {{
    const scriptTag = document.currentScript;
    const tenantId = scriptTag.getAttribute('data-tenant-id');
    const apiBaseUrl = "{api_base_url}".replace(/\/$/, "");
    const frontendUrl = "{frontend_url}".replace(/\/$/, "");

    if (!tenantId) {{
        console.error('SwiftAnswer Widget: data-tenant-id attribute is missing.');
        return;
    }}

    // Create container for the widget
    const container = document.createElement('div');
    container.id = 'swiftanswer-widget-container';
    container.style.position = 'fixed';
    container.style.bottom = '20px';
    container.style.right = '20px';
    container.style.zIndex = '9999';
    container.style.display = 'flex';
    container.style.flexDirection = 'column';
    container.style.alignItems = 'flex-end';
    document.body.appendChild(container);

    // Create Iframe
    const iframe = document.createElement('iframe');
    iframe.src = `${{frontendUrl}}/chat/${{tenantId}}?widget`;
    iframe.style.width = '400px';
    iframe.style.height = '600px';
    iframe.style.border = 'none';
    iframe.style.borderRadius = '10px';
    iframe.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
    iframe.style.marginBottom = '10px';
    iframe.style.display = 'none'; // Hidden by default
    iframe.style.backgroundColor = 'white';
    container.appendChild(iframe);

    // Fetch Tenant Config for Launcher Appearance
    fetch(`${{apiBaseUrl}}/api/tenants/${{tenantId}}/public`)
        .then(response => response.json())
        .then(data => {{
            if (data.error) {{
                console.error('SwiftAnswer Widget: Failed to load tenant config.', data.error);
                return;
            }}

            const config = data.widget_config || {{}};
            const styles = config.component_styles || {{}};
            const palette = config.color_palette || [];

            const getPaletteColor = (colorId) => {{
                const color = palette.find(c => c.id === colorId);
                return color ? color.value : colorId; // Fallback to ID if not found (shouldn't happen if config is valid)
            }};

            const launcherBgColor = getPaletteColor(styles.launcher_background_color || 'c_primary') || '#A855F7';
            const launcherIcon = config.launcher_icon; // Base64 string

            // Create Launcher Button
            const launcher = document.createElement('div');
            launcher.style.width = '60px';
            launcher.style.height = '60px';
            launcher.style.borderRadius = '50%';
            launcher.style.backgroundColor = launcherBgColor;
            launcher.style.cursor = 'pointer';
            launcher.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.1)';
            launcher.style.display = 'flex';
            launcher.style.justifyContent = 'center';
            launcher.style.alignItems = 'center';
            launcher.style.transition = 'transform 0.2s';

            // Add Icon or Default
            if (launcherIcon) {{
                const img = document.createElement('img');
                img.src = launcherIcon;
                img.style.width = '30px';
                img.style.height = '30px';
                img.style.objectFit = 'contain';
                launcher.appendChild(img);
            }} else {{
                // Default Icon (Chat Bubble)
                launcher.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                    </svg>
                `;
            }}

            launcher.addEventListener('mouseenter', () => {{
                launcher.style.transform = 'scale(1.1)';
            }});
            launcher.addEventListener('mouseleave', () => {{
                launcher.style.transform = 'scale(1.0)';
            }});

            launcher.addEventListener('click', () => {{
                if (iframe.style.display === 'none') {{
                    iframe.style.display = 'block';
                }} else {{
                    iframe.style.display = 'none';
                }}
            }});

            container.appendChild(launcher);
        }})
        .catch(err => {{
            console.error('SwiftAnswer Widget: Error fetching config.', err);
        }});

}})();
"""
        return Response(js_content, mimetype='application/javascript')
    except Exception as e:
        error_logger.error(f"Error serving widget script: {e}", exc_info=True)
        return jsonify({"error": "Failed to serve widget script"}), 500
