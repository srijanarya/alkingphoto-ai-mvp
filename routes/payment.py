"""
TalkingPhoto AI MVP - Payment Routes
Stripe integration with Indian payment methods and subscription management
"""

from flask import Blueprint, request, jsonify, current_app
from flask_restful import Api, Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, validate, ValidationError
from datetime import datetime, timezone, timedelta
import stripe
import structlog
from decimal import Decimal

from app import db, limiter
from models.user import User, SubscriptionTier
from models.subscription import Subscription, PaymentTransaction, SubscriptionStatus, PaymentStatus, PaymentMethod
from models.usage import UsageLog, ActionType
from services.payment_service import PaymentService
from services.email_service import EmailService
from utils.security import get_client_info

# Create blueprint and API
payment_bp = Blueprint('payment', __name__)
payment_api = Api(payment_bp)
logger = structlog.get_logger()

# Initialize Stripe
stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')

# Validation Schemas
class CreateSubscriptionSchema(Schema):
    """Subscription creation validation schema"""
    plan_name = fields.Str(required=True, validate=validate.OneOf(['starter', 'pro', 'enterprise']))
    billing_cycle = fields.Str(required=False, default='monthly', validate=validate.OneOf(['monthly', 'yearly']))
    payment_method_id = fields.Str(required=False)  # Stripe payment method ID
    coupon_code = fields.Str(required=False)


class UpdatePaymentMethodSchema(Schema):
    """Payment method update validation schema"""
    payment_method_id = fields.Str(required=True)


class CreatePaymentIntentSchema(Schema):
    """Payment intent creation validation schema"""
    amount = fields.Float(required=True, validate=validate.Range(min=1))
    currency = fields.Str(required=False, default='inr', validate=validate.OneOf(['inr', 'usd']))
    description = fields.Str(required=False)
    subscription_id = fields.Str(required=False)


# Payment Resources
class PricingPlansResource(Resource):
    """Get available pricing plans"""
    
    def get(self):
        """Get current pricing plans and features"""
        try:
            plans = {
                'free': {
                    'name': 'Free',
                    'price_monthly': 0,
                    'price_yearly': 0,
                    'video_generation_limit': 3,
                    'features': [
                        'Basic video generation',
                        'Watermarked output',
                        'Standard quality',
                        'Export instructions'
                    ],
                    'currency': 'INR'
                },
                'starter': {
                    'name': 'Starter',
                    'price_monthly': 999,
                    'price_yearly': 9990,  # 2 months free
                    'video_generation_limit': 30,
                    'features': [
                        'HD video generation',
                        'No watermark',
                        'Standard & premium quality',
                        'All export instructions',
                        'Email support'
                    ],
                    'currency': 'INR',
                    'stripe_price_id_monthly': 'price_starter_monthly_inr',
                    'stripe_price_id_yearly': 'price_starter_yearly_inr'
                },
                'pro': {
                    'name': 'Pro',
                    'price_monthly': 2999,
                    'price_yearly': 29990,  # 2 months free
                    'video_generation_limit': 100,
                    'features': [
                        'All Starter features',
                        'Priority processing',
                        'Analytics dashboard',
                        'Bulk generation',
                        'API access (coming soon)',
                        'Priority support'
                    ],
                    'currency': 'INR',
                    'stripe_price_id_monthly': 'price_pro_monthly_inr',
                    'stripe_price_id_yearly': 'price_pro_yearly_inr'
                },
                'enterprise': {
                    'name': 'Enterprise',
                    'price_monthly': 'Custom',
                    'price_yearly': 'Custom',
                    'video_generation_limit': -1,  # Unlimited
                    'features': [
                        'All Pro features',
                        'Unlimited generations',
                        'White-label solution',
                        'Custom integrations',
                        'Dedicated support',
                        'SLA guarantee'
                    ],
                    'currency': 'INR',
                    'contact_required': True
                }
            }
            
            return {
                'plans': plans,
                'currency': 'INR',
                'tax_info': 'Prices include applicable taxes',
                'payment_methods': ['card', 'upi', 'netbanking', 'wallet']
            }, 200
            
        except Exception as e:
            logger.error("Pricing plans retrieval failed", error=str(e))
            return {'error': 'Failed to retrieve pricing plans'}, 500


class CreateSubscriptionResource(Resource):
    """Create new subscription"""
    
    decorators = [jwt_required(), limiter.limit("3 per hour")]
    
    def post(self):
        """Create new subscription with Stripe"""
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return {'error': 'User not found'}, 404
            
            # Check if user already has active subscription
            active_subscription = Subscription.query.filter_by(
                user_id=current_user_id,
                status=SubscriptionStatus.ACTIVE
            ).first()
            
            if active_subscription:
                return {
                    'error': 'Active subscription exists',
                    'message': 'Please cancel current subscription before creating a new one',
                    'current_subscription': active_subscription.to_dict()
                }, 409
            
            # Validate request data
            schema = CreateSubscriptionSchema()
            data = schema.load(request.get_json() or {})
            
            # Get client information
            client_info = get_client_info(request)
            
            # Initialize payment service
            payment_service = PaymentService()
            
            # Create subscription
            result = payment_service.create_subscription(
                user=user,
                plan_name=data['plan_name'],
                billing_cycle=data['billing_cycle'],
                payment_method_id=data.get('payment_method_id'),
                coupon_code=data.get('coupon_code'),
                client_info=client_info
            )
            
            if not result['success']:
                return {
                    'error': 'Subscription creation failed',
                    'message': result['error']
                }, 400
            
            subscription = result['subscription']
            
            # Update user subscription tier
            tier_mapping = {
                'starter': SubscriptionTier.STARTER,
                'pro': SubscriptionTier.PRO,
                'enterprise': SubscriptionTier.ENTERPRISE
            }
            user.subscription_tier = tier_mapping[data['plan_name']]
            
            db.session.commit()
            
            # Log subscription creation
            UsageLog.log_action(
                user_id=current_user_id,
                action_type=ActionType.SUBSCRIPTION_UPGRADE,
                resource_id=subscription.id,
                resource_type='subscription',
                success=True,
                metadata={
                    'plan_name': data['plan_name'],
                    'billing_cycle': data['billing_cycle']
                },
                ip_address=client_info['ip_address'],
                user_agent=client_info['user_agent']
            )
            
            logger.info("Subscription created", 
                       user_id=current_user_id,
                       subscription_id=subscription.id,
                       plan_name=data['plan_name'])
            
            response_data = {
                'message': 'Subscription created successfully',
                'subscription': subscription.to_dict(),
                'user': user.to_dict()
            }
            
            # Include client secret for payment confirmation if required
            if result.get('requires_payment_confirmation'):
                response_data['client_secret'] = result['client_secret']
                response_data['requires_confirmation'] = True
            
            return response_data, 201
            
        except ValidationError as e:
            return {'error': 'Validation failed', 'details': e.messages}, 400
        except Exception as e:
            logger.error("Subscription creation failed", error=str(e))
            return {'error': 'Subscription creation failed', 'message': 'Internal server error'}, 500


class SubscriptionDetailsResource(Resource):
    """Get subscription details"""
    
    decorators = [jwt_required()]
    
    def get(self):
        """Get current subscription details"""
        try:
            current_user_id = get_jwt_identity()
            
            subscription = Subscription.query.filter_by(
                user_id=current_user_id
            ).order_by(Subscription.created_at.desc()).first()
            
            if not subscription:
                return {
                    'message': 'No subscription found',
                    'subscription': None
                }, 200
            
            return {
                'subscription': subscription.to_dict(include_sensitive=False)
            }, 200
            
        except Exception as e:
            logger.error("Subscription details retrieval failed", error=str(e))
            return {'error': 'Failed to retrieve subscription details'}, 500


class UpdateSubscriptionResource(Resource):
    """Update subscription"""
    
    decorators = [jwt_required()]
    
    def put(self):
        """Update subscription plan or billing cycle"""
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return {'error': 'User not found'}, 404
            
            subscription = Subscription.query.filter_by(
                user_id=current_user_id,
                status=SubscriptionStatus.ACTIVE
            ).first()
            
            if not subscription:
                return {'error': 'No active subscription found'}, 404
            
            # Validate request data
            data = request.get_json() or {}
            
            if 'plan_name' in data:
                # Handle plan change
                payment_service = PaymentService()
                result = payment_service.change_subscription_plan(
                    subscription=subscription,
                    new_plan=data['plan_name']
                )
                
                if not result['success']:
                    return {
                        'error': 'Plan change failed',
                        'message': result['error']
                    }, 400
                
                # Update user tier
                tier_mapping = {
                    'starter': SubscriptionTier.STARTER,
                    'pro': SubscriptionTier.PRO,
                    'enterprise': SubscriptionTier.ENTERPRISE
                }
                user.subscription_tier = tier_mapping[data['plan_name']]
                
                logger.info("Subscription plan changed", 
                           user_id=current_user_id,
                           old_plan=subscription.plan_name,
                           new_plan=data['plan_name'])
            
            db.session.commit()
            
            return {
                'message': 'Subscription updated successfully',
                'subscription': subscription.to_dict()
            }, 200
            
        except Exception as e:
            logger.error("Subscription update failed", error=str(e))
            return {'error': 'Subscription update failed'}, 500


class CancelSubscriptionResource(Resource):
    """Cancel subscription"""
    
    decorators = [jwt_required()]
    
    def post(self):
        """Cancel current subscription"""
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return {'error': 'User not found'}, 404
            
            subscription = Subscription.query.filter_by(
                user_id=current_user_id,
                status=SubscriptionStatus.ACTIVE
            ).first()
            
            if not subscription:
                return {'error': 'No active subscription found'}, 404
            
            # Get cancellation options
            data = request.get_json() or {}
            cancel_immediately = data.get('cancel_immediately', False)
            cancellation_reason = data.get('reason', '')
            
            # Initialize payment service
            payment_service = PaymentService()
            
            if cancel_immediately:
                result = payment_service.cancel_subscription_immediately(subscription)
                user.subscription_tier = SubscriptionTier.FREE
                message = 'Subscription cancelled immediately'
            else:
                result = payment_service.schedule_subscription_cancellation(subscription)
                message = 'Subscription will be cancelled at the end of the current billing period'
            
            if not result['success']:
                return {
                    'error': 'Cancellation failed',
                    'message': result['error']
                }, 400
            
            db.session.commit()
            
            # Send cancellation email
            try:
                email_service = EmailService()
                email_service.send_subscription_cancelled_email(
                    user.email, 
                    subscription,
                    cancel_immediately
                )
            except Exception as e:
                logger.error("Failed to send cancellation email", error=str(e))
            
            # Log cancellation
            action_type = ActionType.SUBSCRIPTION_DOWNGRADE
            UsageLog.log_action(
                user_id=current_user_id,
                action_type=action_type,
                resource_id=subscription.id,
                resource_type='subscription',
                success=True,
                metadata={
                    'cancellation_reason': cancellation_reason,
                    'cancel_immediately': cancel_immediately
                }
            )
            
            logger.info("Subscription cancelled", 
                       user_id=current_user_id,
                       subscription_id=subscription.id,
                       immediately=cancel_immediately)
            
            return {
                'message': message,
                'subscription': subscription.to_dict(),
                'effective_date': subscription.ended_at.isoformat() if subscription.ended_at else subscription.current_period_end.isoformat()
            }, 200
            
        except Exception as e:
            logger.error("Subscription cancellation failed", error=str(e))
            return {'error': 'Cancellation failed'}, 500


class PaymentHistoryResource(Resource):
    """Get payment history"""
    
    decorators = [jwt_required()]
    
    def get(self):
        """Get paginated payment history"""
        try:
            current_user_id = get_jwt_identity()
            
            # Get pagination parameters
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 20, type=int), 100)
            
            # Query payment transactions
            payments = PaymentTransaction.query.filter_by(
                user_id=current_user_id
            ).order_by(PaymentTransaction.created_at.desc()).paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            payment_history = [payment.to_dict() for payment in payments.items]
            
            return {
                'payments': payment_history,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': payments.total,
                    'pages': payments.pages,
                    'has_prev': payments.has_prev,
                    'has_next': payments.has_next
                }
            }, 200
            
        except Exception as e:
            logger.error("Payment history retrieval failed", error=str(e))
            return {'error': 'Failed to retrieve payment history'}, 500


class InvoicesResource(Resource):
    """Get invoices"""
    
    decorators = [jwt_required()]
    
    def get(self):
        """Get user invoices"""
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return {'error': 'User not found'}, 404
            
            # Get subscription to find Stripe customer
            subscription = Subscription.query.filter_by(
                user_id=current_user_id
            ).first()
            
            if not subscription or not subscription.stripe_customer_id:
                return {
                    'invoices': [],
                    'total_count': 0
                }, 200
            
            # Get invoices from Stripe
            try:
                stripe_invoices = stripe.Invoice.list(
                    customer=subscription.stripe_customer_id,
                    limit=20
                )
                
                invoices = []
                for invoice in stripe_invoices.data:
                    invoices.append({
                        'id': invoice.id,
                        'number': invoice.number,
                        'amount': invoice.total / 100,  # Convert from cents
                        'currency': invoice.currency.upper(),
                        'status': invoice.status,
                        'created': datetime.fromtimestamp(invoice.created).isoformat(),
                        'due_date': datetime.fromtimestamp(invoice.due_date).isoformat() if invoice.due_date else None,
                        'pdf_url': invoice.invoice_pdf,
                        'hosted_url': invoice.hosted_invoice_url
                    })
                
                return {
                    'invoices': invoices,
                    'total_count': len(invoices)
                }, 200
                
            except stripe.error.StripeError as e:
                logger.error("Stripe invoice retrieval failed", error=str(e))
                return {'error': 'Failed to retrieve invoices from payment provider'}, 500
            
        except Exception as e:
            logger.error("Invoice retrieval failed", error=str(e))
            return {'error': 'Failed to retrieve invoices'}, 500


class StripeWebhookResource(Resource):
    """Handle Stripe webhooks"""
    
    def post(self):
        """Handle Stripe webhook events"""
        try:
            payload = request.get_data()
            sig_header = request.headers.get('stripe-signature')
            
            if not sig_header:
                return {'error': 'Missing signature'}, 400
            
            try:
                event = stripe.Webhook.construct_event(
                    payload,
                    sig_header,
                    current_app.config['STRIPE_WEBHOOK_SECRET']
                )
            except ValueError:
                return {'error': 'Invalid payload'}, 400
            except stripe.error.SignatureVerificationError:
                return {'error': 'Invalid signature'}, 400
            
            # Handle different event types
            payment_service = PaymentService()
            
            if event['type'] == 'payment_intent.succeeded':
                payment_service.handle_payment_success(event['data']['object'])
            elif event['type'] == 'payment_intent.payment_failed':
                payment_service.handle_payment_failure(event['data']['object'])
            elif event['type'] == 'invoice.payment_succeeded':
                payment_service.handle_invoice_payment_success(event['data']['object'])
            elif event['type'] == 'invoice.payment_failed':
                payment_service.handle_invoice_payment_failure(event['data']['object'])
            elif event['type'] == 'customer.subscription.updated':
                payment_service.handle_subscription_update(event['data']['object'])
            elif event['type'] == 'customer.subscription.deleted':
                payment_service.handle_subscription_cancellation(event['data']['object'])
            
            logger.info("Stripe webhook processed", event_type=event['type'])
            
            return {'received': True}, 200
            
        except Exception as e:
            logger.error("Webhook processing failed", error=str(e))
            return {'error': 'Webhook processing failed'}, 500


# Register API resources
payment_api.add_resource(PricingPlansResource, '/plans')
payment_api.add_resource(CreateSubscriptionResource, '/subscription')
payment_api.add_resource(SubscriptionDetailsResource, '/subscription/details')
payment_api.add_resource(UpdateSubscriptionResource, '/subscription/update')
payment_api.add_resource(CancelSubscriptionResource, '/subscription/cancel')
payment_api.add_resource(PaymentHistoryResource, '/history')
payment_api.add_resource(InvoicesResource, '/invoices')
payment_api.add_resource(StripeWebhookResource, '/webhook/stripe')