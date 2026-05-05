"""Smoke tests for app startup and route registration."""


def test_app_creates(app):
    """App factory should return an app without crashing."""
    assert app is not None


def test_blueprints_registered(app):
    """All expected blueprints should be registered."""
    blueprint_names = list(app.blueprints.keys())
    for expected in ['auth', 'tenants', 'sources', 'widget', 'chat', 'billing']:
        assert expected in blueprint_names, f"Blueprint '{expected}' not registered"
