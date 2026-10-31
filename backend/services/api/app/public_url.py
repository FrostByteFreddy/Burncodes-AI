"""
The public addresses for links that leave the dashboard: calendar feeds, the
embed script. API_BASE_URL wins when set; otherwise the address
the request came in on (nginx forwards Host and the scheme, ProxyFix applies
them), so production never hands out localhost links.
"""
import os

from flask import request


def public_api_base() -> str:
    configured = (os.environ.get('API_BASE_URL') or '').strip()
    if configured:
        return configured.rstrip('/')
    return request.url_root.rstrip('/')


def public_frontend_base() -> str:
    """Where the chat pages are: FRONTEND_URL, else the request's address (nginx serves both there)."""
    configured = (os.environ.get('FRONTEND_URL') or '').strip()
    if configured:
        return configured.rstrip('/')
    return request.url_root.rstrip('/')
