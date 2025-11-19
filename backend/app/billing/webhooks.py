from flask import request, jsonify
from app.billing import billing_bp
from app.billing.services import BillingService
from app.logging_config import error_logger
import stripe
import os

@billing_bp.route('/webhook', methods=['POST'])
def webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')

    if not webhook_secret:
        error_logger.error("STRIPE_WEBHOOK_SECRET is not set")
        return jsonify({'error': 'Webhook secret not configured'}), 500

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        # Invalid payload
        error_logger.error(f"Invalid payload: {e}")
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        error_logger.error(f"Invalid signature: {e}")
        return jsonify({'error': 'Invalid signature'}), 400

    # Handle the event
    try:
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            BillingService.handle_checkout_completed(session)
        elif event['type'] == 'invoice.payment_succeeded':
            invoice = event['data']['object']
            BillingService.handle_invoice_paid(invoice)
        # Add other event types if needed
        
    except Exception as e:
        error_logger.error(f"Error handling webhook event {event['type']}: {e}")
        return jsonify({'error': 'Webhook handler failed'}), 500

    return jsonify({'status': 'success'}), 200
