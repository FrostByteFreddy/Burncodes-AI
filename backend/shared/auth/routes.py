import os
from flask import Blueprint, request, jsonify
from app.database.supabase_client import supabase
from app.auth.decorators import token_required
from app.logging_config import error_logger
from app import limiter
from supabase import create_client

auth_bp = Blueprint('auth', __name__)

# Login, signup and profile updates happen in the frontend via supabase-js.
# Never call session-mutating auth methods (sign_in_*, sign_out, update_user)
# on the shared `supabase` client: supabase-py swaps the client's
# Authorization header to the signed-in user's token, so every later query in
# that process would run as that user instead of the service role.


def _verify_password(email, password):
    """Checks credentials on a throwaway client so the shared client is untouched."""
    key = (
        os.environ.get("SUPABASE_ANON_KEY")
        or os.environ.get("VITE_SUPABASE_ANON_KEY")
        or os.environ["SUPABASE_SERVICE_KEY"]
    )
    client = create_client(os.environ["SUPABASE_URL"], key)
    try:
        client.auth.sign_in_with_password({"email": email, "password": password})
    finally:
        # Drop the session this check created without touching the user's
        # other sessions (the default "global" scope would log them out).
        try:
            client.auth.sign_out({"scope": "local"})
        except Exception:
            pass


@auth_bp.route('/change-password', methods=['POST'])
@limiter.limit("5 per minute")
@token_required
def change_password(current_user):
    try:
        data = request.get_json() or {}
        current_password = data.get('current_password')
        new_password = data.get('new_password')

        if not current_password or not new_password:
            return jsonify({"error": "Current and new passwords are required"}), 400

        try:
            _verify_password(current_user.email, current_password)
        except Exception as e:
            error_logger.warning(f"Password verification failed for user {current_user.id}: {e}")
            return jsonify({"error": "Incorrect current password"}), 401

        supabase.auth.admin.update_user_by_id(current_user.id, {"password": new_password})
        return jsonify({"message": "Password updated successfully"}), 200
    except Exception as e:
        error_logger.error(f"Error changing password for user {current_user.id}: {e}", extra={'user_id': current_user.id}, exc_info=True)
        return jsonify({"error": "Failed to update password"}), 500
