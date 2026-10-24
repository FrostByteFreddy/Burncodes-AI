import os
import tempfile
from types import SimpleNamespace

import pytest

# The app reads these at import time; set harmless test values before importing it.
os.environ.setdefault("SUPABASE_URL", "http://supabase.test")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test.service.key")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("CELERY_BROKER_URL", "memory://")
os.environ.setdefault("CELERY_RESULT_BACKEND", "cache+memory://")
os.environ.setdefault("LOG_DIR", tempfile.mkdtemp(prefix="swiftanswer-logs-"))
os.environ.setdefault("UPLOAD_FOLDER_BASE", tempfile.mkdtemp(prefix="swiftanswer-uploads-"))
os.environ.setdefault("CRAWL4_AI_BASE_DIRECTORY", tempfile.mkdtemp(prefix="swiftanswer-data-"))

from app import create_app, limiter  # noqa: E402


@pytest.fixture
def app():
    """Create a Flask application instance for testing."""
    app = create_app()
    app.config.update({
        "TESTING": True,
    })
    limiter.enabled = False
    yield app
    limiter.enabled = True


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def user():
    return SimpleNamespace(id="11111111-1111-1111-1111-111111111111", email="owner@example.com", user_metadata={})


@pytest.fixture
def auth_as(monkeypatch, user):
    """Makes any bearer token resolve to `user`; returns the auth header to send."""
    from app.auth import decorators

    monkeypatch.setattr(
        decorators.supabase.auth, "get_user", lambda token: SimpleNamespace(user=user)
    )
    return {"Authorization": "Bearer test-token"}
