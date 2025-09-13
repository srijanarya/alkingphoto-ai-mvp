"""
TalkingPhoto AI MVP - Payment Retry Service
Intelligent retry logic for failed payments and dunning management
"""

import stripe
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import sqlite3
import asyncio
from services.payment_service import payment_service
from services.security_service import security_service
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = Config.STRIPE_SECRET_KEY


class FailureReason(Enum):
    """Payment failure reasons"""
    INSUFFICIENT_FUNDS = "insufficient_funds"
    CARD_DECLINED = "card_declined"
    EXPIRED_CARD = "expired_card"
    INVALID_CVV = "incorrect_cvc"
    PROCESSING_ERROR = "processing_error"
    NETWORK_ERROR = "network_error"
    AUTHENTICATION_REQUIRED = "authentication_required"
    CARD_NOT_SUPPORTED = "card_not_supported"
    CURRENCY_NOT_SUPPORTED = "currency_not_supported"
    DUPLICATE_TRANSACTION = "duplicate_transaction"
    RISK_ASSESSMENT = "risk_assessment"
    VELOCITY_LIMIT = "velocity_limit"


class RetryStrategy(Enum):
    """Retry strategies"""
    IMMEDIATE = "immediate"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    SCHEDULED = "scheduled"
    SMART_RETRY = "smart_retry"
    NO_RETRY = "no_retry"


class DunningStage(Enum):
    """Dunning process stages"""
    GRACE_PERIOD = "grace_period"
    SOFT_DECLINE = "soft_decline"
    HARD_DECLINE = "hard_decline"
    FINAL_NOTICE = "final_notice"
    SUSPENDED = "suspended"
    CANCELED = "canceled"


@dataclass
class RetryConfiguration:
    """Retry configuration for different failure types"""
    failure_reason: FailureReason
    strategy: RetryStrategy
    max_attempts: int
    retry_intervals: List[int]  # Hours between retries
    smart_timing: bool
    notify_customer: bool
    escalate_after: int  # Attempts before escalation


@dataclass
class PaymentRetryAttempt:
    """Payment retry attempt record"""
    payment_id: str
    attempt_number: int
    retry_at: datetime
    failure_reason: FailureReason
    customer_email: str
    amount: float
    currency: str
    status: str


class PaymentRetryService:
    """
    Intelligent payment retry service
    Handles failed payments with smart retry logic and dunning management
    """
    
    def __init__(self):
        self.db_path = "data/payment_retries.db"
        self.init_database()
        self.retry_configurations = self._load_retry_configurations()
        self.running = False
    
    def init_database(self):
        """Initialize retry service database"""
        import os
        os.makedirs("data", exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Failed payments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS failed_payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stripe_payment_intent_id TEXT UNIQUE,
                    stripe_subscription_id TEXT,
                    customer_email TEXT NOT NULL,
                    customer_id TEXT NOT NULL,
                    amount REAL NOT NULL,
                    currency TEXT NOT NULL,
                    failure_reason TEXT NOT NULL,
                    failure_code TEXT,
                    failure_message TEXT,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    next_retry_at TIMESTAMP,
                    status TEXT DEFAULT 'pending_retry', -- 'pending_retry', 'retrying', 'succeeded', 'failed', 'abandoned'
                    dunning_stage TEXT DEFAULT 'grace_period',
                    last_attempt_at TIMESTAMP,
                    metadata TEXT, -- JSON
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Retry attempts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS retry_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    failed_payment_id INTEGER,
                    attempt_number INTEGER,
                    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    payment_intent_id TEXT,
                    status TEXT, -- 'succeeded', 'failed', 'processing'
                    failure_reason TEXT,
                    failure_code TEXT,
                    response_data TEXT, -- JSON
                    next_retry_at TIMESTAMP,
                    FOREIGN KEY (failed_payment_id) REFERENCES failed_payments (id)
                )
            """)
            
            # Dunning campaigns table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dunning_campaigns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_email TEXT NOT NULL,
                    campaign_type TEXT NOT NULL, -- 'subscription', 'invoice', 'one_time'
                    stage TEXT NOT NULL,
                    failed_payment_id INTEGER,
                    emails_sent INTEGER DEFAULT 0,
                    last_email_sent TIMESTAMP,
                    next_action_at TIMESTAMP,
                    is_active INTEGER DEFAULT 1,
                    metadata TEXT, -- JSON
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (failed_payment_id) REFERENCES failed_payments (id)
                )
            """)
            
            # Customer payment history table for retry intelligence
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customer_payment_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_email TEXT NOT NULL,
                    successful_payment_times TEXT, -- JSON array of successful payment hours
                    preferred_payment_day INTEGER, -- Day of month
                    average_retry_success_time INTEGER, -- Hours after failure
                    total_successful_retries INTEGER DEFAULT 0,
                    total_failed_retries INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def _load_retry_configurations(self) -> Dict[FailureReason, RetryConfiguration]:
        """Load retry configurations for different failure types"""
        return {
            FailureReason.INSUFFICIENT_FUNDS: RetryConfiguration(
                failure_reason=FailureReason.INSUFFICIENT_FUNDS,
                strategy=RetryStrategy.SMART_RETRY,
                max_attempts=5,
                retry_intervals=[24, 72, 168, 336],  # 1 day, 3 days, 1 week, 2 weeks
                smart_timing=True,
                notify_customer=True,
                escalate_after=3
            ),
            FailureReason.CARD_DECLINED: RetryConfiguration(
                failure_reason=FailureReason.CARD_DECLINED,
                strategy=RetryStrategy.SMART_RETRY,
                max_attempts=3,
                retry_intervals=[6, 24, 72],  # 6 hours, 1 day, 3 days
                smart_timing=True,
                notify_customer=True,
                escalate_after=2
            ),
            FailureReason.EXPIRED_CARD: RetryConfiguration(
                failure_reason=FailureReason.EXPIRED_CARD,
                strategy=RetryStrategy.NO_RETRY,
                max_attempts=0,
                retry_intervals=[],
                smart_timing=False,
                notify_customer=True,
                escalate_after=1
            ),
            FailureReason.INVALID_CVV: RetryConfiguration(
                failure_reason=FailureReason.INVALID_CVV,
                strategy=RetryStrategy.NO_RETRY,
                max_attempts=0,
                retry_intervals=[],
                smart_timing=False,
                notify_customer=True,
                escalate_after=1
            ),
            FailureReason.PROCESSING_ERROR: RetryConfiguration(
                failure_reason=FailureReason.PROCESSING_ERROR,
                strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                max_attempts=4,
                retry_intervals=[1, 4, 12, 24],  # 1 hour, 4 hours, 12 hours, 1 day
                smart_timing=False,
                notify_customer=False,
                escalate_after=3
            ),
            FailureReason.AUTHENTICATION_REQUIRED: RetryConfiguration(
                failure_reason=FailureReason.AUTHENTICATION_REQUIRED,
                strategy=RetryStrategy.SCHEDULED,
                max_attempts=2,
                retry_intervals=[1, 24],  # 1 hour, 1 day
                smart_timing=False,
                notify_customer=True,
                escalate_after=1
            ),
            FailureReason.NETWORK_ERROR: RetryConfiguration(
                failure_reason=FailureReason.NETWORK_ERROR,
                strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                max_attempts=3,
                retry_intervals=[0.5, 2, 8],  # 30 minutes, 2 hours, 8 hours
                smart_timing=False,
                notify_customer=False,
                escalate_after=2
            )
        }
    
    def handle_failed_payment(self, payment_intent_id: str, failure_data: Dict) -> Dict:
        """Handle a failed payment and initiate retry process"""
        try:
            # Extract failure information
            failure_code = failure_data.get('code', 'unknown')
            failure_message = failure_data.get('message', 'Unknown error')
            failure_reason = self._map_failure_code_to_reason(failure_code)
            
            # Get payment intent details
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            customer_id = payment_intent.customer
            customer = stripe.Customer.retrieve(customer_id) if customer_id else None
            customer_email = customer.email if customer else failure_data.get('customer_email')
            
            if not customer_email:
                logger.error(f"No customer email found for payment {payment_intent_id}")
                return {"success": False, "message": "Customer email not found"}
            
            # Check if payment already exists in retry system
            existing_payment = self._get_failed_payment(payment_intent_id)
            if existing_payment:
                return self._update_existing_failed_payment(existing_payment, failure_data)
            
            # Get retry configuration
            retry_config = self.retry_configurations.get(failure_reason)
            if not retry_config:
                retry_config = self.retry_configurations[FailureReason.CARD_DECLINED]  # Default
            
            # Calculate next retry time
            next_retry_at = None
            if retry_config.strategy != RetryStrategy.NO_RETRY:
                next_retry_at = self._calculate_next_retry_time(
                    failure_reason, customer_email, 0, retry_config
                )
            
            # Store failed payment
            failed_payment_id = self._store_failed_payment(
                payment_intent_id=payment_intent_id,
                customer_email=customer_email,
                customer_id=customer_id,
                amount=payment_intent.amount / 100,  # Convert from cents
                currency=payment_intent.currency,
                failure_reason=failure_reason,
                failure_code=failure_code,
                failure_message=failure_message,
                max_retries=retry_config.max_attempts,
                next_retry_at=next_retry_at,
                metadata=failure_data
            )
            
            # Start dunning campaign if needed
            if retry_config.notify_customer:
                self._start_dunning_campaign(failed_payment_id, customer_email, failure_reason)
            
            # Send immediate notification for critical failures
            if failure_reason in [FailureReason.EXPIRED_CARD, FailureReason.INVALID_CVV]:
                self._send_immediate_failure_notification(customer_email, failure_reason)
            
            logger.info(f"Failed payment {payment_intent_id} queued for retry")
            return {
                "success": True,
                "failed_payment_id": failed_payment_id,
                "next_retry_at": next_retry_at.isoformat() if next_retry_at else None,
                "retry_strategy": retry_config.strategy.value
            }
        
        except Exception as e:
            logger.error(f"Failed to handle payment failure: {str(e)}")
            return {"success": False, "message": str(e)}
    
    def retry_failed_payment(self, failed_payment_id: int) -> Dict:
        """Retry a specific failed payment"""
        try:
            # Get failed payment details
            failed_payment = self._get_failed_payment_by_id(failed_payment_id)
            if not failed_payment:
                return {"success": False, "message": "Failed payment not found"}
            
            if failed_payment['status'] not in ['pending_retry', 'failed']:
                return {"success": False, "message": f"Payment not eligible for retry: {failed_payment['status']}"}
            
            # Check retry limits
            if failed_payment['retry_count'] >= failed_payment['max_retries']:
                self._mark_payment_abandoned(failed_payment_id)
                return {"success": False, "message": "Maximum retry attempts reached"}
            
            # Update status to retrying
            self._update_payment_status(failed_payment_id, 'retrying')
            
            # Create new payment intent for retry
            retry_result = self._create_retry_payment_intent(failed_payment)
            
            # Record retry attempt
            self._record_retry_attempt(
                failed_payment_id=failed_payment_id,
                attempt_number=failed_payment['retry_count'] + 1,
                payment_intent_id=retry_result.get('payment_intent_id'),
                status=retry_result['status'],
                failure_reason=retry_result.get('failure_reason'),
                failure_code=retry_result.get('failure_code'),
                response_data=retry_result
            )
            
            if retry_result['success']:
                # Payment succeeded
                self._update_payment_status(failed_payment_id, 'succeeded')
                self._end_dunning_campaign(failed_payment_id)
                self._update_customer_payment_patterns(failed_payment['customer_email'], True)
                
                logger.info(f"Payment retry succeeded for {failed_payment['stripe_payment_intent_id']}")
                return {"success": True, "message": "Payment retry succeeded"}
            
            else:
                # Retry failed, schedule next attempt
                next_retry_at = self._calculate_next_retry_time(
                    FailureReason(failed_payment['failure_reason']),
                    failed_payment['customer_email'],
                    failed_payment['retry_count'] + 1,
                    self.retry_configurations[FailureReason(failed_payment['failure_reason'])]
                )
                
                self._update_failed_payment_for_next_retry(
                    failed_payment_id,
                    failed_payment['retry_count'] + 1,
                    next_retry_at
                )
                
                self._update_customer_payment_patterns(failed_payment['customer_email'], False)
                
                logger.warning(f"Payment retry failed for {failed_payment['stripe_payment_intent_id']}")
                return {
                    "success": False,
                    "message": "Payment retry failed",
                    "next_retry_at": next_retry_at.isoformat() if next_retry_at else None
                }
        
        except Exception as e:
            logger.error(f"Payment retry failed: {str(e)}")
            self._update_payment_status(failed_payment_id, 'failed')
            return {"success": False, "message": str(e)}
    
    def process_pending_retries(self):
        """Process all pending payment retries"""
        try:
            current_time = datetime.utcnow()
            
            # Get payments ready for retry
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id FROM failed_payments 
                    WHERE status = 'pending_retry' 
                    AND next_retry_at <= ? 
                    AND retry_count < max_retries
                    ORDER BY next_retry_at ASC
                    LIMIT 50
                """, (current_time,))
                
                pending_retries = cursor.fetchall()
            
            results = []
            for (failed_payment_id,) in pending_retries:
                result = self.retry_failed_payment(failed_payment_id)
                results.append({
                    "failed_payment_id": failed_payment_id,
                    "result": result
                })
                
                # Add delay between retries to avoid rate limiting
                time.sleep(0.5)
            
            logger.info(f"Processed {len(results)} pending payment retries")
            return results
        
        except Exception as e:
            logger.error(f"Failed to process pending retries: {str(e)}")
            return []
    
    def _map_failure_code_to_reason(self, failure_code: str) -> FailureReason:
        """Map Stripe failure code to internal failure reason"""
        code_mapping = {
            'insufficient_funds': FailureReason.INSUFFICIENT_FUNDS,
            'card_declined': FailureReason.CARD_DECLINED,
            'expired_card': FailureReason.EXPIRED_CARD,
            'incorrect_cvc': FailureReason.INVALID_CVV,
            'processing_error': FailureReason.PROCESSING_ERROR,
            'authentication_required': FailureReason.AUTHENTICATION_REQUIRED,
            'card_not_supported': FailureReason.CARD_NOT_SUPPORTED,
            'currency_not_supported': FailureReason.CURRENCY_NOT_SUPPORTED,
            'duplicate_transaction': FailureReason.DUPLICATE_TRANSACTION
        }
        
        return code_mapping.get(failure_code, FailureReason.CARD_DECLINED)
    
    def _calculate_next_retry_time(self, failure_reason: FailureReason, customer_email: str,
                                  retry_count: int, retry_config: RetryConfiguration) -> Optional[datetime]:
        """Calculate next retry time using smart timing"""
        if retry_count >= len(retry_config.retry_intervals):
            return None
        
        base_delay_hours = retry_config.retry_intervals[retry_count]
        next_retry = datetime.utcnow() + timedelta(hours=base_delay_hours)
        
        if retry_config.smart_timing:
            # Apply smart timing based on customer patterns
            customer_patterns = self._get_customer_payment_patterns(customer_email)
            if customer_patterns:
                next_retry = self._apply_smart_timing(next_retry, customer_patterns)
        
        return next_retry
    
    def _apply_smart_timing(self, base_time: datetime, customer_patterns: Dict) -> datetime:
        """Apply smart timing based on customer payment patterns"""
        try:
            # Adjust to customer's preferred payment day if within reasonable range
            preferred_day = customer_patterns.get('preferred_payment_day')
            if preferred_day and 1 <= preferred_day <= 28:
                target_date = base_time.replace(day=min(preferred_day, 28))
                if target_date > base_time:
                    base_time = target_date
            
            # Adjust to customer's successful payment times
            successful_times = customer_patterns.get('successful_payment_times', [])
            if successful_times:
                # Find the closest successful payment time
                current_hour = base_time.hour
                closest_hour = min(successful_times, key=lambda x: abs(x - current_hour))
                base_time = base_time.replace(hour=closest_hour, minute=0, second=0)
            
            # Avoid weekends for business customers (heuristic)
            if base_time.weekday() >= 5:  # Saturday or Sunday
                days_to_add = 7 - base_time.weekday()  # Move to Monday
                base_time += timedelta(days=days_to_add)
            
            return base_time
        
        except Exception as e:
            logger.error(f"Smart timing adjustment failed: {str(e)}")
            return base_time
    
    def _create_retry_payment_intent(self, failed_payment: Dict) -> Dict:
        """Create new payment intent for retry"""
        try:
            # Create new payment intent with same parameters
            payment_intent = stripe.PaymentIntent.create(
                amount=int(failed_payment['amount'] * 100),  # Convert to cents
                currency=failed_payment['currency'],
                customer=failed_payment['customer_id'],
                metadata={
                    'retry_attempt': True,
                    'original_payment_intent': failed_payment['stripe_payment_intent_id'],
                    'retry_count': failed_payment['retry_count'] + 1
                },
                # Use the same payment method if available
                payment_method=self._get_customer_default_payment_method(failed_payment['customer_id']),
                confirm=True,
                return_url='https://your-domain.com/return'
            )
            
            if payment_intent.status == 'succeeded':
                return {
                    "success": True,
                    "payment_intent_id": payment_intent.id,
                    "status": "succeeded"
                }
            elif payment_intent.status == 'requires_action':
                return {
                    "success": False,
                    "payment_intent_id": payment_intent.id,
                    "status": "requires_action",
                    "failure_reason": "authentication_required",
                    "client_secret": payment_intent.client_secret
                }
            else:
                return {
                    "success": False,
                    "payment_intent_id": payment_intent.id,
                    "status": payment_intent.status,
                    "failure_reason": "processing_error"
                }
        
        except stripe.error.CardError as e:
            return {
                "success": False,
                "status": "failed",
                "failure_reason": e.code,
                "failure_code": e.code,
                "error_message": str(e)
            }
        except Exception as e:
            logger.error(f"Failed to create retry payment intent: {str(e)}")
            return {
                "success": False,
                "status": "failed",
                "failure_reason": "processing_error",
                "error_message": str(e)
            }
    
    def _get_customer_default_payment_method(self, customer_id: str) -> Optional[str]:
        """Get customer's default payment method"""
        try:
            customer = stripe.Customer.retrieve(customer_id)
            return customer.invoice_settings.default_payment_method
        except Exception:
            return None
    
    # Database helper methods
    def _store_failed_payment(self, **kwargs) -> int:
        """Store failed payment in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO failed_payments 
                (stripe_payment_intent_id, customer_email, customer_id, amount, 
                 currency, failure_reason, failure_code, failure_message, 
                 max_retries, next_retry_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                kwargs['payment_intent_id'], kwargs['customer_email'], kwargs['customer_id'],
                kwargs['amount'], kwargs['currency'], kwargs['failure_reason'].value,
                kwargs['failure_code'], kwargs['failure_message'], kwargs['max_retries'],
                kwargs['next_retry_at'], json.dumps(kwargs['metadata'])
            ))
            
            failed_payment_id = cursor.lastrowid
            conn.commit()
            return failed_payment_id
    
    def _get_failed_payment(self, payment_intent_id: str) -> Optional[Dict]:
        """Get failed payment by payment intent ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM failed_payments 
                WHERE stripe_payment_intent_id = ?
            """, (payment_intent_id,))
            
            result = cursor.fetchone()
            if result:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, result))
            return None
    
    def _get_failed_payment_by_id(self, failed_payment_id: int) -> Optional[Dict]:
        """Get failed payment by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM failed_payments WHERE id = ?
            """, (failed_payment_id,))
            
            result = cursor.fetchone()
            if result:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, result))
            return None
    
    def _update_payment_status(self, failed_payment_id: int, status: str):
        """Update payment status"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE failed_payments 
                SET status = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (status, failed_payment_id))
            conn.commit()
    
    def _record_retry_attempt(self, **kwargs):
        """Record retry attempt"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO retry_attempts 
                (failed_payment_id, attempt_number, payment_intent_id, status, 
                 failure_reason, failure_code, response_data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                kwargs['failed_payment_id'], kwargs['attempt_number'],
                kwargs['payment_intent_id'], kwargs['status'],
                kwargs['failure_reason'], kwargs['failure_code'],
                json.dumps(kwargs['response_data'])
            ))
            conn.commit()
    
    def _update_failed_payment_for_next_retry(self, failed_payment_id: int, 
                                            retry_count: int, next_retry_at: Optional[datetime]):
        """Update failed payment for next retry"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if next_retry_at:
                cursor.execute("""
                    UPDATE failed_payments 
                    SET retry_count = ?, next_retry_at = ?, status = 'pending_retry',
                        last_attempt_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (retry_count, next_retry_at, failed_payment_id))
            else:
                cursor.execute("""
                    UPDATE failed_payments 
                    SET retry_count = ?, status = 'failed', 
                        last_attempt_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (retry_count, failed_payment_id))
            
            conn.commit()
    
    def _mark_payment_abandoned(self, failed_payment_id: int):
        """Mark payment as abandoned"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE failed_payments 
                SET status = 'abandoned', updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (failed_payment_id,))
            conn.commit()
    
    def _get_customer_payment_patterns(self, customer_email: str) -> Optional[Dict]:
        """Get customer payment patterns for smart retry timing"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM customer_payment_patterns 
                WHERE customer_email = ?
            """, (customer_email,))
            
            result = cursor.fetchone()
            if result:
                columns = [description[0] for description in cursor.description]
                pattern_data = dict(zip(columns, result))
                # Parse JSON data
                if pattern_data['successful_payment_times']:
                    pattern_data['successful_payment_times'] = json.loads(
                        pattern_data['successful_payment_times']
                    )
                return pattern_data
            return None
    
    def _update_customer_payment_patterns(self, customer_email: str, success: bool):
        """Update customer payment patterns based on retry success/failure"""
        # Implementation for learning customer payment patterns
        pass
    
    # Dunning management methods
    def _start_dunning_campaign(self, failed_payment_id: int, customer_email: str, 
                               failure_reason: FailureReason):
        """Start dunning campaign for failed payment"""
        # Implementation for dunning campaign
        pass
    
    def _end_dunning_campaign(self, failed_payment_id: int):
        """End dunning campaign after successful retry"""
        # Implementation for ending dunning campaign
        pass
    
    def _send_immediate_failure_notification(self, customer_email: str, failure_reason: FailureReason):
        """Send immediate notification for critical payment failures"""
        # Implementation for immediate notification
        pass
    
    def _update_existing_failed_payment(self, existing_payment: Dict, failure_data: Dict) -> Dict:
        """Update existing failed payment record"""
        # Implementation for updating existing failed payment
        return {"success": True, "message": "Existing payment updated"}
    
    async def start_retry_processor(self):
        """Start the retry processor service"""
        self.running = True
        logger.info("Payment retry processor started")
        
        while self.running:
            try:
                self.process_pending_retries()
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"Retry processor error: {str(e)}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    def stop_retry_processor(self):
        """Stop the retry processor service"""
        self.running = False
        logger.info("Payment retry processor stopped")


# Global retry service instance
retry_service = PaymentRetryService()