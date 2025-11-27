import os
import stripe
from app.database.supabase_client import supabase
from app.logging_config import error_logger

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
STRIPE_PRICE_ID = os.environ.get("STRIPE_PRICE_ID")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000").rstrip('/')

class BillingService:
    @staticmethod
    def get_or_create_customer(user_id, email):
        try:
            # Check if user already has a customer ID
            response = supabase.table("user_billing").select("stripe_customer_id").eq("user_id", user_id).execute()
            
            if response.data and response.data[0].get("stripe_customer_id"):
                return response.data[0].get("stripe_customer_id")
            
            # Create new customer in Stripe
            customer = stripe.Customer.create(
                email=email,
                metadata={"user_id": str(user_id)}
            )
            
            # Save to DB
            # We use upsert to handle case where user_billing row exists but stripe_customer_id is null
            # or if row doesn't exist at all
            data = {
                "user_id": user_id,
                "stripe_customer_id": customer.id,
                "updated_at": "now()"
            }
            supabase.table("user_billing").upsert(data).execute()
            
            return customer.id
        except Exception as e:
            error_logger.error(f"Error getting/creating customer: {e}")
            raise e

    @staticmethod
    def create_checkout_session(user_id, email, amount=20.0, is_recurring=False):
        try:
            customer_id = BillingService.get_or_create_customer(user_id, email)

            # Convert amount to cents
            amount_cents = int(amount * 100)

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
                "line_items": [
                    {
                        "price_data": price_data,
                        "quantity": 1,
                    },
                ],
                "mode": "subscription" if is_recurring else "payment",
                "success_url": f"{FRONTEND_URL}/subscription?success=true&session_id={{CHECKOUT_SESSION_ID}}",
                "cancel_url": f"{FRONTEND_URL}/subscription?canceled=true",
                "client_reference_id": str(user_id),
                "metadata": {"user_id": str(user_id)},
            }

            if not is_recurring:
                checkout_session_kwargs["invoice_creation"] = {"enabled": True}
            
            # Customer is already set above
            # if customer_id:
            #     checkout_session_kwargs["customer"] = customer_id
            # else:
            #     checkout_session_kwargs["customer_email"] = email

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
    def calculate_cost(model, input_tokens, output_tokens):
        """
        Calculates the cost in CHF for the given model and token usage.
        """
        # Rates per 1M tokens in CHF
        # TODO: Move these to a configuration file or database
        RATES = {
            "default": {"input": 8.0, "output": 17.5},
            "gemini-1.5-flash": {"input": 0.315, "output": 0.945}, # Example rates, adjust as needed
            "gemini-2.5-flash-lite": {"input": 0.315, "output": 0.945}, # Example rates
        }
        
        rate = RATES.get(model, RATES["default"])
        cost = (input_tokens / 1_000_000 * rate["input"]) + (output_tokens / 1_000_000 * rate["output"])
        return cost

    @staticmethod
    def deduct_cost(user_id, model, input_tokens, output_tokens):
        cost = BillingService.calculate_cost(model, input_tokens, output_tokens)
        
        try:
            # Deduct from balance
            current_balance = BillingService.check_balance(user_id)
            new_balance = current_balance - cost
            
            supabase.table("user_billing").update({"balance_chf": new_balance, "updated_at": "now()"}).eq("user_id", user_id).execute()
            
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

    @staticmethod
    def get_billing_history(user_id):
        try:
            # We can't easily get email here without fetching user profile, 
            # but usually get_billing_history is called for logged in users who should have a record.
            # If they don't have a record, they probably don't have history.
            # But to be safe and consistent, we could try to fetch or create if we had the email.
            # For now, let's just check the DB.
            
            response = supabase.table("user_billing").select("stripe_customer_id").eq("user_id", user_id).execute()
            if not response.data or not response.data[0].get("stripe_customer_id"):
                return []

            customer_id = response.data[0].get("stripe_customer_id")
            
            # Fetch invoices and sessions to build a history
            # For simplicity, we'll just list invoices which cover both one-time (if finalized) and recurring
            invoices = stripe.Invoice.list(customer=customer_id, limit=20)
            
            history = []
            for invoice in invoices.data:
                history.append({
                    "id": invoice.id,
                    "date": invoice.created,
                    "amount": invoice.total / 100.0,
                    "currency": invoice.currency.upper(),
                    "status": invoice.status,
                    "pdf_url": invoice.invoice_pdf,
                    "number": invoice.number
                })
                
            return history
        except Exception as e:
            error_logger.error(f"Error fetching billing history: {e}")
            return []
