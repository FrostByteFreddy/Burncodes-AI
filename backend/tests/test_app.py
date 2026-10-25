"""Smoke tests for app startup and route registration."""


def test_app_creates(app):
    """App factory should return an app without crashing."""
    assert app is not None


def test_blueprints_registered(app):
    """All expected blueprints should be registered."""
    blueprint_names = list(app.blueprints.keys())
    for expected in ['auth', 'tenants', 'sources', 'widget', 'chat', 'billing']:
        assert expected in blueprint_names, f"Blueprint '{expected}' not registered"


def test_public_links_use_the_address_the_request_came_in_on(app, monkeypatch):
    """Behind nginx without API_BASE_URL: calendar feeds and the embed script must not point at localhost."""
    monkeypatch.delenv("API_BASE_URL", raising=False)
    client = app.test_client()
    behind_nginx = {"Host": "ai.burn.codes", "X-Forwarded-Proto": "https", "X-Forwarded-For": "1.2.3.4"}
    script = client.get("/api/tenants/widget.js", headers=behind_nginx).get_data(as_text=True)
    assert '"https://ai.burn.codes"' in script and "localhost" not in script

    # test_request_context skips ProxyFix (the widget request above went through it): set its result
    after_proxyfix = {"base_url": "https://ai.burn.codes/"}
    with app.test_request_context("/", **after_proxyfix):
        from app.tenants.calendar_feed import feed_urls
        urls = feed_urls("t1", "abfall")
    assert urls == {"https": "https://ai.burn.codes/api/calendar/t1/abfall.ics",
                    "webcal": "webcal://ai.burn.codes/api/calendar/t1/abfall.ics"}

    monkeypatch.setenv("API_BASE_URL", "https://api.example.ch/")
    with app.test_request_context("/", **after_proxyfix):
        assert feed_urls("t1", "abfall")["https"] == "https://api.example.ch/api/calendar/t1/abfall.ics"
