import os
from flask import Blueprint, request, jsonify
from app.database.supabase_client import supabase
from app.auth.decorators import token_required
from supabase import create_client, Client

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    first_name = data.get('first_name')
    last_name = data.get('last_name')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    try:
        # Sign up the user with metadata
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "first_name": first_name,
                    "last_name": last_name
                }
            }
        })
        # The profile table is gone, user data is stored in auth.users.
        return jsonify({"message": "Signup successful! Please check your email to confirm your account."}), 201
    except Exception as e:
        error_message = str(e)
        if "User already registered" in error_message:
            return jsonify({"error": "User with this email already exists."}), 409
        return jsonify({"error": error_message}), 400

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        # The session object (including access_token) is in response.session
        return jsonify({
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "user": {
                "id": response.user.id,
                "email": response.user.email,
            }
        }), 200
    except Exception as e:
        return jsonify({"error": "Invalid login credentials."}), 401


@auth_bp.route('/user', methods=['GET'])
@token_required
def get_user(current_user):
    # The user object from the decorator has everything we need.
    # Supabase user object structure has metadata in `user_metadata`.
    return jsonify({
        "id": current_user.id,
        "email": current_user.email,
        "user_metadata": current_user.user_metadata
    }), 200


@auth_bp.route('/user', methods=['PUT'])
@token_required
def update_user(current_user):
    data = request.get_json()

    # Prepare the metadata to update
    user_metadata = current_user.user_metadata or {}
    if 'first_name' in data:
        user_metadata['first_name'] = data['first_name']
    if 'last_name' in data:
        user_metadata['last_name'] = data['last_name']
    if 'phone_number' in data:
        user_metadata['phone_number'] = data['phone_number']

    try:
        # The user's JWT in the decorator has permission to update their own data.
        # We need to get the token from the request to make an authenticated call.
        token = request.headers['Authorization'].split(" ")[1]
        updated_user_response = supabase.auth.update_user(
            {"data": user_metadata},
            jwt=token
        )
        return jsonify(updated_user_response.user.user_metadata), 200
    except Exception as e:
        return jsonify({"error": "Could not update user metadata", "details": str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout(current_user):
    try:
        # Get the token from the header to sign out the specific session
        token = request.headers['Authorization'].split(" ")[1]
        supabase.auth.sign_out(token)
        return jsonify({"message": "Successfully logged out"}), 200
    except Exception as e:
        return jsonify({"error": "Logout failed", "details": str(e)}), 500
