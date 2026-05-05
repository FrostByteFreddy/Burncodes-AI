"""Test billing service cost calculation (no external deps)."""

from app.billing.services import BillingService


class TestCalculateCost:
    def test_default_model_rates(self):
        """Default model should use the default rate."""
        cost = BillingService.calculate_cost("unknown-model", 1_000_000, 1_000_000)
        # default: input=8.0, output=17.5 per 1M tokens
        assert cost == pytest.approx(25.5)

    def test_flash_lite_rates(self):
        """gemini-2.5-flash-lite should use its configured rate."""
        cost = BillingService.calculate_cost("gemini-2.5-flash-lite", 1_000_000, 1_000_000)
        # input=0.315, output=0.945 per 1M tokens
        assert cost == pytest.approx(1.26)

    def test_zero_tokens(self):
        """Zero tokens should yield zero cost."""
        cost = BillingService.calculate_cost("gemini-2.5-flash-lite", 0, 0)
        assert cost == 0.0

    def test_small_token_count(self):
        """Small token counts should produce proportional costs."""
        cost = BillingService.calculate_cost("gemini-2.5-flash-lite", 1000, 500)
        expected = (1000 / 1_000_000 * 0.315) + (500 / 1_000_000 * 0.945)
        assert cost == pytest.approx(expected)


import pytest
