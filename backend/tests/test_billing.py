"""Test billing service cost calculation (no external deps)."""

from app.billing.services import BillingService


class TestCalculateCost:
    def test_chat_rate(self):
        """Chat uses the chat role rate (default 8.0 / 17.5 CHF per 1M tokens)."""
        cost = BillingService.calculate_cost("chat", 1_000_000, 1_000_000)
        assert cost == pytest.approx(25.5)

    def test_unknown_role_falls_back_to_chat_rate(self):
        assert BillingService.calculate_cost("whatever", 1_000_000, 0) == pytest.approx(8.0)

    def test_indexing_rate_has_no_output_component(self):
        cost = BillingService.calculate_cost("indexing", 1_000_000, 1_000_000)
        assert cost == pytest.approx(0.15)

    def test_zero_tokens(self):
        """Zero tokens should yield zero cost."""
        assert BillingService.calculate_cost("chat", 0, 0) == 0.0

    def test_small_token_count(self):
        """Small token counts should produce proportional costs."""
        cost = BillingService.calculate_cost("chat", 1000, 500)
        assert cost == pytest.approx((1000 / 1_000_000 * 8.0) + (500 / 1_000_000 * 17.5))

    def test_rates_are_configurable_via_env(self, monkeypatch):
        import importlib
        from app import ai_models
        monkeypatch.setenv("CHAT_RATE_CHF_PER_1M_INPUT", "2.5")
        monkeypatch.setenv("CHAT_GEMINI_MODEL", "gemini-test-model")
        reloaded = importlib.reload(ai_models)
        try:
            assert reloaded.RATES["chat"]["input"] == 2.5
            assert reloaded.CHAT_GEMINI_MODEL == "gemini-test-model"
        finally:
            monkeypatch.undo()
            importlib.reload(ai_models)


import pytest
