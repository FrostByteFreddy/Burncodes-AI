"""
Password protection for a chatbot that is still in development.

The owner sets a password; visitors type it once and get a signed access
token (kept by their browser) that the chat endpoints require. The token
carries a fingerprint of the password hash, so changing or removing the
password invalidates every token handed out before.
"""
import hashlib

from flask import current_app, request
from itsdangerous import BadSignature, URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

TOKEN_MAX_AGE = 30 * 24 * 3600
HEADER = "X-Chat-Access"


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def check_password(password_hash: str, password: str) -> bool:
    return bool(password_hash) and check_password_hash(password_hash, password or "")


def _fingerprint(password_hash: str) -> str:
    return hashlib.sha256(password_hash.encode()).hexdigest()[:16]


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="chat-access")


def make_token(tenant_id: str, password_hash: str) -> str:
    return _serializer().dumps({"t": str(tenant_id), "f": _fingerprint(password_hash)})


def token_ok(tenant_id: str, password_hash: str | None) -> bool:
    """True when the chatbot isn't protected or the request carries a valid token."""
    if not password_hash:
        return True
    token = request.headers.get(HEADER, "")
    if not token:
        return False
    try:
        data = _serializer().loads(token, max_age=TOKEN_MAX_AGE)
    except BadSignature:
        return False
    return data.get("t") == str(tenant_id) and data.get("f") == _fingerprint(password_hash)
