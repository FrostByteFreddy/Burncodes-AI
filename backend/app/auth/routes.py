import os
from flask import Blueprint, request, jsonify
from app.database.supabase_client import supabase
from app.auth.decorators import token_required
from app.logging_config import error_logger
from supabase import create_client, Client

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        first_name = data.get('first_name')
        last_name = data.get('last_name')

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        response = supabase.auth.sign_up({
            "email": email, "password": password,
            "options": {"data": {"first_name": first_name, "last_name": last_name}}
        })
        return jsonify({"message": "Signup successful! Please check your email to confirm your account."}), 201
    except Exception as e:
        error_message = str(e)
        # Log the generic error
        error_logger.error(f"Error during signup for email {email}: {error_message}", exc_info=True)
        if "User already registered" in error_message:
            return jsonify({"error": "User with this email already exists."}), 409
        return jsonify({"error": error_message}), 400

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return jsonify({
            "access_token": response.session.access_token, "refresh_token": response.session.refresh_token,
            "user": {"id": response.user.id, "email": response.user.email}
        }), 200
    except Exception as e:
        # Note: No user_id available yet at this stage
        error_logger.error(f"Error during login for email {email}: {e}", exc_info=True)
        return jsonify({"error": "Invalid login credentials."}), 401

@auth_bp.route('/user', methods=['GET'])
@token_required
def get_user(current_user):
    try:
        return jsonify({
            "id": current_user.id, "email": current_user.email,
            "user_metadata": current_user.user_metadata
        }), 200
    except Exception as e:
        error_logger.error(f"Error getting user {current_user.id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to retrieve user information", "details": str(e)}), 500

@auth_bp.route('/user', methods=['PUT'])
@token_required
def update_user(current_user):
    try:
        data = request.get_json()
        user_metadata = current_user.user_metadata or {}
        if 'first_name' in data: user_metadata['first_name'] = data['first_name']
        if 'last_name' in data: user_metadata['last_name'] = data['last_name']
        if 'phone_number' in data: user_metadata['phone_number'] = data['phone_number']

        token = request.headers['Authorization'].split(" ")[1]
        updated_user_response = supabase.auth.update_user({"data": user_metadata}, jwt=token)
        return jsonify(updated_user_response.user.user_metadata), 200
    except Exception as e:
        error_logger.error(f"Error updating user {current_user.id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Could not update user metadata", "details": str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout(current_user):
    try:
        token = request.headers['Authorization'].split(" ")[1]
        supabase.auth.sign_out(token)
        return jsonify({"message": "Successfully logged out"}), 200
    except Exception as e:
        error_logger.error(f"Error during logout for user {current_user.id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Logout failed", "details": str(e)}), 500
