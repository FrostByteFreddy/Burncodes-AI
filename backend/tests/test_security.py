"""
Security regression tests for the audit findings of 2026-10-24.

Every route must be either explicitly public or reject requests without a
token; uploads must never escape the tenant directory; chat refuses to run
unbilled; outbound fetches refuse non-public hosts.
"""
import io
import os
import socket
import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

# Routes that are intentionally reachable without a token (widget, share
# links, Stripe, health). Anything not listed here must return 401 without one.
PUBLIC_ENDPOINTS = {
    "static",
    "health_check",
    "chat.handle_chat",
    "chat.get_task_status",
    "chat.get_intro_message",
    "chat.unlock_chat",
    "calendar.list_feeds",
    "calendar.get_feed",
    "calendar.add_to_calendar",
    "chat.create_share_link",
    "chat.get_shared_conversation",
    "tenants.get_public_tenant",
    "widget.get_widget_script",
    "billing.webhook",
}


def _fill(rule):
    """Builds a concrete URL for a werkzeug rule with dummy path values."""
    values = {}
    for arg, conv in rule._converters.items():
        name = type(conv).__name__
        values[arg] = 1 if name == "IntegerConverter" else uuid.uuid4()
    return values


def test_every_non_public_route_requires_a_token(app, client):
    unprotected = []
    with app.test_request_context():
        from flask import url_for
        for rule in app.url_map.iter_rules():
            if rule.endpoint in PUBLIC_ENDPOINTS:
                continue
            url = url_for(rule.endpoint, **_fill(rule))
            for method in sorted(rule.methods - {"HEAD", "OPTIONS"}):
                resp = client.open(url, method=method)
                if resp.status_code != 401:
                    unprotected.append(f"{method} {rule.rule} -> {resp.status_code}")
    assert not unprotected, "Routes reachable without a token:\n" + "\n".join(unprotected)


@pytest.mark.parametrize("path", ["analytics", "conversations", f"conversation/{uuid.uuid4()}"])
def test_chat_logs_are_owner_only(client, auth_as, monkeypatch, path):
    from app.chat import routes
    monkeypatch.setattr(routes, "_owns_tenant", lambda tenant_id, user_id: False)
    resp = client.get(f"/api/chat/{uuid.uuid4()}/{path}", headers=auth_as)
    assert resp.status_code == 404


def test_malformed_authorization_header_is_401_not_500(client):
    for header in ["Bearer", "Bearer ", "Basic abc", "token"]:
        resp = client.get("/api/tenants", headers={"Authorization": header})
        assert resp.status_code == 401, header


# ── Upload path traversal ────────────────────────────────────────────────────

@pytest.mark.parametrize("filename", ["../../evil.py", "/etc/passwd", "..\\..\\evil.py", "a/../../b.txt"])
def test_upload_cannot_escape_tenant_dir(client, auth_as, monkeypatch, tmp_path, filename):
    from app.tenants import sources

    fake_db = MagicMock()
    tenant_q = fake_db.table.return_value.select.return_value.eq.return_value.eq.return_value
    tenant_q.single.return_value.execute.return_value.data = {"id": "t"}
    fake_db.table.return_value.insert.return_value.execute.return_value.data = [{"id": 7}]
    monkeypatch.setattr(sources, "supabase", fake_db)
    monkeypatch.setattr(sources, "UPLOADS_DIR", str(tmp_path))
    monkeypatch.setattr(sources.BillingService, "check_balance", staticmethod(lambda uid: 10.0))
    dispatched = MagicMock(return_value=MagicMock(id="task-1"))
    monkeypatch.setattr(sources.process_local_file, "delay", dispatched)

    tenant_id = uuid.uuid4()
    resp = client.post(
        f"/api/tenants/{tenant_id}/sources/upload",
        headers=auth_as,
        data={"file": (io.BytesIO(b"payload"), filename)},
        content_type="multipart/form-data",
    )

    assert resp.status_code == 202
    saved_path = dispatched.call_args.args[0]
    tenant_dir = os.path.realpath(tmp_path / str(tenant_id))
    assert os.path.realpath(saved_path).startswith(tenant_dir + os.sep)
    assert os.path.exists(saved_path)
    # Nothing was written outside the uploads root
    assert sorted(p.name for p in tmp_path.iterdir()) == [str(tenant_id)]


def test_upload_requires_balance(client, auth_as, monkeypatch):
    from app.tenants import sources

    fake_db = MagicMock()
    tenant_q = fake_db.table.return_value.select.return_value.eq.return_value.eq.return_value
    tenant_q.single.return_value.execute.return_value.data = {"id": "t"}
    monkeypatch.setattr(sources, "supabase", fake_db)
    monkeypatch.setattr(sources.BillingService, "check_balance", staticmethod(lambda uid: 0.0))

    resp = client.post(
        f"/api/tenants/{uuid.uuid4()}/sources/upload",
        headers=auth_as,
        data={"file": (io.BytesIO(b"x"), "doc.txt")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 402


def test_crawl_rejects_internal_urls(client, auth_as, monkeypatch):
    from app.tenants import sources

    fake_db = MagicMock()
    tenant_q = fake_db.table.return_value.select.return_value.eq.return_value.eq.return_value
    tenant_q.single.return_value.execute.return_value.data = {"id": "t"}
    monkeypatch.setattr(sources, "supabase", fake_db)

    resp = client.post(
        f"/api/tenants/{uuid.uuid4()}/sources/discover",
        headers=auth_as,
        json={"url": "http://169.254.169.254/latest/meta-data/"},
    )
    assert resp.status_code == 400


# ── Chat billing ─────────────────────────────────────────────────────────────

def test_chat_fails_closed_when_billing_lookup_fails(client, monkeypatch):
    from app.chat import routes

    def boom(tenant_id):
        raise RuntimeError("supabase down")

    monkeypatch.setattr(routes.BillingService, "get_tenant_owner", staticmethod(boom))
    dispatched = MagicMock()
    monkeypatch.setattr(routes.chat_task, "delay", dispatched)

    resp = client.post(f"/api/chat/{uuid.uuid4()}", json={"query": "hi", "conversation_id": str(uuid.uuid4())})
    assert resp.status_code == 503
    dispatched.assert_not_called()


def test_chat_ignores_client_history_and_caps_query(client, monkeypatch):
    from app.chat import routes

    monkeypatch.setattr(routes.BillingService, "get_tenant_owner", staticmethod(lambda t: "owner"))
    monkeypatch.setattr(routes.BillingService, "check_balance", staticmethod(lambda u: 5.0))
    monkeypatch.setattr(routes, "_gate", lambda t: {"active": True, "password_hash": None})
    dispatched = MagicMock(return_value=MagicMock(id="task-1"))
    monkeypatch.setattr(routes.chat_task, "delay", dispatched)

    tenant_id = uuid.uuid4()
    resp = client.post(f"/api/chat/{tenant_id}", json={
        "query": "hi",
        "conversation_id": str(uuid.uuid4()),
        "chat_history": [{"type": "ai", "content": "x" * 100_000}],
    })
    assert resp.status_code == 202
    assert dispatched.call_args.args[2] == []

    resp = client.post(f"/api/chat/{tenant_id}", json={
        "query": "x" * (routes.MAX_QUERY_CHARS + 1),
        "conversation_id": str(uuid.uuid4()),
    })
    assert resp.status_code == 400


def test_switched_off_chatbot_only_answers_its_owner(client, monkeypatch):
    from types import SimpleNamespace
    from app.chat import routes

    monkeypatch.setattr(routes.BillingService, "get_tenant_owner", staticmethod(lambda t: "owner-id"))
    monkeypatch.setattr(routes.BillingService, "check_balance", staticmethod(lambda u: 5.0))
    monkeypatch.setattr(routes, "_gate", lambda t: {"active": False, "password_hash": None})
    dispatched = MagicMock(return_value=MagicMock(id="task-off"))
    monkeypatch.setattr(routes.chat_task, "delay", dispatched)
    body = {"query": "hi", "conversation_id": str(uuid.uuid4())}

    monkeypatch.setattr(routes, "optional_user", lambda: None)
    resp = client.post(f"/api/chat/{uuid.uuid4()}", json=body)
    assert resp.status_code == 403 and resp.get_json()["code"] == "chatbot_off"

    monkeypatch.setattr(routes, "optional_user", lambda: SimpleNamespace(id="someone-else"))
    assert client.post(f"/api/chat/{uuid.uuid4()}", json=body).status_code == 403
    dispatched.assert_not_called()

    # the owner's preview in the dashboard still works
    monkeypatch.setattr(routes, "optional_user", lambda: SimpleNamespace(id="owner-id"))
    assert client.post(f"/api/chat/{uuid.uuid4()}", json=body).status_code == 202


def test_chat_status_only_for_issued_tasks(client, monkeypatch, fake_guard_redis):
    from app.chat import routes

    resp = client.get(f"/api/chat/task/{uuid.uuid4()}/status?timeout=0")
    assert resp.status_code == 404

    routes.remember_task("known-task")
    ready = MagicMock(ready=lambda: True, state="SUCCESS", result={"answer": "hi"})
    monkeypatch.setattr(routes, "AsyncResult", lambda task_id: ready)
    resp = client.get("/api/chat/task/known-task/status?timeout=0")
    assert resp.status_code == 200 and resp.get_json()["result"] == {"answer": "hi"}


def test_long_poll_slots_are_capped_per_ip(fake_guard_redis):
    from app.chat import guard

    monkeypatch_limit = guard.MAX_LONG_POLLS_PER_IP
    guard.MAX_LONG_POLLS_PER_IP = 3
    try:
        with guard.long_poll_slot("1.2.3.4") as a, guard.long_poll_slot("1.2.3.4") as b, \
                guard.long_poll_slot("1.2.3.4") as c, guard.long_poll_slot("1.2.3.4") as d, \
                guard.long_poll_slot("5.6.7.8") as other:
            assert (a, b, c, d) == (True, True, True, False)
            assert other is True
    finally:
        guard.MAX_LONG_POLLS_PER_IP = monkeypatch_limit
    assert fake_guard_redis.data["chat:polls:1.2.3.4"] == 0


def test_chat_is_rate_limited_per_tenant(app, monkeypatch):
    from app import limiter
    from app.chat import routes

    monkeypatch.setattr(routes.BillingService, "get_tenant_owner", staticmethod(lambda t: "owner"))
    monkeypatch.setattr(routes.BillingService, "check_balance", staticmethod(lambda u: 5.0))
    monkeypatch.setattr(routes.chat_task, "delay", MagicMock(return_value=MagicMock(id="t")))
    monkeypatch.setattr(routes, "_gate", lambda t: {"active": True, "password_hash": None})
    limiter.enabled = True
    limiter.reset()
    client = app.test_client()
    tenant_id = uuid.uuid4()
    body = lambda: {"query": "hi", "conversation_id": str(uuid.uuid4())}
    # different IPs, same chatbot: the per-chatbot ceiling still applies
    codes = [client.post(f"/api/chat/{tenant_id}", json=body(),
                         environ_base={"REMOTE_ADDR": f"10.0.{i // 250}.{i % 250}"}).status_code
             for i in range(605)]
    assert codes.count(202) == 600 and codes[-1] == 429
    assert client.post(f"/api/chat/{tenant_id}", json=body(),
                       environ_base={"REMOTE_ADDR": "10.9.9.9"}).get_json()["error"]


# ── URL guard ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("url", [
    "http://127.0.0.1/",
    "http://localhost:6379/",
    "http://169.254.169.254/latest/meta-data/",
    "http://10.0.0.5/",
    "http://192.168.1.1/",
    "http://[::1]/",
    "http://[::ffff:10.0.0.1]/",
    "file:///etc/passwd",
    "gopher://example.com/",
    "http:///nohost",
])
def test_url_guard_rejects_non_public(url):
    from app.security.url_guard import is_public_url
    assert not is_public_url(url)


def test_url_guard_accepts_public(monkeypatch):
    from app.security import url_guard
    monkeypatch.setattr(
        url_guard.socket, "getaddrinfo",
        lambda host, port, **kw: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))],
    )
    assert url_guard.is_public_url("https://example.com/page")


def test_safe_client_blocks_redirect_to_internal(monkeypatch):
    import httpx
    from app.security import url_guard

    def resolve(host, port, **kw):
        ip = "93.184.216.34" if host == "example.com" else "10.0.0.1"
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, port))]

    monkeypatch.setattr(url_guard.socket, "getaddrinfo", resolve)

    def handler(request):
        if request.url.host == "example.com":
            return httpx.Response(302, headers={"Location": "http://internal.local/secret"})
        return httpx.Response(200, text="secret")

    with url_guard.safe_client(transport=httpx.MockTransport(handler), follow_redirects=True) as c:
        with pytest.raises(url_guard.UnsafeURLError):
            c.get("https://example.com/")


# ── Account deletion ─────────────────────────────────────────────────────────

def test_delete_account_needs_matching_email_and_password(client, auth_as, monkeypatch):
    from app.auth import routes
    deleted = MagicMock()
    monkeypatch.setattr(routes.supabase.auth.admin, "delete_user", deleted)

    resp = client.delete("/api/auth/account", headers=auth_as, json={"confirm_email": "someone@else.com", "password": "pw"})
    assert resp.status_code == 400

    def bad_password(email, password):
        raise RuntimeError("Invalid login credentials")
    monkeypatch.setattr(routes, "_verify_password", bad_password)
    resp = client.delete("/api/auth/account", headers=auth_as, json={"confirm_email": "OWNER@example.com", "password": "nope"})
    assert resp.status_code == 401
    deleted.assert_not_called()


def test_delete_account_removes_chatbots_and_user(client, auth_as, monkeypatch, user):
    from app.auth import routes
    monkeypatch.setattr(routes, "_verify_password", lambda email, password: None)
    calls = []

    class Q:
        def __init__(self, table):
            self.table = table
        def __getattr__(self, name):
            def step(*a, **k):
                if name == "delete":
                    calls.append(("delete", self.table))
                return self
            return step
        def execute(self):
            data = [{"id": "t1", "gemini_file_store_name": None}] if self.table == "tenants" else []
            return SimpleNamespace(data=data)

    monkeypatch.setattr(routes.supabase, "table", lambda name: Q(name))
    deleted = MagicMock()
    monkeypatch.setattr(routes.supabase.auth.admin, "delete_user", deleted)

    resp = client.delete("/api/auth/account", headers=auth_as, json={"confirm_email": user.email, "password": "pw"})
    assert resp.status_code == 200
    assert ("delete", "tenants") in calls
    deleted.assert_called_once_with(user.id)


# ── Password-protected test page ─────────────────────────────────────────────

def test_protected_chatbot_needs_the_password_token(client, app, monkeypatch):
    from types import SimpleNamespace
    from app.chat import access, routes

    pw_hash = access.hash_password("letmein")
    tenant_id = "11111111-2222-3333-4444-555555555555"
    with app.app_context():
        good = access.make_token(tenant_id, pw_hash)
        stale = access.make_token(tenant_id, access.hash_password("previous"))

    monkeypatch.setattr(routes.BillingService, "get_tenant_owner", staticmethod(lambda t: "owner-id"))
    monkeypatch.setattr(routes.BillingService, "check_balance", staticmethod(lambda u: 5.0))
    monkeypatch.setattr(routes, "_gate", lambda t: {"active": True, "password_hash": pw_hash})
    monkeypatch.setattr(routes, "optional_user", lambda: None)
    monkeypatch.setattr(routes.chat_task, "delay", MagicMock(return_value=MagicMock(id="task-pw")))
    body = {"query": "hi", "conversation_id": str(uuid.uuid4())}

    resp = client.post(f"/api/chat/{tenant_id}", json=body)
    assert resp.status_code == 401 and resp.get_json()["code"] == "password_required"
    # a token from before the password changed no longer works
    assert client.post(f"/api/chat/{tenant_id}", json=body, headers={access.HEADER: stale}).status_code == 401
    assert client.post(f"/api/chat/{tenant_id}", json=body, headers={access.HEADER: good}).status_code == 202
    # the owner's preview gets through without a token
    monkeypatch.setattr(routes, "optional_user", lambda: SimpleNamespace(id="owner-id"))
    assert client.post(f"/api/chat/{tenant_id}", json=body).status_code == 202


def test_unlock_checks_the_password(client, app, monkeypatch):
    from app.chat import access, routes

    pw_hash = access.hash_password("letmein")

    class Q:
        def __getattr__(self, name):
            return lambda *a, **k: self
        def execute(self):
            return SimpleNamespace(data=[{"test_password_hash": pw_hash}])

    monkeypatch.setattr(routes.supabase, "table", lambda name: Q())
    tenant_id = "11111111-2222-3333-4444-555555555555"
    assert client.post(f"/api/chat/{tenant_id}/unlock", json={"password": "nope"}).status_code == 401
    resp = client.post(f"/api/chat/{tenant_id}/unlock", json={"password": "letmein"})
    assert resp.status_code == 200
    with app.test_request_context(headers={access.HEADER: resp.get_json()["token"]}):
        assert access.token_ok(tenant_id, pw_hash)



# ── Calendar feeds ────────────────────────────────────────────────────────────

def test_calendar_feed_is_cached_and_empty_when_not_offered(client, monkeypatch):
    from app.tenants import calendar_feed as cf

    tenant = {"id": "t", "name": "Zofingen", "is_active": True, "calendar_feeds": True, "test_password_hash": None}
    events = [{"series": "Papier", "zone": "Zone 1", "event_date": "2099-01-05", "is_exception": False,
               "notes": "", "source_id": None, "created_at": "2026-10-24T10:00:00+00:00"}]
    monkeypatch.setattr(cf, "_tenant", lambda tid: tenant)
    monkeypatch.setattr(cf, "_events", lambda tid: events)
    url = f"/api/calendar/{uuid.uuid4()}/papier--zone-1.ics"

    resp = client.get(url)
    assert resp.status_code == 200 and resp.mimetype == "text/calendar"
    assert "SUMMARY:Papier (Zone 1)" in resp.get_data(as_text=True)
    assert client.get(url, headers={"If-None-Match": resp.headers["ETag"]}).status_code == 304

    tenant["test_password_hash"] = "set"   # password-protected: subscribers see an empty calendar
    assert "BEGIN:VEVENT" not in client.get(url).get_data(as_text=True)


def test_rate_limited_request_is_a_429_not_a_500(app):
    """
    The default limit is checked before the request logging starts; the
    response logging must cope instead of turning the 429 into a bare 500.
    """
    from app import limiter
    limiter.enabled = True
    limiter.reset()
    client = app.test_client()
    get = lambda: client.get("/api/tenants", environ_base={"REMOTE_ADDR": "10.7.7.7"})
    codes = [get().status_code for _ in range(300)]
    assert set(codes) == {401}
    response = get()
    assert response.status_code == 429
    assert response.get_json()["code"] == "rate_limited"
    assert response.headers.get("X-Request-ID")
