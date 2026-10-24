"""
Stripe crediting must happen exactly once per paid object.

The once-only guarantee lives in the apply_payment SQL function
(processed_payments primary key); these tests pin down which Stripe objects
reach it, with which idempotency key, and that verify-session can't be used
to credit someone else's or an old session.
"""
import time
from unittest.mock import MagicMock

import pytest

from app.billing import services
from app.billing.services import BillingError, BillingService


@pytest.fixture
def rpc(monkeypatch):
    fake_db = MagicMock()
    fake_db.rpc.return_value.execute.return_value.data = True
    monkeypatch.setattr(services, "supabase", fake_db)
    return fake_db


def _apply_calls(fake_db):
    return [c for c in fake_db.rpc.call_args_list if c.args[0] == "apply_payment"]


def test_one_time_checkout_credits_with_session_key(rpc):
    BillingService.handle_checkout_completed({
        "id": "cs_1", "mode": "payment", "payment_status": "paid",
        "amount_total": 2000, "client_reference_id": "user-1", "customer": "cus_1",
    })
    (call,) = _apply_calls(rpc)
    assert call.args[1] == {"p_source_id": "checkout:cs_1", "p_user_id": "user-1", "p_amount": 20.0}


def test_subscription_checkout_does_not_credit(rpc):
    BillingService.handle_checkout_completed({
        "id": "cs_2", "mode": "subscription", "payment_status": "paid",
        "amount_total": 2000, "client_reference_id": "user-1",
    })
    assert _apply_calls(rpc) == []


def test_one_time_invoice_is_ignored(rpc):
    """invoice_creation on one-time checkouts emits invoice events too — already credited."""
    BillingService.handle_invoice_paid({"id": "in_1", "billing_reason": "manual", "customer": "cus_1", "amount_paid": 2000})
    assert _apply_calls(rpc) == []
    rpc.table.assert_not_called()


@pytest.mark.parametrize("reason", ["subscription_create", "subscription_cycle"])
def test_subscription_invoice_credits_with_invoice_key(rpc, reason):
    rpc.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{"user_id": "user-1"}]
    BillingService.handle_invoice_paid({"id": "in_2", "billing_reason": reason, "customer": "cus_1", "amount_paid": 2000})
    (call,) = _apply_calls(rpc)
    assert call.args[1] == {"p_source_id": "invoice:in_2", "p_user_id": "user-1", "p_amount": 20.0}


def _session(**overrides):
    session = {
        "id": "cs_3", "mode": "payment", "payment_status": "paid", "amount_total": 500,
        "client_reference_id": "user-1", "created": int(time.time()),
    }
    session.update(overrides)
    return session


def test_verify_session_rejects_foreign_session(rpc, monkeypatch):
    monkeypatch.setattr(services.stripe.checkout.Session, "retrieve", lambda sid: _session())
    with pytest.raises(BillingError):
        BillingService.verify_session("cs_3", "someone-else")
    assert _apply_calls(rpc) == []


def test_verify_session_credits_fresh_session_once_per_key(rpc, monkeypatch):
    monkeypatch.setattr(services.stripe.checkout.Session, "retrieve", lambda sid: _session())
    assert BillingService.verify_session("cs_3", "user-1") is True
    assert [c.args[1]["p_source_id"] for c in _apply_calls(rpc)] == ["checkout:cs_3"]


def test_verify_session_does_not_credit_stale_session(rpc, monkeypatch):
    stale = _session(created=int(time.time()) - services.VERIFY_SESSION_MAX_AGE_SECONDS - 60)
    monkeypatch.setattr(services.stripe.checkout.Session, "retrieve", lambda sid: stale)
    assert BillingService.verify_session("cs_3", "user-1") is True
    assert _apply_calls(rpc) == []


def test_verify_session_route_maps_foreign_session_to_404(client, auth_as, rpc, monkeypatch):
    monkeypatch.setattr(services.stripe.checkout.Session, "retrieve", lambda sid: _session(client_reference_id="other"))
    resp = client.post("/api/billing/verify-session", headers=auth_as, json={"session_id": "cs_3"})
    assert resp.status_code == 404


@pytest.mark.parametrize("amount", ["nan", "inf", 1e9, "abc", None])
def test_checkout_rejects_bad_amounts(client, auth_as, amount):
    resp = client.post("/api/billing/create-checkout-session", headers=auth_as, json={"amount": amount})
    assert resp.status_code == 400


def test_indexing_estimate_uses_text_vs_binary_ratio():
    assert BillingService.estimate_indexing_tokens(4000, ".txt") == 1000
    assert BillingService.estimate_indexing_tokens(4000, ".pdf") == 400
    assert BillingService.estimate_indexing_tokens(0, ".pdf") == 1
