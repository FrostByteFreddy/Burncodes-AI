from flask import request, jsonify, redirect
from app.billing import billing_bp
from app.billing.services import BillingService
from app.auth.decorators import token_required
from app.logging_config import error_logger
import stripe
import os

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
            if amount < 5.0:
                return jsonify({'error': 'Minimum recharge amount is 5 CHF'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid amount'}), 400
            
        checkout_url = BillingService.create_checkout_session(user_id, email, amount, data.get('is_recurring', False))
        return jsonify({'url': checkout_url})
    except Exception as e:
        error_logger.error(f"Error in create_checkout_session route: {e}")
        return jsonify({'error': str(e)}), 500

@billing_bp.route('/history', methods=['GET'])
@token_required
def get_history(current_user):
    try:
        history = BillingService.get_billing_history(current_user.id)
        return jsonify({'history': history})
    except Exception as e:
        error_logger.error(f"Error getting history: {e}")
        return jsonify({'error': str(e)}), 500

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
        return_url = os.environ.get("FRONTEND_URL", "http://localhost:3000") + "/billing"

        portal_session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        return jsonify({'url': portal_session.url})
    except Exception as e:
        error_logger.error(f"Error in customer_portal route: {e}")
        return jsonify({'error': str(e)}), 500

@billing_bp.route('/balance', methods=['GET'])
@token_required
def get_balance(current_user):
    try:
        balance = BillingService.check_balance(current_user.id)
        return jsonify({'balance_chf': balance})
    except Exception as e:
        error_logger.error(f"Error getting balance: {e}")
        return jsonify({'error': str(e)}), 500

@billing_bp.route('/usage', methods=['GET'])
@token_required
def get_usage(current_user):
    try:
        from app.database.supabase_client import supabase
        
        # Get user's tenants
        tenants_response = supabase.table("tenants").select("id").eq("user_id", current_user.id).execute()
        if not tenants_response.data:
            return jsonify({'total_cost': 0.0, 'input_tokens': 0, 'output_tokens': 0})
            
        tenant_ids = [t['id'] for t in tenants_response.data]
        
        # Query chat_logs for these tenants
        # Note: For production, use an RPC or View for aggregation to avoid fetching all rows.
        logs_response = supabase.table("chat_logs").select("cost_chf, input_tokens, output_tokens").in_("tenant_id", tenant_ids).execute()
        
        chat_cost = sum(float(item.get('cost_chf', 0) or 0) for item in logs_response.data)
        chat_input = sum(int(item.get('input_tokens', 0) or 0) for item in logs_response.data)
        chat_output = sum(int(item.get('output_tokens', 0) or 0) for item in logs_response.data)

        # Query tenant_sources for these tenants
        sources_response = supabase.table("tenant_sources").select("cost_chf, input_tokens, output_tokens").in_("tenant_id", tenant_ids).execute()

        sources_cost = sum(float(item.get('cost_chf', 0) or 0) for item in sources_response.data)
        sources_input = sum(int(item.get('input_tokens', 0) or 0) for item in sources_response.data)
        sources_output = sum(int(item.get('output_tokens', 0) or 0) for item in sources_response.data)
        
        return jsonify({
            'total_cost': chat_cost + sources_cost,
            'input_tokens': chat_input + sources_input,
            'output_tokens': chat_output + sources_output,
            'chat_cost': chat_cost,
            'sources_cost': sources_cost
        })
    except Exception as e:
        error_logger.error(f"Error getting usage: {e}")
        return jsonify({'error': str(e)}), 500

@billing_bp.route('/verify-session', methods=['POST'])
@token_required
def verify_session(current_user):
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        if not session_id:
            return jsonify({'error': 'Missing session_id'}), 400
            
        success = BillingService.verify_session(session_id)
        return jsonify({'success': success})
    except Exception as e:
        error_logger.error(f"Error verifying session: {e}")
        return jsonify({'error': str(e)}), 500
