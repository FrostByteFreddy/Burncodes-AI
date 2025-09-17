import asyncio
from flask import Blueprint, request, jsonify
from app.database.supabase_client import supabase
from app.auth.decorators import token_required
from app.models.database import Tenant, TenantFineTune, SourceType
from app.data_processing import processor
from uuid import uuid4
import os

tenants_bp = Blueprint('tenants', __name__)

@tenants_bp.route('', methods=['POST'])
@token_required
def create_tenant(current_user):
    data = request.get_json()

    try:
        # Basic validation
        if not all(k in data for k in ['name', 'intro_message', 'system_persona', 'rag_prompt_template']):
            return jsonify({"error": "Missing required tenant fields"}), 400

        tenant_id = uuid4()

        # Create Tenant object
        tenant_data = {
            "id": str(tenant_id),
            "user_id": str(current_user.id),
            "name": data['name'],
            "intro_message": data['intro_message'],
            "system_persona": data['system_persona'],
            "rag_prompt_template": data['rag_prompt_template'],
            "doc_language": data.get('doc_language'),
            "doc_description": data.get('doc_description'),
            "source_description": data.get('source_description'),
            "last_updated_description": data.get('last_updated_description'),
            "translation_target": data.get('translation_target'),
        }

        # Insert tenant into Supabase
        supabase.table('tenants').insert(tenant_data).execute()

        # Handle fine-tuning rules
        fine_tune_rules = data.get('fine_tune_rules', [])
        if fine_tune_rules:
            rules_to_insert = [
                {
                    "tenant_id": str(tenant_id),
                    "trigger": rule['trigger'],
                    "instruction": rule['instruction']
                } for rule in fine_tune_rules
            ]
            supabase.table('tenant_fine_tune').insert(rules_to_insert).execute()

        # Fetch the created tenant with its rules to return it
        created_tenant = supabase.table('tenants').select("*, tenant_fine_tune(*)").eq('id', str(tenant_id)).single().execute()

        return jsonify(created_tenant.data), 201

    except Exception as e:
        return jsonify({"error": "Failed to create tenant", "details": str(e)}), 500


@tenants_bp.route('', methods=['GET'])
@token_required
def get_tenants(current_user):
    try:
        # Fetch all tenants for the current user, along with their fine-tuning rules and sources
        tenants = supabase.table('tenants').select("*, tenant_fine_tune(*), tenant_sources(*)").eq('user_id', current_user.id).execute()
        return jsonify(tenants.data), 200
    except Exception as e:
        return jsonify({"error": "Failed to retrieve tenants", "details": str(e)}), 500

@tenants_bp.route('/<uuid:tenant_id>', methods=['GET'])
@token_required
def get_tenant(current_user, tenant_id):
    try:
        tenant = supabase.table('tenants').select("*, tenant_fine_tune(*), tenant_sources(*)").eq('id', str(tenant_id)).eq('user_id', current_user.id).single().execute()
        if not tenant.data:
            return jsonify({"error": "Tenant not found or access denied"}), 404
        return jsonify(tenant.data), 200
    except Exception as e:
        return jsonify({"error": "Failed to retrieve tenant", "details": str(e)}), 500

@tenants_bp.route('/<uuid:tenant_id>', methods=['PUT'])
@token_required
def update_tenant(current_user, tenant_id):
    data = request.get_json()
    tenant_id_str = str(tenant_id)

    try:
        # Verify tenant ownership
        tenant_check = supabase.table('tenants').select("id").eq('id', tenant_id_str).eq('user_id', current_user.id).single().execute()
        if not tenant_check.data:
            return jsonify({"error": "Tenant not found or access denied"}), 404

        # Update tenant details
        allowed_fields = [
            'name', 'intro_message', 'system_persona', 'rag_prompt_template',
            'doc_language', 'doc_description', 'source_description',
            'last_updated_description', 'translation_target'
        ]
        tenant_update_data = {k: v for k, v in data.items() if k in allowed_fields}
        if tenant_update_data:
            supabase.table('tenants').update(tenant_update_data).eq('id', tenant_id_str).execute()

        # Update fine-tuning rules (replace all existing rules)
        if 'fine_tune_rules' in data:
            # First, delete old rules
            supabase.table('tenant_fine_tune').delete().eq('tenant_id', tenant_id_str).execute()
            # Then, insert new ones if any
            new_rules = data['fine_tune_rules']
            if new_rules:
                rules_to_insert = [
                    {"tenant_id": tenant_id_str, "trigger": r['trigger'], "instruction": r['instruction']}
                    for r in new_rules
                ]
                supabase.table('tenant_fine_tune').insert(rules_to_insert).execute()

        # Fetch the updated tenant to return
        updated_tenant = supabase.table('tenants').select("*, tenant_fine_tune(*)").eq('id', tenant_id_str).single().execute()
        return jsonify(updated_tenant.data), 200

    except Exception as e:
        return jsonify({"error": "Failed to update tenant", "details": str(e)}), 500

@tenants_bp.route('/<uuid:tenant_id>', methods=['DELETE'])
@token_required
def delete_tenant(current_user, tenant_id):
    tenant_id_str = str(tenant_id)
    try:
        # Verify tenant ownership
        tenant_check = supabase.table('tenants').select("id").eq('id', tenant_id_str).eq('user_id', current_user.id).single().execute()
        if not tenant_check.data:
            return jsonify({"error": "Tenant not found or access denied"}), 404

        # Delete from all related tables first
        supabase.table('tenant_fine_tune').delete().eq('tenant_id', tenant_id_str).execute()
        supabase.table('tenant_sources').delete().eq('tenant_id', tenant_id_str).execute()

        # Finally, delete the tenant itself
        supabase.table('tenants').delete().eq('id', tenant_id_str).execute()

        # Here you would also add logic to delete the vector store from ChromaDB
        # This will be handled in a later step.

        return jsonify({"message": "Tenant deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": "Failed to delete tenant", "details": str(e)}), 500

# --- Data Source Management ---

@tenants_bp.route('/<uuid:tenant_id>/sources', methods=['GET'])
@token_required
def get_sources(current_user, tenant_id):
    tenant_id_str = str(tenant_id)
    try:
        # Verify tenant ownership
        tenant_check = supabase.table('tenants').select("id").eq('id', tenant_id_str).eq('user_id', current_user.id).single().execute()
        if not tenant_check.data:
            return jsonify({"error": "Tenant not found or access denied"}), 404

        sources = supabase.table('tenant_sources').select("*").eq('tenant_id', tenant_id_str).execute()
        return jsonify(sources.data), 200
    except Exception as e:
        return jsonify({"error": "Failed to retrieve sources", "details": str(e)}), 500

@tenants_bp.route('/<uuid:tenant_id>/sources/upload', methods=['POST'])
@token_required
def upload_source(current_user, tenant_id):
    tenant_id_str = str(tenant_id)
    # Verify tenant ownership
    tenant_check = supabase.table('tenants').select("id").eq('id', tenant_id_str).eq('user_id', current_user.id).single().execute()
    if not tenant_check.data:
        return jsonify({"error": "Tenant not found or access denied"}), 404

    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        # Save file temporarily
        tenant_upload_path = os.path.join('uploads', tenant_id_str)
        os.makedirs(tenant_upload_path, exist_ok=True)
        filepath = os.path.join(tenant_upload_path, file.filename)
        file.save(filepath)

        # Create a source record in the database
        source_data = {
            "tenant_id": tenant_id_str,
            "source_type": SourceType.FILE,
            "source_location": file.filename,
            "status": "PROCESSING"
        }
        source_record = supabase.table('tenant_sources').insert(source_data).execute()
        source_id = source_record.data[0]['id']

        # Process the file
        loader = processor.get_loader(filepath)
        if not loader:
            supabase.table('tenant_sources').update({"status": "ERROR"}).eq('id', source_id).execute()
            return jsonify({"error": f"Unsupported file type: {file.filename}"}), 400

        docs_from_loader = loader.load()
        os.remove(filepath) # Clean up the saved file

        if not docs_from_loader:
            supabase.table('tenant_sources').update({"status": "ERROR"}).eq('id', source_id).execute()
            return jsonify({"error": f"No content could be extracted from: {file.filename}"}), 400

        content = docs_from_loader[0].page_content

        # Process and vectorize the document
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        documents = loop.run_until_complete(processor.async_create_document_chunks_with_metadata(content, file.filename, source_id))
        loop.close()

        processor.process_documents(documents, tenant_id)

        return jsonify({"success": True, "message": f"File '{file.filename}' processed.", "source_id": source_id}), 201

    except Exception as e:
        if 'loop' in locals() and not loop.is_closed():
            loop.close()
        return jsonify({"error": f"Failed to process file: {str(e)}"}), 500

@tenants_bp.route('/<uuid:tenant_id>/sources/crawl', methods=['POST'])
@token_required
def crawl_sources(current_user, tenant_id):
    data = request.get_json()
    urls = data.get('urls')
    tenant_id_str = str(tenant_id)

    if not urls or not isinstance(urls, list):
        return jsonify({"error": "A list of URLs is required"}), 400

    # Verify tenant ownership
    tenant_check = supabase.table('tenants').select("id").eq('id', tenant_id_str).eq('user_id', current_user.id).single().execute()
    if not tenant_check.data:
        return jsonify({"error": "Tenant not found or access denied"}), 404

    try:
        # Create source records in the database
        sources_to_insert = [
            {
                "tenant_id": tenant_id_str,
                "source_type": SourceType.URL,
                "source_location": url,
                "status": "PROCESSING"
            } for url in urls
        ]
        source_records = supabase.table('tenant_sources').insert(sources_to_insert).execute()

        # Get the IDs of the created sources
        urls_with_ids = [(rec['source_location'], rec['id']) for rec in source_records.data]

        # Process and vectorize the URLs
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        documents = loop.run_until_complete(processor.process_urls_concurrently(urls_with_ids, tenant_id))
        loop.close()

        processor.process_documents(documents, tenant_id)

        processed_sources = list(set([doc.metadata['source'] for doc in documents]))
        return jsonify({
            "success": True,
            "message": f"Successfully processed {len(processed_sources)} URLs.",
            "processed_sources": processed_sources
        }), 200

    except Exception as e:
        if 'loop' in locals() and not loop.is_closed():
            loop.close()
        return jsonify({"error": f"Failed to process URLs: {str(e)}"}), 500


@tenants_bp.route('/<uuid:tenant_id>/sources/discover', methods=['POST'])
@token_required
def discover_links(current_user, tenant_id):
    data = request.get_json()
    start_url = data.get('url')

    if not start_url:
        return jsonify({"error": "URL is required"}), 400

    # Basic ownership check
    tenant_id_str = str(tenant_id)
    tenant_check = supabase.table('tenants').select("id").eq('id', tenant_id_str).eq('user_id', current_user.id).single().execute()
    if not tenant_check.data:
        return jsonify({"error": "Tenant not found or access denied"}), 404

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        links_by_depth = loop.run_until_complete(processor.crawl_recursive_for_links(start_url))
        loop.close()

        # We need to flatten the list for the final crawl, but for now, let's return counts
        discovery_summary = [
            {"depth": i + 1, "count": len(links), "links": links}
            for i, links in enumerate(links_by_depth)
        ]

        return jsonify(discovery_summary), 200

    except Exception as e:
        if 'loop' in locals() and not loop.is_closed():
            loop.close()
        return jsonify({"error": f"Failed to discover links: {str(e)}"}), 500


@tenants_bp.route('/<uuid:tenant_id>/sources/<int:source_id>', methods=['DELETE'])
@token_required
def delete_source(current_user, tenant_id, source_id):
    tenant_id_str = str(tenant_id)
    try:
        # Verify tenant ownership
        tenant_check = supabase.table('tenants').select("id").eq('id', tenant_id_str).eq('user_id', current_user.id).single().execute()
        if not tenant_check.data:
            return jsonify({"error": "Tenant not found or access denied"}), 404

        # Verify source ownership
        source_check = supabase.table('tenant_sources').select("id").eq('id', source_id).eq('tenant_id', tenant_id_str).single().execute()
        if not source_check.data:
            return jsonify({"error": "Source not found or access denied"}), 404

        # This is tricky: deleting a source requires deleting its vectors from ChromaDB.
        # ChromaDB doesn't have a simple "delete by metadata" that is transactional with this DB.
        # A common strategy is to rebuild the index or periodically clean it.
        # For now, we will just delete the source record from our DB.
        # A more robust solution would involve a background job to clean up the vector store.

        supabase.table('tenant_sources').delete().eq('id', source_id).execute()

        return jsonify({"message": "Source deleted successfully. Note: Vector data may still exist and will be cleaned up later."}), 200

    except Exception as e:
        return jsonify({"error": "Failed to delete source", "details": str(e)}), 500
