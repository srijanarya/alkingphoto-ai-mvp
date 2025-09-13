"""
TalkingPhoto AI MVP - Stripe Payment Service
Comprehensive payment processing for Streamlit environment
"""

import stripe
import os
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import streamlit as st
import sqlite3
import json
import hashlib
import hmac
import requests
from config import Config

# Configure Stripe
stripe.api_key = Config.STRIPE_SECRET_KEY

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SubscriptionTier(Enum):
    """Subscription tier definitions"""
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class PaymentStatus(Enum):
    """Payment status definitions"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"
    REFUNDED = "refunded"


@dataclass
class PricingPlan:
    """Pricing plan configuration"""
    tier: SubscriptionTier
    name: str
    price_monthly: float
    price_yearly: float
    credits_monthly: int
    features: List[str]
    stripe_price_id_monthly: str
    stripe_price_id_yearly: str
    currency: str = "usd"


class PaymentService:
    """
    Comprehensive payment service for TalkingPhoto MVP
    Handles subscriptions, one-time payments, and credit purchases
    """
    
    def __init__(self):
        self.db_path = "data/payments.db"
        self.webhook_secret = Config.STRIPE_WEBHOOK_SECRET
        self.init_database()
        self.pricing_plans = self._load_pricing_plans()
    
    def init_database(self):
        """Initialize SQLite database for payment tracking"""
        os.makedirs("data", exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    stripe_customer_id TEXT UNIQUE,
                    subscription_tier TEXT DEFAULT 'free',
                    credits INTEGER DEFAULT 3,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Payments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    stripe_payment_intent_id TEXT,
                    stripe_subscription_id TEXT,
                    amount REAL,
                    currency TEXT DEFAULT 'usd',
                    status TEXT,
                    payment_type TEXT, -- 'subscription', 'credits', 'one_time'
                    credits_purchased INTEGER DEFAULT 0,
                    metadata TEXT, -- JSON string
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Subscription history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS subscription_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    stripe_subscription_id TEXT,
                    tier TEXT,
                    status TEXT,
                    current_period_start TIMESTAMP,
                    current_period_end TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Credit transactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS credit_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    transaction_type TEXT, -- 'purchase', 'usage', 'refund', 'bonus'
                    credits INTEGER,
                    description TEXT,
                    payment_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (payment_id) REFERENCES payments (id)
                )
            """)
            
            conn.commit()
    
    def _load_pricing_plans(self) -> Dict[SubscriptionTier, PricingPlan]:
        """Load pricing plans configuration"""
        return {
            SubscriptionTier.FREE: PricingPlan(
                tier=SubscriptionTier.FREE,
                name="Free",
                price_monthly=0.0,
                price_yearly=0.0,
                credits_monthly=3,
                features=[
                    "3 video generations per month",
                    "720p quality",
                    "Basic voice options",
                    "Community support"
                ],
                stripe_price_id_monthly="",
                stripe_price_id_yearly=""
            ),
            SubscriptionTier.STARTER: PricingPlan(
                tier=SubscriptionTier.STARTER,
                name="Starter",
                price_monthly=19.99,
                price_yearly=199.99,
                credits_monthly=30,
                features=[
                    "30 video generations per month",
                    "1080p HD quality",
                    "Premium voice options",
                    "Priority support",
                    "Commercial usage rights"
                ],
                stripe_price_id_monthly=os.getenv('STRIPE_STARTER_MONTHLY_PRICE_ID'),
                stripe_price_id_yearly=os.getenv('STRIPE_STARTER_YEARLY_PRICE_ID')
            ),
            SubscriptionTier.PRO: PricingPlan(
                tier=SubscriptionTier.PRO,
                name="Pro",
                price_monthly=49.99,
                price_yearly=499.99,
                credits_monthly=100,
                features=[
                    "100 video generations per month",
                    "4K ultra-HD quality",
                    "All voice options + voice cloning",
                    "Priority support",
                    "Commercial usage rights",
                    "Custom branding",
                    "API access"
                ],
                stripe_price_id_monthly=os.getenv('STRIPE_PRO_MONTHLY_PRICE_ID'),
                stripe_price_id_yearly=os.getenv('STRIPE_PRO_YEARLY_PRICE_ID')
            ),
            SubscriptionTier.ENTERPRISE: PricingPlan(
                tier=SubscriptionTier.ENTERPRISE,
                name="Enterprise",
                price_monthly=199.99,
                price_yearly=1999.99,
                credits_monthly=500,
                features=[
                    "500 video generations per month",
                    "4K ultra-HD quality",
                    "All premium features",
                    "Dedicated support",
                    "White-label solution",
                    "Custom integrations",
                    "SLA guarantee"
                ],
                stripe_price_id_monthly=os.getenv('STRIPE_ENTERPRISE_MONTHLY_PRICE_ID'),
                stripe_price_id_yearly=os.getenv('STRIPE_ENTERPRISE_YEARLY_PRICE_ID')
            )
        }
    
    def create_customer(self, email: str, name: str = None) -> str:
        """Create a new Stripe customer"""
        try:
            customer_data = {"email": email}
            if name:
                customer_data["name"] = name
            
            customer = stripe.Customer.create(**customer_data)
            
            # Store in local database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO users (email, stripe_customer_id)
                    VALUES (?, ?)
                """, (email, customer.id))
                conn.commit()
            
            logger.info(f"Created customer {customer.id} for {email}")
            return customer.id
        
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create customer: {str(e)}")
            raise
    
    def get_or_create_customer(self, email: str, name: str = None) -> str:
        """Get existing customer or create new one"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT stripe_customer_id FROM users WHERE email = ?", (email,))
            result = cursor.fetchone()
            
            if result and result[0]:
                return result[0]
            else:
                return self.create_customer(email, name)
    
    def create_subscription_checkout(
        self, 
        customer_email: str, 
        tier: SubscriptionTier, 
        billing_cycle: str = "monthly",
        success_url: str = None,
        cancel_url: str = None
    ) -> str:
        """Create Stripe checkout session for subscription"""
        try:
            customer_id = self.get_or_create_customer(customer_email)
            plan = self.pricing_plans[tier]
            
            price_id = (plan.stripe_price_id_monthly if billing_cycle == "monthly" 
                       else plan.stripe_price_id_yearly)
            
            if not price_id:
                raise ValueError(f"Price ID not configured for {tier.value} {billing_cycle}")
            
            checkout_session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url or 'https://your-domain.com/success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=cancel_url or 'https://your-domain.com/cancel',
                metadata={
                    'tier': tier.value,
                    'billing_cycle': billing_cycle,
                    'customer_email': customer_email
                }
            )
            
            logger.info(f"Created subscription checkout for {customer_email}: {checkout_session.id}")
            return checkout_session.url
        
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create subscription checkout: {str(e)}")
            raise
    
    def create_credits_checkout(
        self, 
        customer_email: str, 
        credits_amount: int,
        price_per_credit: float = 0.99,
        success_url: str = None,
        cancel_url: str = None
    ) -> str:
        """Create Stripe checkout session for credit purchase"""
        try:
            customer_id = self.get_or_create_customer(customer_email)
            total_amount = int(credits_amount * price_per_credit * 100)  # Convert to cents
            
            checkout_session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f'{credits_amount} TalkingPhoto Credits',
                            'description': f'Purchase {credits_amount} video generation credits'
                        },
                        'unit_amount': total_amount,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=success_url or 'https://your-domain.com/success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=cancel_url or 'https://your-domain.com/cancel',
                metadata={
                    'payment_type': 'credits',
                    'credits_amount': str(credits_amount),
                    'customer_email': customer_email
                }
            )
            
            logger.info(f"Created credits checkout for {customer_email}: {checkout_session.id}")
            return checkout_session.url
        
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create credits checkout: {str(e)}")
            raise
    
    def handle_successful_payment(self, session_id: str):
        """Handle successful payment completion"""
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            customer_email = session.metadata.get('customer_email')
            
            if session.mode == 'subscription':
                self._handle_subscription_success(session, customer_email)
            elif session.metadata.get('payment_type') == 'credits':
                self._handle_credits_success(session, customer_email)
            
            logger.info(f"Successfully processed payment for session {session_id}")
        
        except stripe.error.StripeError as e:
            logger.error(f"Failed to handle successful payment: {str(e)}")
            raise
    
    def _handle_subscription_success(self, session, customer_email: str):
        """Handle successful subscription payment"""
        subscription = stripe.Subscription.retrieve(session.subscription)
        tier = SubscriptionTier(session.metadata.get('tier'))
        plan = self.pricing_plans[tier]
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Update user subscription
            cursor.execute("""
                UPDATE users 
                SET subscription_tier = ?, credits = credits + ?, updated_at = CURRENT_TIMESTAMP
                WHERE email = ?
            """, (tier.value, plan.credits_monthly, customer_email))
            
            # Get user ID
            cursor.execute("SELECT id FROM users WHERE email = ?", (customer_email,))
            user_id = cursor.fetchone()[0]
            
            # Record payment
            cursor.execute("""
                INSERT INTO payments (
                    user_id, stripe_subscription_id, amount, currency, status, 
                    payment_type, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, subscription.id, session.amount_total / 100, session.currency,
                PaymentStatus.COMPLETED.value, 'subscription', json.dumps(session.metadata)
            ))
            
            # Record subscription history
            cursor.execute("""
                INSERT INTO subscription_history (
                    user_id, stripe_subscription_id, tier, status,
                    current_period_start, current_period_end
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id, subscription.id, tier.value, subscription.status,
                datetime.fromtimestamp(subscription.current_period_start),
                datetime.fromtimestamp(subscription.current_period_end)
            ))
            
            # Record credit transaction
            cursor.execute("""
                INSERT INTO credit_transactions (
                    user_id, transaction_type, credits, description
                ) VALUES (?, ?, ?, ?)
            """, (
                user_id, 'purchase', plan.credits_monthly,
                f"Monthly credits for {plan.name} subscription"
            ))
            
            conn.commit()
    
    def _handle_credits_success(self, session, customer_email: str):
        """Handle successful credit purchase"""
        credits_amount = int(session.metadata.get('credits_amount'))
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Update user credits
            cursor.execute("""
                UPDATE users 
                SET credits = credits + ?, updated_at = CURRENT_TIMESTAMP
                WHERE email = ?
            """, (credits_amount, customer_email))
            
            # Get user ID
            cursor.execute("SELECT id FROM users WHERE email = ?", (customer_email,))
            user_id = cursor.fetchone()[0]
            
            # Record payment
            cursor.execute("""
                INSERT INTO payments (
                    user_id, stripe_payment_intent_id, amount, currency, status, 
                    payment_type, credits_purchased, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, session.payment_intent, session.amount_total / 100, session.currency,
                PaymentStatus.COMPLETED.value, 'credits', credits_amount, json.dumps(session.metadata)
            ))
            
            payment_id = cursor.lastrowid
            
            # Record credit transaction
            cursor.execute("""
                INSERT INTO credit_transactions (
                    user_id, transaction_type, credits, description, payment_id
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                user_id, 'purchase', credits_amount,
                f"Purchased {credits_amount} credits", payment_id
            ))
            
            conn.commit()
    
    def use_credit(self, customer_email: str, description: str = "Video generation") -> bool:
        """Use one credit for video generation"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check current credits
            cursor.execute("SELECT id, credits FROM users WHERE email = ?", (customer_email,))
            result = cursor.fetchone()
            
            if not result or result[1] <= 0:
                return False
            
            user_id, current_credits = result
            
            # Deduct credit
            cursor.execute("""
                UPDATE users 
                SET credits = credits - 1, updated_at = CURRENT_TIMESTAMP
                WHERE email = ?
            """, (customer_email,))
            
            # Record transaction
            cursor.execute("""
                INSERT INTO credit_transactions (
                    user_id, transaction_type, credits, description
                ) VALUES (?, ?, ?, ?)
            """, (user_id, 'usage', -1, description))
            
            conn.commit()
            return True
    
    def get_user_info(self, customer_email: str) -> Optional[Dict]:
        """Get user subscription and credit information"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT subscription_tier, credits, created_at
                FROM users WHERE email = ?
            """, (customer_email,))
            result = cursor.fetchone()
            
            if result:
                return {
                    'subscription_tier': result[0],
                    'credits': result[1],
                    'created_at': result[2]
                }
            return None
    
    def get_payment_history(self, customer_email: str) -> List[Dict]:
        """Get user payment history"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.amount, p.currency, p.status, p.payment_type, 
                       p.credits_purchased, p.created_at
                FROM payments p
                JOIN users u ON p.user_id = u.id
                WHERE u.email = ?
                ORDER BY p.created_at DESC
            """, (customer_email,))
            
            payments = []
            for row in cursor.fetchall():
                payments.append({
                    'amount': row[0],
                    'currency': row[1],
                    'status': row[2],
                    'payment_type': row[3],
                    'credits_purchased': row[4],
                    'created_at': row[5]
                })
            
            return payments
    
    def cancel_subscription(self, customer_email: str) -> bool:
        """Cancel user subscription"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT stripe_customer_id FROM users WHERE email = ?
                """, (customer_email,))
                result = cursor.fetchone()
                
                if not result:
                    return False
                
                customer_id = result[0]
                
                # Get active subscriptions
                subscriptions = stripe.Subscription.list(customer=customer_id, status='active')
                
                for subscription in subscriptions:
                    stripe.Subscription.delete(subscription.id)
                
                # Update user tier to free
                cursor.execute("""
                    UPDATE users 
                    SET subscription_tier = 'free', updated_at = CURRENT_TIMESTAMP
                    WHERE email = ?
                """, (customer_email,))
                conn.commit()
                
                logger.info(f"Canceled subscription for {customer_email}")
                return True
        
        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel subscription: {str(e)}")
            return False


# Global payment service instance
payment_service = PaymentService()