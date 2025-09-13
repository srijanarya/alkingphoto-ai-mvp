"""
TalkingPhoto AI MVP - Stripe Webhook Service
Secure webhook handling for payment confirmations and subscription events
"""

import stripe
import json
import logging
import hmac
import hashlib
import time
from datetime import datetime
from typing import Dict, Optional
from flask import Flask, request, jsonify
from services.payment_service import payment_service, PaymentStatus
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = Config.STRIPE_SECRET_KEY


class WebhookService:
    """
    Secure Stripe webhook handling service
    Processes payment confirmations, subscription updates, and failed payments
    """
    
    def __init__(self):
        self.webhook_secret = Config.STRIPE_WEBHOOK_SECRET
        self.app = Flask(__name__)
        self.setup_routes()
    
    def setup_routes(self):
        """Setup Flask routes for webhook endpoints"""
        @self.app.route('/webhook/stripe', methods=['POST'])
        def handle_stripe_webhook():
            return self.process_stripe_webhook()
        
        @self.app.route('/webhook/health', methods=['GET'])
        def health_check():
            return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Stripe webhook signature for security"""
        try:
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            # Extract signature from header
            signature_elements = signature.split(',')
            signature_dict = {}
            
            for element in signature_elements:
                key, value = element.split('=')
                signature_dict[key] = value
            
            received_signature = signature_dict.get('v1')
            timestamp = int(signature_dict.get('t', 0))
            
            # Check timestamp to prevent replay attacks (5 minute tolerance)
            current_time = int(time.time())
            if abs(current_time - timestamp) > 300:
                logger.warning(f"Webhook timestamp too old: {timestamp}")
                return False
            
            return hmac.compare_digest(expected_signature, received_signature)
        
        except Exception as e:
            logger.error(f"Webhook signature verification failed: {str(e)}")
            return False
    
    def process_stripe_webhook(self):
        """Process incoming Stripe webhook"""
        try:
            payload = request.get_data()
            signature = request.headers.get('Stripe-Signature')
            
            if not signature:
                logger.warning("Missing Stripe signature header")
                return jsonify({"error": "Missing signature"}), 400
            
            # Verify webhook signature
            if not self.verify_webhook_signature(payload, signature):
                logger.warning("Invalid webhook signature")
                return jsonify({"error": "Invalid signature"}), 401
            
            # Parse event
            try:
                event = stripe.Event.construct_from(
                    json.loads(payload.decode('utf-8')),
                    stripe.api_key
                )
            except ValueError as e:
                logger.error(f"Invalid payload: {str(e)}")
                return jsonify({"error": "Invalid payload"}), 400
            
            # Process event
            success = self.handle_webhook_event(event)
            
            if success:
                return jsonify({"status": "success"}), 200
            else:
                return jsonify({"status": "error"}), 500
        
        except Exception as e:
            logger.error(f"Webhook processing failed: {str(e)}")
            return jsonify({"error": "Processing failed"}), 500
    
    def handle_webhook_event(self, event: stripe.Event) -> bool:
        """Handle specific webhook events"""
        try:
            event_type = event['type']
            data = event['data']
            
            logger.info(f"Processing webhook event: {event_type}")
            
            # Map event types to handlers
            event_handlers = {
                'checkout.session.completed': self.handle_checkout_completed,
                'payment_intent.succeeded': self.handle_payment_succeeded,
                'payment_intent.payment_failed': self.handle_payment_failed,
                'invoice.payment_succeeded': self.handle_subscription_payment_succeeded,
                'invoice.payment_failed': self.handle_subscription_payment_failed,
                'customer.subscription.created': self.handle_subscription_created,
                'customer.subscription.updated': self.handle_subscription_updated,
                'customer.subscription.deleted': self.handle_subscription_canceled,
                'customer.subscription.trial_will_end': self.handle_trial_ending,
                'payment_method.attached': self.handle_payment_method_attached,
                'setup_intent.succeeded': self.handle_setup_intent_succeeded,
            }
            
            handler = event_handlers.get(event_type)
            if handler:
                return handler(data['object'])
            else:
                logger.info(f"Unhandled event type: {event_type}")
                return True  # Return success for unhandled events
        
        except Exception as e:
            logger.error(f"Event handling failed: {str(e)}")
            return False
    
    def handle_checkout_completed(self, session) -> bool:
        """Handle successful checkout session completion"""
        try:
            session_id = session['id']
            customer_email = session.get('customer_details', {}).get('email')
            
            if not customer_email:
                customer_email = session.get('metadata', {}).get('customer_email')
            
            if not customer_email:
                logger.error(f"No customer email found for session {session_id}")
                return False
            
            # Process the successful payment
            payment_service.handle_successful_payment(session_id)
            
            # Send confirmation email (implement based on your email service)
            self.send_payment_confirmation_email(customer_email, session)
            
            logger.info(f"Checkout completed for {customer_email}: {session_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to handle checkout completion: {str(e)}")
            return False
    
    def handle_payment_succeeded(self, payment_intent) -> bool:
        """Handle successful payment intent"""
        try:
            pi_id = payment_intent['id']
            customer_id = payment_intent.get('customer')
            
            if customer_id:
                customer = stripe.Customer.retrieve(customer_id)
                customer_email = customer.email
                
                # Update payment record
                self.update_payment_status(pi_id, PaymentStatus.COMPLETED, customer_email)
                
                logger.info(f"Payment succeeded: {pi_id} for {customer_email}")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to handle payment success: {str(e)}")
            return False
    
    def handle_payment_failed(self, payment_intent) -> bool:
        """Handle failed payment intent"""
        try:
            pi_id = payment_intent['id']
            customer_id = payment_intent.get('customer')
            failure_reason = payment_intent.get('last_payment_error', {}).get('message', 'Unknown error')
            
            if customer_id:
                customer = stripe.Customer.retrieve(customer_id)
                customer_email = customer.email
                
                # Update payment record
                self.update_payment_status(pi_id, PaymentStatus.FAILED, customer_email, failure_reason)
                
                # Send failure notification
                self.send_payment_failure_email(customer_email, failure_reason)
                
                # Implement retry logic for recoverable failures
                self.schedule_payment_retry(pi_id, customer_email, failure_reason)
                
                logger.warning(f"Payment failed: {pi_id} for {customer_email} - {failure_reason}")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to handle payment failure: {str(e)}")
            return False
    
    def handle_subscription_payment_succeeded(self, invoice) -> bool:
        """Handle successful subscription payment"""
        try:
            subscription_id = invoice['subscription']
            customer_id = invoice['customer']
            amount_paid = invoice['amount_paid'] / 100  # Convert from cents
            
            customer = stripe.Customer.retrieve(customer_id)
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            customer_email = customer.email
            
            # Add monthly credits to user account
            tier_credits = self.get_tier_credits_from_subscription(subscription)
            if tier_credits:
                payment_service.add_monthly_credits(customer_email, tier_credits)
            
            # Record successful payment
            self.record_subscription_payment(customer_email, subscription_id, amount_paid, 'succeeded')
            
            # Send receipt
            self.send_subscription_receipt(customer_email, invoice)
            
            logger.info(f"Subscription payment succeeded: {subscription_id} for {customer_email}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to handle subscription payment success: {str(e)}")
            return False
    
    def handle_subscription_payment_failed(self, invoice) -> bool:
        """Handle failed subscription payment"""
        try:
            subscription_id = invoice['subscription']
            customer_id = invoice['customer']
            
            customer = stripe.Customer.retrieve(customer_id)
            customer_email = customer.email
            
            # Record failed payment
            self.record_subscription_payment(customer_email, subscription_id, 0, 'failed')
            
            # Send dunning email
            self.send_dunning_email(customer_email, invoice)
            
            # Implement grace period logic
            self.handle_subscription_grace_period(customer_email, subscription_id)
            
            logger.warning(f"Subscription payment failed: {subscription_id} for {customer_email}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to handle subscription payment failure: {str(e)}")
            return False
    
    def handle_subscription_created(self, subscription) -> bool:
        """Handle new subscription creation"""
        try:
            customer_id = subscription['customer']
            customer = stripe.Customer.retrieve(customer_id)
            customer_email = customer.email
            
            # Update user subscription status
            tier = self.get_tier_from_subscription(subscription)
            payment_service.update_user_subscription(customer_email, tier, subscription['id'])
            
            # Send welcome email
            self.send_subscription_welcome_email(customer_email, tier)
            
            logger.info(f"Subscription created: {subscription['id']} for {customer_email}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to handle subscription creation: {str(e)}")
            return False
    
    def handle_subscription_updated(self, subscription) -> bool:
        """Handle subscription updates (upgrades/downgrades)"""
        try:
            customer_id = subscription['customer']
            customer = stripe.Customer.retrieve(customer_id)
            customer_email = customer.email
            
            # Update user subscription
            tier = self.get_tier_from_subscription(subscription)
            payment_service.update_user_subscription(customer_email, tier, subscription['id'])
            
            # Send update confirmation
            self.send_subscription_update_email(customer_email, tier)
            
            logger.info(f"Subscription updated: {subscription['id']} for {customer_email}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to handle subscription update: {str(e)}")
            return False
    
    def handle_subscription_canceled(self, subscription) -> bool:
        """Handle subscription cancellation"""
        try:
            customer_id = subscription['customer']
            customer = stripe.Customer.retrieve(customer_id)
            customer_email = customer.email
            
            # Downgrade to free tier
            payment_service.update_user_subscription(customer_email, 'free', None)
            
            # Send cancellation confirmation
            self.send_subscription_cancellation_email(customer_email)
            
            logger.info(f"Subscription canceled: {subscription['id']} for {customer_email}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to handle subscription cancellation: {str(e)}")
            return False
    
    def handle_trial_ending(self, subscription) -> bool:
        """Handle trial period ending notification"""
        try:
            customer_id = subscription['customer']
            customer = stripe.Customer.retrieve(customer_id)
            customer_email = customer.email
            
            # Send trial ending notification
            self.send_trial_ending_email(customer_email, subscription)
            
            logger.info(f"Trial ending for: {customer_email}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to handle trial ending: {str(e)}")
            return False
    
    def handle_payment_method_attached(self, payment_method) -> bool:
        """Handle payment method attachment"""
        try:
            customer_id = payment_method['customer']
            
            if customer_id:
                customer = stripe.Customer.retrieve(customer_id)
                customer_email = customer.email
                
                # Update payment method on file
                self.update_customer_payment_method(customer_email, payment_method['id'])
                
                logger.info(f"Payment method attached for: {customer_email}")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to handle payment method attachment: {str(e)}")
            return False
    
    def handle_setup_intent_succeeded(self, setup_intent) -> bool:
        """Handle successful setup intent for future payments"""
        try:
            customer_id = setup_intent['customer']
            
            if customer_id:
                customer = stripe.Customer.retrieve(customer_id)
                customer_email = customer.email
                
                logger.info(f"Setup intent succeeded for: {customer_email}")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to handle setup intent success: {str(e)}")
            return False
    
    # Helper methods
    def update_payment_status(self, payment_intent_id: str, status: PaymentStatus, 
                            customer_email: str, failure_reason: str = None):
        """Update payment status in database"""
        # Implementation depends on your database structure
        pass
    
    def get_tier_from_subscription(self, subscription) -> str:
        """Extract tier from subscription metadata"""
        items = subscription.get('items', {}).get('data', [])
        if items:
            price_id = items[0].get('price', {}).get('id')
            # Map price IDs to tiers (implement based on your configuration)
            price_tier_mapping = {
                Config.STRIPE_STARTER_MONTHLY_PRICE_ID: 'starter',
                Config.STRIPE_STARTER_YEARLY_PRICE_ID: 'starter',
                Config.STRIPE_PRO_MONTHLY_PRICE_ID: 'pro',
                Config.STRIPE_PRO_YEARLY_PRICE_ID: 'pro',
                # Add more mappings
            }
            return price_tier_mapping.get(price_id, 'free')
        return 'free'
    
    def get_tier_credits_from_subscription(self, subscription) -> int:
        """Get monthly credits for subscription tier"""
        tier = self.get_tier_from_subscription(subscription)
        credit_mapping = {
            'starter': 30,
            'pro': 100,
            'enterprise': 500
        }
        return credit_mapping.get(tier, 0)
    
    def schedule_payment_retry(self, payment_intent_id: str, customer_email: str, failure_reason: str):
        """Schedule payment retry for recoverable failures"""
        recoverable_codes = ['card_declined', 'insufficient_funds', 'processing_error']
        
        # Check if failure is recoverable
        if any(code in failure_reason.lower() for code in recoverable_codes):
            # Implement retry logic (could use Celery, Redis, or similar)
            logger.info(f"Scheduling retry for {payment_intent_id}")
    
    # Email notification methods (implement based on your email service)
    def send_payment_confirmation_email(self, customer_email: str, session):
        """Send payment confirmation email"""
        logger.info(f"Sending payment confirmation to {customer_email}")
    
    def send_payment_failure_email(self, customer_email: str, failure_reason: str):
        """Send payment failure notification"""
        logger.info(f"Sending payment failure notification to {customer_email}")
    
    def send_subscription_receipt(self, customer_email: str, invoice):
        """Send subscription receipt"""
        logger.info(f"Sending subscription receipt to {customer_email}")
    
    def send_dunning_email(self, customer_email: str, invoice):
        """Send dunning email for failed subscription payment"""
        logger.info(f"Sending dunning email to {customer_email}")
    
    def send_subscription_welcome_email(self, customer_email: str, tier: str):
        """Send subscription welcome email"""
        logger.info(f"Sending welcome email to {customer_email} for {tier} tier")
    
    def send_subscription_update_email(self, customer_email: str, tier: str):
        """Send subscription update confirmation"""
        logger.info(f"Sending update confirmation to {customer_email} for {tier} tier")
    
    def send_subscription_cancellation_email(self, customer_email: str):
        """Send subscription cancellation confirmation"""
        logger.info(f"Sending cancellation confirmation to {customer_email}")
    
    def send_trial_ending_email(self, customer_email: str, subscription):
        """Send trial ending notification"""
        logger.info(f"Sending trial ending notification to {customer_email}")
    
    def update_customer_payment_method(self, customer_email: str, payment_method_id: str):
        """Update customer's default payment method"""
        logger.info(f"Updating payment method for {customer_email}")
    
    def handle_subscription_grace_period(self, customer_email: str, subscription_id: str):
        """Handle subscription grace period for failed payments"""
        logger.info(f"Handling grace period for {customer_email}")
        # Implement grace period logic (e.g., 3-day grace period)
    
    def record_subscription_payment(self, customer_email: str, subscription_id: str, 
                                  amount: float, status: str):
        """Record subscription payment in database"""
        logger.info(f"Recording subscription payment: {customer_email} - {status}")


# Global webhook service instance
webhook_service = WebhookService()

# Flask app for webhook endpoints
def create_webhook_app():
    """Create Flask app for webhook handling"""
    return webhook_service.app

if __name__ == "__main__":
    # Run webhook server
    app = create_webhook_app()
    app.run(host='0.0.0.0', port=5001, debug=False)