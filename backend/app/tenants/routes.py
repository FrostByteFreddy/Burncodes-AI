from flask import Blueprint, request, jsonify
from app.database.supabase_client import supabase
from app.auth.decorators import token_required
from app.models.database import Tenant, TenantFineTune
from app.data_processing.processor import process_fine_tune_rules, delete_fine_tune_vectors
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.logging_config import error_logger
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

            # Update each rule in tenant_fine_tune with the vector_id
            for rule, vector_id in zip(inserted_rules, vector_ids):
                supabase.table('tenant_fine_tune').update({"vector_id": vector_id}).eq('id', rule['id']).execute()

        return jsonify({"message": "Tenant created successfully", "id": str(tenant_id)}), 201
    except Exception as e:
        error_logger.error(f"Error creating tenant for user {current_user.id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to create tenant", "details": str(e)}), 500

@tenants_bp.route('', methods=['GET'])
@token_required
def get_tenants(current_user):
    try:
        tenants = supabase.table('tenants').select("*").eq('user_id', current_user.id).execute()
        return jsonify(tenants.data), 200
    except Exception as e:
        error_logger.error(f"Error fetching tenants for user {current_user.id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to fetch tenants", "details": str(e)}), 500

@tenants_bp.route('/<uuid:tenant_id>', methods=['GET'])
@token_required
def get_tenant(current_user, tenant_id):
    try:
        tenant = supabase.table('tenants').select("*").eq('id', str(tenant_id)).eq('user_id', current_user.id).single().execute()
        if not tenant.data:
            return jsonify({"error": "Tenant not found"}), 404

        fine_tune_rules = supabase.table('tenant_fine_tune').select("*").eq('tenant_id', str(tenant_id)).execute()
        tenant.data['fine_tune_rules'] = fine_tune_rules.data
        return jsonify(tenant.data), 200
    except Exception as e:
        error_logger.error(f"Error fetching tenant {tenant_id} for user {current_user.id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to fetch tenant", "details": str(e)}), 500

@tenants_bp.route('/<uuid:tenant_id>/public', methods=['GET'])
def get_public_tenant(tenant_id):
    try:
        tenant = supabase.table('tenants').select("name, intro_message, widget_config").eq('id', str(tenant_id)).single().execute()
        if not tenant.data:
            return jsonify({"error": "Tenant not found"}), 404
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
        allowed_fields = ['name', 'intro_message', 'system_persona', 'rag_prompt_template', 'doc_language', 'translation_target', 'widget_config']
        for field in allowed_fields:
            if field in data:
                tenant_update_data[field] = data[field]

        if tenant_update_data:
            supabase.table('tenants').update(tenant_update_data).eq('id', tenant_id_str).execute()

        if 'fine_tune_rules' in data:
            new_rules_data = data['fine_tune_rules']
            existing_rules_response = supabase.table('tenant_fine_tune').select('id, vector_id').eq('tenant_id', tenant_id_str).execute()
            existing_rules = existing_rules_response.data

            vector_ids_to_delete = [rule['vector_id'] for rule in existing_rules if rule.get('vector_id')]
            embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

            if vector_ids_to_delete:
                delete_fine_tune_vectors(vector_ids_to_delete, tenant_id, embeddings)

            supabase.table('tenant_fine_tune').delete().eq('tenant_id', tenant_id_str).execute()

            if new_rules_data:
                rules_to_insert = [{"tenant_id": tenant_id_str, "trigger": r['trigger'], "instruction": r['instruction']} for r in new_rules_data]
                inserted_rules_response = supabase.table('tenant_fine_tune').insert(rules_to_insert).execute()
                inserted_rules = inserted_rules_response.data
                fine_tune_rules_models = [TenantFineTune(**rule) for rule in inserted_rules]
                vector_ids = process_fine_tune_rules(fine_tune_rules_models, tenant_id, embeddings)
                for rule, vector_id in zip(inserted_rules, vector_ids):
                    supabase.table('tenant_fine_tune').update({"vector_id": vector_id}).eq('id', rule['id']).execute()

        return jsonify({"message": "Tenant updated successfully"}), 200
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

        existing_rules_response = supabase.table('tenant_fine_tune').select('id, vector_id').eq('tenant_id', tenant_id_str).execute()
        existing_rules = existing_rules_response.data
        vector_ids_to_delete = [rule['vector_id'] for rule in existing_rules if rule.get('vector_id')]

        if vector_ids_to_delete:
            embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
            delete_fine_tune_vectors(vector_ids_to_delete, tenant_id, embeddings)

        supabase.table('tenant_fine_tune').delete().eq('tenant_id', tenant_id_str).execute()
        supabase.table('tenant_sources').delete().eq('tenant_id', tenant_id_str).execute()
        supabase.table('tenants').delete().eq('id', tenant_id_str).execute()
        return jsonify({"message": "Tenant deleted successfully"}), 200
    except Exception as e:
        error_logger.error(f"Error deleting tenant {tenant_id} for user {current_user.id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to delete tenant", "details": str(e)}), 500
