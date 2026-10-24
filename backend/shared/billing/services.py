"""
shared/billing/services.py

Single source of truth for balance checks, cost deduction and Stripe crediting.
Copied into every service image as app/billing/services.py (see Dockerfiles)
and symlinked there for local dev.
"""
import os
import time

import stripe
from app.database.supabase_client import supabase
from app.database.supabase_retry import retrying_execute
from app.logging_config import error_logger

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000").rstrip('/')

# verify-session only accepts sessions this fresh. The success redirect happens
# seconds after payment; older sessions are left to the (idempotent) webhook.
VERIFY_SESSION_MAX_AGE_SECONDS = 60 * 60

# Rates per 1M tokens in CHF. Override the chat/indexing rates via env so
# pricing changes don't need a deploy of code.
RATES = {
    "default": {"input": 8.0, "output": 17.5},
    "gemini-1.5-flash": {"input": 0.315, "output": 0.945},
    "gemini-2.5-flash-lite": {"input": 0.315, "output": 0.945},
    "indexing": {
        "input": float(os.environ.get("INDEXING_RATE_CHF_PER_1M_TOKENS", "0.15")),
        "output": 0.0,
    },
}

# Rough bytes→tokens ratios used to estimate indexing cost before Gemini
# reports anything. Text is ~4 chars/token; binary formats (PDF, DOCX, images)
# carry a lot of non-text overhead per token.
_TEXT_BYTES_PER_TOKEN = 4
_BINARY_BYTES_PER_TOKEN = 10
_TEXT_SUFFIXES = {".txt", ".md", ".csv", ".html", ".htm"}


class BillingError(Exception):
    """Raised when a billing precondition (e.g. ownership) is not met."""


class BillingService:
    # ------------------------------------------------------------------
    # Lookups
    # ------------------------------------------------------------------

    @staticmethod
    def get_tenant_owner(tenant_id):
        """Returns the user_id owning a tenant, or None if the tenant doesn't exist."""
        response = retrying_execute(
            supabase.table("tenants").select("user_id").eq("id", str(tenant_id)).limit(1)
        )
        if not response.data:
            return None
        return response.data[0]["user_id"]

    @staticmethod
    def check_balance(user_id):
        """Returns the user's balance. Raises on DB errors so callers can fail closed."""
        response = retrying_execute(
            supabase.table("user_billing").select("balance_chf").eq("user_id", user_id)
        )
        if response.data:
            return float(response.data[0].get("balance_chf") or 0.0)
        return 0.0

    @staticmethod
    def tenant_has_balance(tenant_id):
        """True if the tenant's owner has a positive balance. Raises on DB errors."""
        owner = BillingService.get_tenant_owner(tenant_id)
        if not owner:
            return False
        return BillingService.check_balance(owner) > 0

    # ------------------------------------------------------------------
    # Stripe checkout
    # ------------------------------------------------------------------

    @staticmethod
    def get_or_create_customer(user_id, email):
        try:
            response = retrying_execute(
                supabase.table("user_billing").select("stripe_customer_id").eq("user_id", user_id)
            )
            if response.data and response.data[0].get("stripe_customer_id"):
                return response.data[0].get("stripe_customer_id")

            customer = stripe.Customer.create(email=email, metadata={"user_id": str(user_id)})

            # Upsert handles both a missing row and a row with a null customer id
            supabase.table("user_billing").upsert({
                "user_id": user_id,
                "stripe_customer_id": customer.id,
                "updated_at": "now()",
            }).execute()
            return customer.id
        except Exception as e:
            error_logger.error(f"Error getting/creating customer: {e}")
            raise

    @staticmethod
    def create_checkout_session(user_id, email, amount=20.0, is_recurring=False):
        try:
            customer_id = BillingService.get_or_create_customer(user_id, email)
            amount_cents = int(round(amount * 100))

            price_data = {
                "currency": "chf",
                "product_data": {
                    "name": "Monthly Subscription" if is_recurring else "Balance Recharge",
                    "description": f"Add {amount:.2f} CHF to your balance monthly" if is_recurring else f"Add {amount:.2f} CHF to your balance",
                },
                "unit_amount": amount_cents,
            }
            if is_recurring:
                price_data["recurring"] = {"interval": "month"}

            checkout_session_kwargs = {
                "payment_method_types": ["card"],
                "customer": customer_id,
                "line_items": [{"price_data": price_data, "quantity": 1}],
                "mode": "subscription" if is_recurring else "payment",
                "success_url": f"{FRONTEND_URL}/subscription?success=true&session_id={{CHECKOUT_SESSION_ID}}",
                "cancel_url": f"{FRONTEND_URL}/subscription?canceled=true",
                "client_reference_id": str(user_id),
                "metadata": {"user_id": str(user_id)},
            }
            if not is_recurring:
                checkout_session_kwargs["invoice_creation"] = {"enabled": True}

            checkout_session = stripe.checkout.Session.create(**checkout_session_kwargs)
            return checkout_session.url
        except Exception as e:
            error_logger.error(f"Error creating checkout session: {e}")
            raise

    # ------------------------------------------------------------------
    # Crediting — every credit goes through apply_payment(), which records
    # the Stripe object id in processed_payments and credits at most once.
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_payment(source_id, user_id, amount_chf):
        """Credits the balance once per source_id. Returns True if this call credited."""
        result = supabase.rpc("apply_payment", {
            "p_source_id": source_id,
            "p_user_id": user_id,
            "p_amount": amount_chf,
        }).execute()
        credited = bool(result.data)
        if not credited:
            error_logger.info("Payment %s already credited — skipping", source_id)
        return credited

    @staticmethod
    def handle_checkout_completed(session):
        user_id = session.get("client_reference_id") or (session.get("metadata") or {}).get("user_id")
        if not user_id:
            error_logger.error("No user_id found in checkout session")
            return

        try:
            supabase.table("user_billing").upsert({
                "user_id": user_id,
                "stripe_customer_id": session.get("customer"),
                "stripe_subscription_id": session.get("subscription"),
                "updated_at": "now()",
            }).execute()

            # One-time payments are credited here. Subscription payments are
            # credited from invoice.payment_succeeded (see handle_invoice_paid).
            if session.get("mode") == "payment" and session.get("payment_status") == "paid":
                amount_chf = (session.get("amount_total") or 0) / 100.0
                BillingService._apply_payment(f"checkout:{session.get('id')}", user_id, amount_chf)
        except Exception as e:
            error_logger.error(f"Error handling checkout completed: {e}")
            raise

    @staticmethod
    def handle_invoice_paid(invoice):
        # One-time checkouts with invoice_creation also emit invoice events
        # (billing_reason="manual"); those were already credited by the
        # checkout handler. Only subscription invoices add balance here.
        billing_reason = invoice.get("billing_reason") or ""
        if not billing_reason.startswith("subscription"):
            error_logger.info(
                "Ignoring invoice %s with billing_reason=%s", invoice.get("id"), billing_reason
            )
            return

        customer_id = invoice.get("customer")
        try:
            response = supabase.table("user_billing").select("user_id").eq("stripe_customer_id", customer_id).execute()
            if not response.data:
                error_logger.error(f"No user found for customer_id {customer_id}")
                return

            user_id = response.data[0]["user_id"]
            amount_chf = (invoice.get("amount_paid") or 0) / 100.0
            BillingService._apply_payment(f"invoice:{invoice.get('id')}", user_id, amount_chf)
        except Exception as e:
            error_logger.error(f"Error handling invoice paid: {e}")
            raise

    @staticmethod
    def verify_session(session_id, user_id):
        """
        Called from the success redirect so the balance updates without waiting
        for the webhook. Only credits fresh sessions that belong to the caller;
        apply_payment makes it a no-op if the webhook got there first.
        """
        session = stripe.checkout.Session.retrieve(session_id)
        owner = session.get("client_reference_id") or (session.get("metadata") or {}).get("user_id")
        if str(owner) != str(user_id):
            raise BillingError("Checkout session does not belong to this user")
        if session.get("payment_status") != "paid":
            return False
        if time.time() - (session.get("created") or 0) > VERIFY_SESSION_MAX_AGE_SECONDS:
            # Stale session: report status only, crediting is the webhook's job.
            return True
        BillingService.handle_checkout_completed(session)
        return True

    # ------------------------------------------------------------------
    # Cost deduction
    # ------------------------------------------------------------------

    @staticmethod
    def calculate_cost(model, input_tokens, output_tokens):
        """Calculates the cost in CHF for the given model and token usage."""
        rate = RATES.get(model, RATES["default"])
        return (input_tokens / 1_000_000 * rate["input"]) + (output_tokens / 1_000_000 * rate["output"])

    @staticmethod
    def deduct_cost(user_id, model, input_tokens, output_tokens):
        cost = BillingService.calculate_cost(model, input_tokens, output_tokens)
        try:
            result = supabase.rpc("deduct_balance", {"p_user_id": user_id, "p_amount": cost}).execute()
            if result.data == -1:
                error_logger.error(f"User {user_id} not found in user_billing during deduction")
                return 0.0
            return cost
        except Exception as e:
            error_logger.error(f"Error deducting cost: {e}")
            return 0.0

    @staticmethod
    def estimate_indexing_tokens(size_bytes, suffix):
        per_token = _TEXT_BYTES_PER_TOKEN if suffix.lower() in _TEXT_SUFFIXES else _BINARY_BYTES_PER_TOKEN
        return max(1, size_bytes // per_token)

    @staticmethod
    def charge_indexing(tenant_id, source_id, input_tokens):
        """
        Deducts the indexing cost for one document from the tenant owner's
        balance and records it on the tenant_sources row (feeds /billing/usage).
        Never raises — a billing hiccup must not fail an already-indexed document.
        """
        try:
            owner = BillingService.get_tenant_owner(tenant_id)
            if not owner:
                return 0.0
            cost = BillingService.deduct_cost(owner, "indexing", input_tokens, 0)
            if source_id is not None:
                supabase.table("tenant_sources").update({
                    "cost_chf": cost,
                    "input_tokens": input_tokens,
                    "output_tokens": 0,
                }).eq("id", source_id).execute()
            return cost
        except Exception as e:
            error_logger.error(f"Error charging indexing for tenant {tenant_id}: {e}")
            return 0.0

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    @staticmethod
    def get_billing_history(user_id):
        try:
            response = supabase.table("user_billing").select("stripe_customer_id").eq("user_id", user_id).execute()
            if not response.data or not response.data[0].get("stripe_customer_id"):
                return []

            invoices = stripe.Invoice.list(customer=response.data[0]["stripe_customer_id"], limit=20)
            return [
                {
                    "id": invoice.id,
                    "date": invoice.created,
                    "amount": invoice.total / 100.0,
                    "currency": invoice.currency.upper(),
                    "status": invoice.status,
                    "pdf_url": invoice.invoice_pdf,
                    "number": invoice.number,
                }
                for invoice in invoices.data
            ]
        except Exception as e:
            error_logger.error(f"Error fetching billing history: {e}")
            return []
