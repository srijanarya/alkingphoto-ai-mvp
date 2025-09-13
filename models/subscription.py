"""
TalkingPhoto AI MVP - Subscription and Payment Models
Stripe integration with comprehensive billing tracking
"""

from datetime import datetime, timezone, timedelta
from flask_sqlalchemy import SQLAlchemy
import uuid
from enum import Enum
from decimal import Decimal
from app import db


class SubscriptionStatus(Enum):
    """Subscription status enumeration"""
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    CANCELLED = 'cancelled'
    PAST_DUE = 'past_due'
    UNPAID = 'unpaid'
    TRIALING = 'trialing'


class PaymentStatus(Enum):
    """Payment transaction status enumeration"""
    PENDING = 'pending'
    PROCESSING = 'processing'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    REFUNDED = 'refunded'
    PARTIALLY_REFUNDED = 'partially_refunded'


class PaymentMethod(Enum):
    """Payment method enumeration"""
    CARD = 'card'
    UPI = 'upi'
    NETBANKING = 'netbanking'
    WALLET = 'wallet'


class Subscription(db.Model):
    """
    User subscription management with Stripe integration
    """
    __tablename__ = 'subscriptions'

    # Primary identification
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Stripe integration
    stripe_subscription_id = db.Column(db.String(255), unique=True, nullable=True, index=True)
    stripe_customer_id = db.Column(db.String(255), nullable=True, index=True)
    stripe_price_id = db.Column(db.String(255), nullable=True)
    
    # Subscription details
    plan_name = db.Column(db.String(50), nullable=False)  # free, starter, pro, enterprise
    status = db.Column(db.Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE, nullable=False)
    
    # Pricing information
    amount = db.Column(db.Numeric(10, 2), nullable=False)  # INR
    currency = db.Column(db.String(3), default='INR', nullable=False)
    billing_cycle = db.Column(db.String(20), default='monthly', nullable=False)  # monthly, yearly
    
    # Usage limits
    video_generation_limit = db.Column(db.Integer, nullable=False)
    current_usage = db.Column(db.Integer, default=0, nullable=False)
    
    # Subscription lifecycle
    trial_start = db.Column(db.DateTime, nullable=True)
    trial_end = db.Column(db.DateTime, nullable=True)
    current_period_start = db.Column(db.DateTime, nullable=False)
    current_period_end = db.Column(db.DateTime, nullable=False)
    cancel_at_period_end = db.Column(db.Boolean, default=False, nullable=False)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    ended_at = db.Column(db.DateTime, nullable=True)
    
    # Billing information
    next_billing_date = db.Column(db.DateTime, nullable=True)
    last_payment_date = db.Column(db.DateTime, nullable=True)
    failed_payment_count = db.Column(db.Integer, default=0, nullable=False)
    
    # Discounts and promotions
    discount_percentage = db.Column(db.Float, nullable=True)
    coupon_code = db.Column(db.String(50), nullable=True)
    promotional_credits = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    payment_transactions = db.relationship('PaymentTransaction', backref='subscription', lazy='dynamic', cascade='all, delete-orphan')

    def __init__(self, user_id, plan_name, amount, video_generation_limit, **kwargs):
        """Initialize subscription with plan details"""
        self.user_id = user_id
        self.plan_name = plan_name
        self.amount = Decimal(str(amount))
        self.video_generation_limit = video_generation_limit
        
        # Set billing period
        self.current_period_start = datetime.now(timezone.utc)
        self.current_period_end = self.current_period_start + timedelta(days=30)
        self.next_billing_date = self.current_period_end
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def is_active(self):
        """Check if subscription is currently active"""
        return (
            self.status == SubscriptionStatus.ACTIVE and
            datetime.now(timezone.utc) <= self.current_period_end
        )

    def is_trial(self):
        """Check if subscription is in trial period"""
        return (
            self.status == SubscriptionStatus.TRIALING and
            self.trial_end and
            datetime.now(timezone.utc) <= self.trial_end
        )

    def has_usage_remaining(self):
        """Check if user has video generation usage remaining"""
        if self.video_generation_limit == -1:  # Unlimited
            return True
        return self.current_usage < self.video_generation_limit

    def get_usage_percentage(self):
        """Get usage percentage"""
        if self.video_generation_limit == -1:  # Unlimited
            return 0
        return (self.current_usage / self.video_generation_limit) * 100

    def increment_usage(self):
        """Increment current usage count"""
        self.current_usage += 1

    def reset_usage(self):
        """Reset usage counter (called at billing cycle)"""
        self.current_usage = 0

    def apply_discount(self, percentage, coupon_code=None):
        """Apply discount to subscription"""
        self.discount_percentage = percentage
        self.coupon_code = coupon_code

    def add_promotional_credits(self, amount):
        """Add promotional credits"""
        self.promotional_credits += Decimal(str(amount))

    def deduct_promotional_credits(self, amount):
        """Deduct promotional credits"""
        amount = Decimal(str(amount))
        if self.promotional_credits >= amount:
            self.promotional_credits -= amount
            return amount
        else:
            available = self.promotional_credits
            self.promotional_credits = 0
            return available

    def get_effective_amount(self):
        """Get effective amount after discount"""
        if self.discount_percentage:
            return self.amount * (1 - self.discount_percentage / 100)
        return self.amount

    def schedule_cancellation(self):
        """Schedule cancellation at period end"""
        self.cancel_at_period_end = True
        self.cancelled_at = datetime.now(timezone.utc)

    def cancel_immediately(self):
        """Cancel subscription immediately"""
        self.status = SubscriptionStatus.CANCELLED
        self.cancelled_at = datetime.now(timezone.utc)
        self.ended_at = datetime.now(timezone.utc)

    def renew_period(self):
        """Renew subscription for next billing period"""
        if self.billing_cycle == 'yearly':
            self.current_period_start = self.current_period_end
            self.current_period_end = self.current_period_start + timedelta(days=365)
        else:  # monthly
            self.current_period_start = self.current_period_end
            self.current_period_end = self.current_period_start + timedelta(days=30)
        
        self.next_billing_date = self.current_period_end
        self.reset_usage()

    def mark_payment_failed(self):
        """Mark payment as failed and update counters"""
        self.failed_payment_count += 1
        if self.failed_payment_count >= 3:
            self.status = SubscriptionStatus.UNPAID

    def mark_payment_succeeded(self):
        """Mark payment as succeeded and reset counters"""
        self.failed_payment_count = 0
        self.last_payment_date = datetime.now(timezone.utc)
        if self.status in [SubscriptionStatus.PAST_DUE, SubscriptionStatus.UNPAID]:
            self.status = SubscriptionStatus.ACTIVE

    def to_dict(self, include_sensitive=False):
        """Convert subscription to dictionary for API responses"""
        data = {
            'id': self.id,
            'plan_name': self.plan_name,
            'status': self.status.value,
            'amount': float(self.amount),
            'currency': self.currency,
            'billing_cycle': self.billing_cycle,
            'video_generation_limit': self.video_generation_limit,
            'current_usage': self.current_usage,
            'usage_percentage': self.get_usage_percentage(),
            'effective_amount': float(self.get_effective_amount()),
            'discount_percentage': self.discount_percentage,
            'promotional_credits': float(self.promotional_credits),
            'current_period_start': self.current_period_start.isoformat(),
            'current_period_end': self.current_period_end.isoformat(),
            'next_billing_date': self.next_billing_date.isoformat() if self.next_billing_date else None,
            'cancel_at_period_end': self.cancel_at_period_end,
            'is_active': self.is_active(),
            'is_trial': self.is_trial(),
            'has_usage_remaining': self.has_usage_remaining(),
            'created_at': self.created_at.isoformat()
        }
        
        if include_sensitive:
            data.update({
                'stripe_subscription_id': self.stripe_subscription_id,
                'stripe_customer_id': self.stripe_customer_id,
                'failed_payment_count': self.failed_payment_count
            })
        
        return data

    def __repr__(self):
        return f'<Subscription {self.plan_name} for User {self.user_id}>'


class PaymentTransaction(db.Model):
    """
    Payment transaction tracking with Stripe integration
    """
    __tablename__ = 'payment_transactions'

    # Primary identification
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    subscription_id = db.Column(db.String(36), db.ForeignKey('subscriptions.id'), nullable=True)
    
    # Stripe integration
    stripe_payment_intent_id = db.Column(db.String(255), unique=True, nullable=True, index=True)
    stripe_charge_id = db.Column(db.String(255), nullable=True)
    stripe_invoice_id = db.Column(db.String(255), nullable=True)
    
    # Transaction details
    amount = db.Column(db.Numeric(10, 2), nullable=False)  # INR
    currency = db.Column(db.String(3), default='INR', nullable=False)
    description = db.Column(db.String(255), nullable=True)
    
    # Payment information
    payment_method = db.Column(db.Enum(PaymentMethod), nullable=True)
    payment_method_details = db.Column(db.JSON, nullable=True)  # Last 4 digits, UPI ID, etc.
    
    # Transaction status
    status = db.Column(db.Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    failure_reason = db.Column(db.String(255), nullable=True)
    failure_code = db.Column(db.String(50), nullable=True)
    
    # Processing information
    processing_fee = db.Column(db.Numeric(10, 2), nullable=True)  # Stripe fees
    net_amount = db.Column(db.Numeric(10, 2), nullable=True)  # Amount after fees
    
    # Refund information
    refunded_amount = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    refund_reason = db.Column(db.String(255), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    processed_at = db.Column(db.DateTime, nullable=True)
    failed_at = db.Column(db.DateTime, nullable=True)
    refunded_at = db.Column(db.DateTime, nullable=True)
    
    # Metadata
    metadata = db.Column(db.JSON, nullable=True)
    stripe_response = db.Column(db.JSON, nullable=True)

    def __init__(self, user_id, amount, **kwargs):
        """Initialize payment transaction"""
        self.user_id = user_id
        self.amount = Decimal(str(amount))
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def mark_processing(self):
        """Mark transaction as processing"""
        self.status = PaymentStatus.PROCESSING

    def mark_succeeded(self, processing_fee=None):
        """Mark transaction as succeeded"""
        self.status = PaymentStatus.SUCCEEDED
        self.processed_at = datetime.now(timezone.utc)
        
        if processing_fee:
            self.processing_fee = Decimal(str(processing_fee))
            self.net_amount = self.amount - self.processing_fee
        else:
            self.net_amount = self.amount

    def mark_failed(self, failure_reason, failure_code=None):
        """Mark transaction as failed"""
        self.status = PaymentStatus.FAILED
        self.failed_at = datetime.now(timezone.utc)
        self.failure_reason = failure_reason
        self.failure_code = failure_code

    def process_refund(self, amount=None, reason=None):
        """Process refund for transaction"""
        refund_amount = Decimal(str(amount)) if amount else self.amount
        
        if refund_amount > (self.amount - self.refunded_amount):
            raise ValueError("Refund amount exceeds available amount")
        
        self.refunded_amount += refund_amount
        self.refunded_at = datetime.now(timezone.utc)
        
        if reason:
            self.refund_reason = reason
        
        if self.refunded_amount >= self.amount:
            self.status = PaymentStatus.REFUNDED
        else:
            self.status = PaymentStatus.PARTIALLY_REFUNDED

    def is_successful(self):
        """Check if transaction was successful"""
        return self.status == PaymentStatus.SUCCEEDED

    def is_failed(self):
        """Check if transaction failed"""
        return self.status == PaymentStatus.FAILED

    def can_be_refunded(self):
        """Check if transaction can be refunded"""
        return (
            self.status == PaymentStatus.SUCCEEDED and
            self.refunded_amount < self.amount
        )

    def get_refundable_amount(self):
        """Get remaining refundable amount"""
        return self.amount - self.refunded_amount

    def to_dict(self, include_sensitive=False):
        """Convert transaction to dictionary for API responses"""
        data = {
            'id': self.id,
            'amount': float(self.amount),
            'currency': self.currency,
            'description': self.description,
            'status': self.status.value,
            'payment_method': self.payment_method.value if self.payment_method else None,
            'net_amount': float(self.net_amount) if self.net_amount else None,
            'refunded_amount': float(self.refunded_amount),
            'created_at': self.created_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }
        
        if self.status == PaymentStatus.FAILED:
            data.update({
                'failure_reason': self.failure_reason,
                'failed_at': self.failed_at.isoformat() if self.failed_at else None
            })
        
        if include_sensitive:
            data.update({
                'stripe_payment_intent_id': self.stripe_payment_intent_id,
                'processing_fee': float(self.processing_fee) if self.processing_fee else None,
                'payment_method_details': self.payment_method_details,
                'metadata': self.metadata
            })
        
        return data

    def __repr__(self):
        return f'<PaymentTransaction {self.id} ({self.status.value})>'