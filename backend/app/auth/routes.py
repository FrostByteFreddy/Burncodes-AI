from flask import Blueprint, request, jsonify
from app.database.supabase_client import supabase
from app.auth.decorators import token_required

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
        # Sign up the user
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

        # The user object is available in response.user
        new_user = response.user
        if new_user:
            # Create a corresponding profile in the 'profiles' table
            profile_data = {
                "id": new_user.id,
                "email": new_user.email,
                "first_name": first_name,
                "last_name": last_name
            }
            supabase.table('profiles').insert(profile_data).execute()

        return jsonify({"message": "Signup successful! Please check your email to confirm your account."}), 201
    except Exception as e:
        # Attempt to parse Supabase-specific errors
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
    try:
        # The user object from the token doesn't contain profile data.
        # We need to fetch it from the 'profiles' table.
        profile = supabase.table('profiles').select("*").eq('id', current_user.id).single().execute()
        return jsonify(profile.data), 200
    except Exception as e:
        return jsonify({"error": "Could not retrieve profile", "details": str(e)}), 500


@auth_bp.route('/user', methods=['PUT'])
@token_required
def update_user(current_user):
    data = request.get_json()
    update_data = {
        "first_name": data.get('first_name'),
        "last_name": data.get('last_name'),
        "phone_number": data.get('phone_number')
    }
    # Filter out any None values so we only update provided fields
    update_data = {k: v for k, v in update_data.items() if v is not None}

    if not update_data:
        return jsonify({"error": "No update information provided"}), 400

    try:
        updated_profile = supabase.table('profiles').update(update_data).eq('id', current_user.id).execute()
        return jsonify(updated_profile.data), 200
    except Exception as e:
        return jsonify({"error": "Could not update profile", "details": str(e)}), 500

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
