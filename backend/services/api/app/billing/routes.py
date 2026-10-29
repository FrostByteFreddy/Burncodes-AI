from flask import request, jsonify, redirect
from app.billing import billing_bp
from app.billing.services import BillingService, BillingError
from app.auth.decorators import token_required
from app.logging_config import error_logger
import math
import stripe
import os

MAX_RECHARGE_CHF = 10_000

@billing_bp.route('/create-checkout-session', methods=['POST'])
@token_required
def create_checkout_session(current_user):
    try:
        user_id = current_user.id
        email = current_user.email
        
        data = request.get_json() or {}
        amount = data.get('amount', 20.0)
        
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            return jsonify({'error': 'Invalid amount'}), 400
        if not math.isfinite(amount) or amount > MAX_RECHARGE_CHF:
            return jsonify({'error': 'Invalid amount'}), 400
        if amount < 5.0:
            return jsonify({'error': 'Minimum recharge amount is 5 CHF'}), 400

        checkout_url = BillingService.create_checkout_session(user_id, email, amount, bool(data.get('is_recurring', False)))
        return jsonify({'url': checkout_url})
    except Exception as e:
        error_logger.error(f"Error in create_checkout_session route: {e}")
        return jsonify({'error': 'An internal error occurred'}), 500

@billing_bp.route('/history', methods=['GET'])
@token_required
def get_history(current_user):
    try:
        history = BillingService.get_billing_history(current_user.id)
        return jsonify({'history': history})
    except Exception as e:
        error_logger.error(f"Error getting history: {e}")
        return jsonify({'error': 'An internal error occurred'}), 500

@billing_bp.route('/portal', methods=['POST'])
@token_required
def customer_portal(current_user):
    try:
        # We need the customer ID to create a portal session
        # We can fetch it from our DB or let Stripe handle it if we had stored it in a way Stripe expects, 
        # but usually we need to pass customer_id to stripe.billing_portal.Session.create
        
        from app.database.supabase_client import supabase
        response = supabase.table("user_billing").select("stripe_customer_id").eq("user_id", current_user.id).execute()
        
        if not response.data or not response.data[0].get("stripe_customer_id"):
            return jsonify({'error': 'No billing account found'}), 404
            
        customer_id = response.data[0].get("stripe_customer_id")
        
        # This is the URL to which the user is redirected after they are done managing their billing in the portal.
        return_url = os.environ.get("FRONTEND_URL", "http://localhost:3000").rstrip("/") + "/settings/billing"

        portal_session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        return jsonify({'url': portal_session.url})
    except Exception as e:
        error_logger.error(f"Error in customer_portal route: {e}")
        return jsonify({'error': 'An internal error occurred'}), 500

@billing_bp.route('/balance', methods=['GET'])
@token_required
def get_balance(current_user):
    try:
        balance = BillingService.check_balance(current_user.id)
        return jsonify({'balance_chf': balance})
    except Exception as e:
        error_logger.error(f"Error getting balance: {e}")
        return jsonify({'error': 'An internal error occurred'}), 500

@billing_bp.route('/usage', methods=['GET'])
@token_required
def get_usage(current_user):
    try:
        from app.database.supabase_client import supabase

        response = supabase.rpc('usage_totals', {'p_user_id': current_user.id}).execute()
        row = (response.data or [{}])[0]
        # what was spent, as booked in the ledger (survives deleted runs and chatbots)
        from app.database.supabase_client import fetch_all
        booked = fetch_all(lambda: supabase.table('billing_ledger').select('kind, amount_chf')
                           .eq('user_id', current_user.id).lt('amount_chf', 0).order('id'))
        by_kind = {}
        for r in booked:
            by_kind[r['kind']] = by_kind.get(r['kind'], 0.0) - float(r['amount_chf'])
        chat_cost = round(by_kind.get('answer', 0.0), 4)
        sources_cost = round(by_kind.get('learning', 0.0), 4)
        review_cost = round(by_kind.get('review', 0.0), 4)
        return jsonify({
            'total_cost': chat_cost + sources_cost + review_cost,
            'input_tokens': int(row.get('chat_input') or 0) + int(row.get('sources_input') or 0),
            'output_tokens': int(row.get('chat_output') or 0) + int(row.get('sources_output') or 0),
            'chat_cost': chat_cost,
            'sources_cost': sources_cost,
            'review_cost': round(review_cost, 4)
        })
    except Exception as e:
        error_logger.error(f"Error getting usage: {e}")
        return jsonify({'error': 'An internal error occurred'}), 500

@billing_bp.route('/verify-session', methods=['POST'])
@token_required
def verify_session(current_user):
    try:
        data = request.get_json() or {}
        session_id = data.get('session_id')
        if not session_id or not isinstance(session_id, str):
            return jsonify({'error': 'Missing session_id'}), 400

        success = BillingService.verify_session(session_id, current_user.id)
        return jsonify({'success': success})
    except BillingError:
        return jsonify({'error': 'Checkout session not found'}), 404
    except stripe.error.InvalidRequestError:
        return jsonify({'error': 'Checkout session not found'}), 404
    except Exception as e:
        error_logger.error(f"Error verifying session: {e}")
        return jsonify({'error': 'An internal error occurred'}), 500
