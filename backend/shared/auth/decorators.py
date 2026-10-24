from functools import wraps
from flask import request, jsonify
from app.database.supabase_client import supabase

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        scheme, _, token = request.headers.get('Authorization', '').partition(' ')
        if scheme.lower() != 'bearer' or not token.strip():
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            # get_user only reads; it doesn't change the shared client's session.
            current_user = supabase.auth.get_user(token.strip()).user
        except Exception:
            current_user = None
        if not current_user:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated_function
