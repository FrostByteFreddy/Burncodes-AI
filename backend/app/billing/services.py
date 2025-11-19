import os
import stripe
from app.database.supabase_client import supabase
from app.logging_config import error_logger

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
STRIPE_PRICE_ID = os.environ.get("STRIPE_PRICE_ID")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000").rstrip('/')

class BillingService:
    @staticmethod
    def create_checkout_session(user_id, email, amount=20.0):
        try:
            # Check if user already has a customer ID
            response = supabase.table("user_billing").select("stripe_customer_id").eq("user_id", user_id).execute()
            customer_id = None
            if response.data:
                customer_id = response.data[0].get("stripe_customer_id")

            # Convert amount to cents
            amount_cents = int(amount * 100)

            checkout_session_kwargs = {
                "payment_method_types": ["card"],
                "line_items": [
                    {
                        "price_data": {
                            "currency": "chf",
                            "product_data": {
                                "name": "Balance Recharge",
                                "description": f"Add {amount:.2f} CHF to your balance",
                            },
                            "unit_amount": amount_cents,
                        },
                        "quantity": 1,
                    },
                ],
                "mode": "payment",
                "success_url": f"{FRONTEND_URL}/subscription?success=true&session_id={{CHECKOUT_SESSION_ID}}",
                "cancel_url": f"{FRONTEND_URL}/subscription?canceled=true",
                "client_reference_id": str(user_id),
                "metadata": {"user_id": str(user_id)},
            }

            if customer_id:
                checkout_session_kwargs["customer"] = customer_id
            else:
                checkout_session_kwargs["customer_email"] = email

            checkout_session = stripe.checkout.Session.create(**checkout_session_kwargs)
            return checkout_session.url
        except Exception as e:
            error_logger.error(f"Error creating checkout session: {e}")
            raise e

    @staticmethod
    def handle_checkout_completed(session):
        user_id = session.get("client_reference_id") or session.get("metadata", {}).get("user_id")
        customer_id = session.get("customer")
        subscription_id = session.get("subscription")
        payment_status = session.get("payment_status")
        amount_total = session.get("amount_total") # in cents

        if not user_id:
            error_logger.error("No user_id found in checkout session")
            return

        # Update user_billing with customer_id and subscription_id
        try:
            # Upsert user_billing
            data = {
                "user_id": user_id,
                "stripe_customer_id": customer_id,
                "stripe_subscription_id": subscription_id,
                "updated_at": "now()"
            }
            supabase.table("user_billing").upsert(data).execute()
            
            # If it's a one-time payment and successful, credit the balance here
            if session.get("mode") == "payment" and payment_status == "paid":
                current_balance = BillingService.check_balance(user_id)
                amount_chf = amount_total / 100.0
                new_balance = current_balance + amount_chf
                supabase.table("user_billing").update({"balance_chf": new_balance, "updated_at": "now()"}).eq("user_id", user_id).execute()
                
        except Exception as e:
            error_logger.error(f"Error handling checkout completed: {e}")
            raise e

    @staticmethod
    def handle_invoice_paid(invoice):
        customer_id = invoice.get("customer")
        subscription_id = invoice.get("subscription")
        
        # Find user by customer_id or subscription_id if needed, but we should rely on what we stored.
        # However, invoice object might not have user_id metadata if it wasn't passed down from subscription.
        # Stripe subscriptions usually inherit metadata from checkout session but let's check.
        # Better to query our DB to find the user associated with this customer_id.
        
        try:
            response = supabase.table("user_billing").select("user_id, balance_chf").eq("stripe_customer_id", customer_id).execute()
            if not response.data:
                error_logger.error(f"No user found for customer_id {customer_id}")
                return
            
            user_record = response.data[0]
            user_id = user_record["user_id"]
            current_balance = float(user_record.get("balance_chf", 0.0))
            
            # Determine amount to add. 
            # For now, let's assume the recharge amount is fixed or we get it from the invoice.
            # Invoice amount_paid is in cents.
            amount_paid_cents = invoice.get("amount_paid")
            currency = invoice.get("currency")
            
            # Assuming CHF. 20 CHF = 2000 cents.
            # If we want to credit exactly what was paid:
            amount_chf = amount_paid_cents / 100.0
            
            new_balance = current_balance + amount_chf
            
            supabase.table("user_billing").update({"balance_chf": new_balance, "updated_at": "now()"}).eq("user_id", user_id).execute()
            
        except Exception as e:
            error_logger.error(f"Error handling invoice paid: {e}")
            raise e

    @staticmethod
    def check_balance(user_id):
        try:
            response = supabase.table("user_billing").select("balance_chf").eq("user_id", user_id).execute()
            if response.data:
                return float(response.data[0].get("balance_chf", 0.0))
            return 0.0
        except Exception as e:
            error_logger.error(f"Error checking balance: {e}")
            return 0.0

    @staticmethod
    def deduct_cost(user_id, model, input_tokens, output_tokens):
        # Calculate cost based on model
        # Pricing (example values, should be configured somewhere)
        # GPT-4o: Input $5/1M, Output $15/1M
        # GPT-3.5-turbo: Input $0.5/1M, Output $1.5/1M
        # Let's assume some default rates or fetch from config.
        # For now I will hardcode some approximate CHF rates (1 USD ~= 0.9 CHF)
        
        # Rates per 1M tokens in CHF
        RATES = {
            "gpt-4o": {"input": 4.5, "output": 13.5},
            "gpt-4o-mini": {"input": 0.135, "output": 0.54},
            # Default to gpt-4o if unknown
            "default": {"input": 4.5, "output": 13.5}
        }
        
        rate = RATES.get(model, RATES["default"])
        cost = (input_tokens / 1_000_000 * rate["input"]) + (output_tokens / 1_000_000 * rate["output"])
        
        try:
            # Deduct from balance
            # We need to fetch current balance first to ensure we don't go negative (though we check before chat)
            # Or just decrement.
            
            # It's better to do this in a transaction or RPC, but with Supabase client we might just do read-then-write
            # for simplicity in this MVP.
            
            current_balance = BillingService.check_balance(user_id)
            new_balance = current_balance - cost
            
            supabase.table("user_billing").update({"balance_chf": new_balance, "updated_at": "now()"}).eq("user_id", user_id).execute()
            
            return cost
            return cost
        except Exception as e:
            error_logger.error(f"Error deducting cost: {e}")
            return 0.0

    @staticmethod
    def verify_session(session_id):
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == 'paid':
                BillingService.handle_checkout_completed(session)
                return True
            return False
        except Exception as e:
            error_logger.error(f"Error verifying session {session_id}: {e}")
            raise e
