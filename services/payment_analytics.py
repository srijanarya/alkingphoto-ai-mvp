"""
TalkingPhoto AI MVP - Payment Analytics Service
Comprehensive payment tracking, conversion analysis, and business intelligence
"""

import json
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Analytics metric types"""
    REVENUE = "revenue"
    CONVERSION = "conversion"
    CHURN = "churn"
    LTV = "lifetime_value"
    CAC = "customer_acquisition_cost"
    ARR = "annual_recurring_revenue"
    MRR = "monthly_recurring_revenue"
    TRIAL_CONVERSION = "trial_conversion"


class TimeRange(Enum):
    """Time range options for analytics"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


@dataclass
class PaymentMetric:
    """Payment metric data structure"""
    metric_type: MetricType
    value: float
    period: str
    currency: str
    metadata: Dict[str, Any]
    calculated_at: datetime


@dataclass
class ConversionFunnel:
    """Conversion funnel data"""
    stage: str
    users: int
    conversion_rate: float
    drop_off_rate: float


class PaymentAnalyticsService:
    """
    Comprehensive payment analytics service
    Tracks revenue, conversions, churn, and business metrics
    """
    
    def __init__(self):
        self.db_path = "data/payment_analytics.db"
        self.init_database()
    
    def init_database(self):
        """Initialize analytics database"""
        import os
        os.makedirs("data", exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Revenue analytics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS revenue_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    tier TEXT NOT NULL,
                    currency TEXT NOT NULL,
                    gross_revenue REAL DEFAULT 0,
                    net_revenue REAL DEFAULT 0,
                    refunds REAL DEFAULT 0,
                    chargebacks REAL DEFAULT 0,
                    transaction_count INTEGER DEFAULT 0,
                    new_customers INTEGER DEFAULT 0,
                    returning_customers INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, tier, currency)
                )
            """)
            
            # Conversion funnel analytics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversion_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    funnel_stage TEXT NOT NULL,
                    visitors INTEGER DEFAULT 0,
                    pricing_page_views INTEGER DEFAULT 0,
                    checkout_starts INTEGER DEFAULT 0,
                    payment_attempts INTEGER DEFAULT 0,
                    successful_payments INTEGER DEFAULT 0,
                    conversion_rate REAL DEFAULT 0,
                    source TEXT,
                    campaign TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, funnel_stage, source, campaign)
                )
            """)
            
            # Subscription analytics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS subscription_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    tier TEXT NOT NULL,
                    active_subscriptions INTEGER DEFAULT 0,
                    new_subscriptions INTEGER DEFAULT 0,
                    canceled_subscriptions INTEGER DEFAULT 0,
                    churned_subscriptions INTEGER DEFAULT 0,
                    upgraded_subscriptions INTEGER DEFAULT 0,
                    downgraded_subscriptions INTEGER DEFAULT 0,
                    mrr REAL DEFAULT 0,
                    arr REAL DEFAULT 0,
                    churn_rate REAL DEFAULT 0,
                    ltv REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, tier)
                )
            """)
            
            # Customer lifetime value analytics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ltv_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_email TEXT NOT NULL,
                    acquisition_date DATE NOT NULL,
                    first_payment_date DATE,
                    last_payment_date DATE,
                    total_revenue REAL DEFAULT 0,
                    total_payments INTEGER DEFAULT 0,
                    subscription_months INTEGER DEFAULT 0,
                    current_tier TEXT,
                    acquisition_source TEXT,
                    acquisition_campaign TEXT,
                    predicted_ltv REAL DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    churn_date DATE,
                    churn_reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(customer_email)
                )
            """)
            
            # Payment method analytics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS payment_method_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    payment_method TEXT NOT NULL, -- 'card', 'paypal', 'apple_pay', etc.
                    card_brand TEXT, -- 'visa', 'mastercard', 'amex', etc.
                    country TEXT,
                    currency TEXT,
                    transaction_count INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    success_rate REAL DEFAULT 0,
                    average_amount REAL DEFAULT 0,
                    total_amount REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, payment_method, card_brand, country, currency)
                )
            """)
            
            # Cohort analytics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cohort_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cohort_month TEXT NOT NULL, -- YYYY-MM format
                    period_number INTEGER NOT NULL, -- 0, 1, 2, 3... (months since acquisition)
                    customers_start INTEGER NOT NULL,
                    customers_active INTEGER NOT NULL,
                    retention_rate REAL DEFAULT 0,
                    revenue REAL DEFAULT 0,
                    avg_revenue_per_customer REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(cohort_month, period_number)
                )
            """)
            
            # A/B test analytics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ab_test_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_name TEXT NOT NULL,
                    variant TEXT NOT NULL,
                    date DATE NOT NULL,
                    exposures INTEGER DEFAULT 0,
                    conversions INTEGER DEFAULT 0,
                    conversion_rate REAL DEFAULT 0,
                    revenue REAL DEFAULT 0,
                    statistical_significance REAL DEFAULT 0,
                    is_winner INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(test_name, variant, date)
                )
            """)
            
            conn.commit()
    
    def track_payment_event(self, event_type: str, event_data: Dict):
        """Track payment-related events for analytics"""
        try:
            current_date = datetime.now().date()
            
            if event_type == "payment_success":
                self._track_successful_payment(current_date, event_data)
            elif event_type == "payment_failure":
                self._track_failed_payment(current_date, event_data)
            elif event_type == "subscription_created":
                self._track_new_subscription(current_date, event_data)
            elif event_type == "subscription_canceled":
                self._track_subscription_cancellation(current_date, event_data)
            elif event_type == "customer_acquired":
                self._track_customer_acquisition(event_data)
            elif event_type == "trial_started":
                self._track_trial_start(current_date, event_data)
            elif event_type == "pricing_page_view":
                self._track_pricing_page_view(current_date, event_data)
            elif event_type == "checkout_started":
                self._track_checkout_start(current_date, event_data)
            
            logger.info(f"Tracked payment event: {event_type}")
        
        except Exception as e:
            logger.error(f"Failed to track payment event {event_type}: {str(e)}")
    
    def _track_successful_payment(self, date: datetime.date, event_data: Dict):
        """Track successful payment"""
        amount = event_data.get('amount', 0)
        currency = event_data.get('currency', 'usd')
        tier = event_data.get('tier', 'unknown')
        customer_email = event_data.get('customer_email')
        payment_method = event_data.get('payment_method', 'card')
        card_brand = event_data.get('card_brand')
        country = event_data.get('country')
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Update revenue analytics
            cursor.execute("""
                INSERT OR REPLACE INTO revenue_analytics 
                (date, tier, currency, gross_revenue, net_revenue, transaction_count)
                VALUES (?, ?, ?, 
                    COALESCE((SELECT gross_revenue FROM revenue_analytics WHERE date = ? AND tier = ? AND currency = ?), 0) + ?,
                    COALESCE((SELECT net_revenue FROM revenue_analytics WHERE date = ? AND tier = ? AND currency = ?), 0) + ?,
                    COALESCE((SELECT transaction_count FROM revenue_analytics WHERE date = ? AND tier = ? AND currency = ?), 0) + 1)
            """, (date, tier, currency, date, tier, currency, amount,
                  date, tier, currency, amount, date, tier, currency))
            
            # Update payment method analytics
            cursor.execute("""
                INSERT OR REPLACE INTO payment_method_analytics 
                (date, payment_method, card_brand, country, currency, 
                 transaction_count, success_count, total_amount, average_amount, success_rate)
                VALUES (?, ?, ?, ?, ?, 
                    COALESCE((SELECT transaction_count FROM payment_method_analytics WHERE date = ? AND payment_method = ? AND COALESCE(card_brand, '') = COALESCE(?, '') AND COALESCE(country, '') = COALESCE(?, '') AND currency = ?), 0) + 1,
                    COALESCE((SELECT success_count FROM payment_method_analytics WHERE date = ? AND payment_method = ? AND COALESCE(card_brand, '') = COALESCE(?, '') AND COALESCE(country, '') = COALESCE(?, '') AND currency = ?), 0) + 1,
                    COALESCE((SELECT total_amount FROM payment_method_analytics WHERE date = ? AND payment_method = ? AND COALESCE(card_brand, '') = COALESCE(?, '') AND COALESCE(country, '') = COALESCE(?, '') AND currency = ?), 0) + ?,
                    (COALESCE((SELECT total_amount FROM payment_method_analytics WHERE date = ? AND payment_method = ? AND COALESCE(card_brand, '') = COALESCE(?, '') AND COALESCE(country, '') = COALESCE(?, '') AND currency = ?), 0) + ?) / 
                     (COALESCE((SELECT transaction_count FROM payment_method_analytics WHERE date = ? AND payment_method = ? AND COALESCE(card_brand, '') = COALESCE(?, '') AND COALESCE(country, '') = COALESCE(?, '') AND currency = ?), 0) + 1),
                    (COALESCE((SELECT success_count FROM payment_method_analytics WHERE date = ? AND payment_method = ? AND COALESCE(card_brand, '') = COALESCE(?, '') AND COALESCE(country, '') = COALESCE(?, '') AND currency = ?), 0) + 1) * 100.0 / 
                     (COALESCE((SELECT transaction_count FROM payment_method_analytics WHERE date = ? AND payment_method = ? AND COALESCE(card_brand, '') = COALESCE(?, '') AND COALESCE(country, '') = COALESCE(?, '') AND currency = ?), 0) + 1))
            """, (date, payment_method, card_brand, country, currency,
                  date, payment_method, card_brand, country, currency,
                  date, payment_method, card_brand, country, currency,
                  date, payment_method, card_brand, country, currency, amount,
                  date, payment_method, card_brand, country, currency, amount,
                  date, payment_method, card_brand, country, currency,
                  date, payment_method, card_brand, country, currency,
                  date, payment_method, card_brand, country, currency))
            
            # Update customer LTV
            if customer_email:
                self._update_customer_ltv(cursor, customer_email, amount, tier)
            
            conn.commit()
    
    def _track_failed_payment(self, date: datetime.date, event_data: Dict):
        """Track failed payment"""
        payment_method = event_data.get('payment_method', 'card')
        card_brand = event_data.get('card_brand')
        country = event_data.get('country')
        currency = event_data.get('currency', 'usd')
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Update payment method analytics
            cursor.execute("""
                INSERT OR REPLACE INTO payment_method_analytics 
                (date, payment_method, card_brand, country, currency, 
                 transaction_count, failure_count, success_rate)
                VALUES (?, ?, ?, ?, ?, 
                    COALESCE((SELECT transaction_count FROM payment_method_analytics WHERE date = ? AND payment_method = ? AND COALESCE(card_brand, '') = COALESCE(?, '') AND COALESCE(country, '') = COALESCE(?, '') AND currency = ?), 0) + 1,
                    COALESCE((SELECT failure_count FROM payment_method_analytics WHERE date = ? AND payment_method = ? AND COALESCE(card_brand, '') = COALESCE(?, '') AND COALESCE(country, '') = COALESCE(?, '') AND currency = ?), 0) + 1,
                    COALESCE((SELECT success_count FROM payment_method_analytics WHERE date = ? AND payment_method = ? AND COALESCE(card_brand, '') = COALESCE(?, '') AND COALESCE(country, '') = COALESCE(?, '') AND currency = ?), 0) * 100.0 / 
                     (COALESCE((SELECT transaction_count FROM payment_method_analytics WHERE date = ? AND payment_method = ? AND COALESCE(card_brand, '') = COALESCE(?, '') AND COALESCE(country, '') = COALESCE(?, '') AND currency = ?), 0) + 1))
            """, (date, payment_method, card_brand, country, currency,
                  date, payment_method, card_brand, country, currency,
                  date, payment_method, card_brand, country, currency,
                  date, payment_method, card_brand, country, currency,
                  date, payment_method, card_brand, country, currency))
            
            conn.commit()
    
    def _track_new_subscription(self, date: datetime.date, event_data: Dict):
        """Track new subscription"""
        tier = event_data.get('tier', 'unknown')
        mrr = event_data.get('monthly_amount', 0)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO subscription_analytics 
                (date, tier, active_subscriptions, new_subscriptions, mrr, arr)
                VALUES (?, ?, 
                    COALESCE((SELECT active_subscriptions FROM subscription_analytics WHERE date = ? AND tier = ?), 0) + 1,
                    COALESCE((SELECT new_subscriptions FROM subscription_analytics WHERE date = ? AND tier = ?), 0) + 1,
                    COALESCE((SELECT mrr FROM subscription_analytics WHERE date = ? AND tier = ?), 0) + ?,
                    (COALESCE((SELECT mrr FROM subscription_analytics WHERE date = ? AND tier = ?), 0) + ?) * 12)
            """, (date, tier, date, tier, date, tier, date, tier, mrr, date, tier, mrr))
            
            conn.commit()
    
    def _track_subscription_cancellation(self, date: datetime.date, event_data: Dict):
        """Track subscription cancellation"""
        tier = event_data.get('tier', 'unknown')
        mrr_lost = event_data.get('monthly_amount', 0)
        customer_email = event_data.get('customer_email')
        churn_reason = event_data.get('churn_reason')
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Update subscription analytics
            cursor.execute("""
                INSERT OR REPLACE INTO subscription_analytics 
                (date, tier, active_subscriptions, canceled_subscriptions, 
                 churned_subscriptions, mrr, arr)
                VALUES (?, ?, 
                    MAX(0, COALESCE((SELECT active_subscriptions FROM subscription_analytics WHERE date = ? AND tier = ?), 0) - 1),
                    COALESCE((SELECT canceled_subscriptions FROM subscription_analytics WHERE date = ? AND tier = ?), 0) + 1,
                    COALESCE((SELECT churned_subscriptions FROM subscription_analytics WHERE date = ? AND tier = ?), 0) + 1,
                    MAX(0, COALESCE((SELECT mrr FROM subscription_analytics WHERE date = ? AND tier = ?), 0) - ?),
                    MAX(0, (COALESCE((SELECT mrr FROM subscription_analytics WHERE date = ? AND tier = ?), 0) - ?) * 12))
            """, (date, tier, date, tier, date, tier, date, tier, 
                  date, tier, mrr_lost, date, tier, mrr_lost))
            
            # Update customer LTV
            if customer_email:
                cursor.execute("""
                    UPDATE ltv_analytics 
                    SET is_active = 0, churn_date = ?, churn_reason = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE customer_email = ?
                """, (date, churn_reason, customer_email))
            
            conn.commit()
    
    def _track_customer_acquisition(self, event_data: Dict):
        """Track customer acquisition"""
        customer_email = event_data.get('customer_email')
        acquisition_source = event_data.get('source', 'unknown')
        acquisition_campaign = event_data.get('campaign')
        tier = event_data.get('tier')
        
        if not customer_email:
            return
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO ltv_analytics 
                (customer_email, acquisition_date, current_tier, 
                 acquisition_source, acquisition_campaign)
                VALUES (?, ?, ?, ?, ?)
            """, (customer_email, datetime.now().date(), tier, 
                  acquisition_source, acquisition_campaign))
            
            conn.commit()
    
    def _track_pricing_page_view(self, date: datetime.date, event_data: Dict):
        """Track pricing page view"""
        source = event_data.get('source', 'direct')
        campaign = event_data.get('campaign', 'none')
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO conversion_analytics 
                (date, funnel_stage, pricing_page_views, source, campaign)
                VALUES (?, 'pricing_page', 
                    COALESCE((SELECT pricing_page_views FROM conversion_analytics WHERE date = ? AND funnel_stage = 'pricing_page' AND source = ? AND campaign = ?), 0) + 1,
                    ?, ?)
            """, (date, date, source, campaign, source, campaign))
            
            conn.commit()
    
    def _track_checkout_start(self, date: datetime.date, event_data: Dict):
        """Track checkout start"""
        source = event_data.get('source', 'direct')
        campaign = event_data.get('campaign', 'none')
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO conversion_analytics 
                (date, funnel_stage, checkout_starts, source, campaign)
                VALUES (?, 'checkout', 
                    COALESCE((SELECT checkout_starts FROM conversion_analytics WHERE date = ? AND funnel_stage = 'checkout' AND source = ? AND campaign = ?), 0) + 1,
                    ?, ?)
            """, (date, date, source, campaign, source, campaign))
            
            conn.commit()
    
    def _update_customer_ltv(self, cursor, customer_email: str, amount: float, tier: str):
        """Update customer lifetime value"""
        cursor.execute("""
            UPDATE ltv_analytics 
            SET total_revenue = total_revenue + ?,
                total_payments = total_payments + 1,
                current_tier = ?,
                last_payment_date = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE customer_email = ?
        """, (amount, tier, datetime.now().date(), customer_email))
        
        # If no existing record, create one
        if cursor.rowcount == 0:
            cursor.execute("""
                INSERT INTO ltv_analytics 
                (customer_email, acquisition_date, first_payment_date, 
                 last_payment_date, total_revenue, total_payments, current_tier)
                VALUES (?, ?, ?, ?, ?, 1, ?)
            """, (customer_email, datetime.now().date(), datetime.now().date(),
                  datetime.now().date(), amount, tier))
    
    def get_revenue_analytics(self, start_date: datetime.date, end_date: datetime.date,
                            group_by: str = "daily") -> Dict:
        """Get revenue analytics for specified period"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Group by clause
                if group_by == "daily":
                    group_clause = "date"
                elif group_by == "weekly":
                    group_clause = "strftime('%Y-W%W', date)"
                elif group_by == "monthly":
                    group_clause = "strftime('%Y-%m', date)"
                else:
                    group_clause = "date"
                
                query = f"""
                    SELECT {group_clause} as period,
                           SUM(gross_revenue) as gross_revenue,
                           SUM(net_revenue) as net_revenue,
                           SUM(refunds) as refunds,
                           SUM(chargebacks) as chargebacks,
                           SUM(transaction_count) as transactions,
                           COUNT(DISTINCT tier) as active_tiers
                    FROM revenue_analytics 
                    WHERE date BETWEEN ? AND ?
                    GROUP BY {group_clause}
                    ORDER BY period ASC
                """
                
                df = pd.read_sql_query(query, conn, params=(start_date, end_date))
                
                return {
                    "periods": df['period'].tolist(),
                    "gross_revenue": df['gross_revenue'].tolist(),
                    "net_revenue": df['net_revenue'].tolist(),
                    "refunds": df['refunds'].tolist(),
                    "chargebacks": df['chargebacks'].tolist(),
                    "transactions": df['transactions'].tolist(),
                    "total_gross_revenue": df['gross_revenue'].sum(),
                    "total_net_revenue": df['net_revenue'].sum(),
                    "total_transactions": df['transactions'].sum(),
                    "average_transaction_value": df['gross_revenue'].sum() / max(df['transactions'].sum(), 1)
                }
        
        except Exception as e:
            logger.error(f"Failed to get revenue analytics: {str(e)}")
            return {}
    
    def get_conversion_funnel(self, start_date: datetime.date, end_date: datetime.date) -> List[ConversionFunnel]:
        """Get conversion funnel analysis"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT 
                        SUM(visitors) as total_visitors,
                        SUM(pricing_page_views) as total_pricing_views,
                        SUM(checkout_starts) as total_checkout_starts,
                        SUM(payment_attempts) as total_payment_attempts,
                        SUM(successful_payments) as total_successful_payments
                    FROM conversion_analytics 
                    WHERE date BETWEEN ? AND ?
                """
                
                result = conn.execute(query, (start_date, end_date)).fetchone()
                
                if not result:
                    return []
                
                visitors, pricing_views, checkout_starts, payment_attempts, successful_payments = result
                
                # Calculate conversion rates
                funnel_stages = []
                
                if visitors and visitors > 0:
                    funnel_stages.append(ConversionFunnel(
                        stage="Visitors",
                        users=visitors,
                        conversion_rate=100.0,
                        drop_off_rate=0.0
                    ))
                    
                    if pricing_views and pricing_views > 0:
                        pricing_conversion = (pricing_views / visitors) * 100
                        funnel_stages.append(ConversionFunnel(
                            stage="Pricing Page",
                            users=pricing_views,
                            conversion_rate=pricing_conversion,
                            drop_off_rate=100 - pricing_conversion
                        ))
                        
                        if checkout_starts and checkout_starts > 0:
                            checkout_conversion = (checkout_starts / pricing_views) * 100
                            funnel_stages.append(ConversionFunnel(
                                stage="Checkout Started",
                                users=checkout_starts,
                                conversion_rate=checkout_conversion,
                                drop_off_rate=100 - checkout_conversion
                            ))
                            
                            if successful_payments and successful_payments > 0:
                                payment_conversion = (successful_payments / checkout_starts) * 100
                                funnel_stages.append(ConversionFunnel(
                                    stage="Payment Success",
                                    users=successful_payments,
                                    conversion_rate=payment_conversion,
                                    drop_off_rate=100 - payment_conversion
                                ))
                
                return funnel_stages
        
        except Exception as e:
            logger.error(f"Failed to get conversion funnel: {str(e)}")
            return []
    
    def get_subscription_metrics(self, start_date: datetime.date, end_date: datetime.date) -> Dict:
        """Get subscription analytics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT 
                        tier,
                        SUM(new_subscriptions) as new_subs,
                        SUM(canceled_subscriptions) as canceled_subs,
                        AVG(churn_rate) as avg_churn_rate,
                        SUM(mrr) as total_mrr,
                        SUM(arr) as total_arr,
                        AVG(ltv) as avg_ltv
                    FROM subscription_analytics 
                    WHERE date BETWEEN ? AND ?
                    GROUP BY tier
                """
                
                df = pd.read_sql_query(query, conn, params=(start_date, end_date))
                
                return {
                    "by_tier": df.to_dict('records'),
                    "total_mrr": df['total_mrr'].sum(),
                    "total_arr": df['total_arr'].sum(),
                    "overall_churn_rate": df['avg_churn_rate'].mean(),
                    "net_new_subscriptions": df['new_subs'].sum() - df['canceled_subs'].sum()
                }
        
        except Exception as e:
            logger.error(f"Failed to get subscription metrics: {str(e)}")
            return {}
    
    def get_payment_method_performance(self, start_date: datetime.date, end_date: datetime.date) -> Dict:
        """Get payment method performance analytics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT 
                        payment_method,
                        card_brand,
                        SUM(transaction_count) as total_transactions,
                        SUM(success_count) as total_successes,
                        SUM(failure_count) as total_failures,
                        AVG(success_rate) as avg_success_rate,
                        SUM(total_amount) as total_amount,
                        AVG(average_amount) as avg_transaction_amount
                    FROM payment_method_analytics 
                    WHERE date BETWEEN ? AND ?
                    GROUP BY payment_method, card_brand
                    ORDER BY total_transactions DESC
                """
                
                df = pd.read_sql_query(query, conn, params=(start_date, end_date))
                
                return {
                    "payment_methods": df.to_dict('records'),
                    "overall_success_rate": (df['total_successes'].sum() / df['total_transactions'].sum()) * 100 if df['total_transactions'].sum() > 0 else 0,
                    "total_volume": df['total_amount'].sum()
                }
        
        except Exception as e:
            logger.error(f"Failed to get payment method performance: {str(e)}")
            return {}
    
    def get_customer_ltv_analysis(self, limit: int = 100) -> Dict:
        """Get customer lifetime value analysis"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT 
                        current_tier,
                        COUNT(*) as customer_count,
                        AVG(total_revenue) as avg_ltv,
                        AVG(total_payments) as avg_payments,
                        AVG(subscription_months) as avg_subscription_months,
                        SUM(total_revenue) as total_revenue,
                        acquisition_source,
                        AVG(CASE WHEN churn_date IS NOT NULL THEN 
                            julianday(churn_date) - julianday(acquisition_date) 
                            ELSE julianday('now') - julianday(acquisition_date) END) as avg_days_active
                    FROM ltv_analytics 
                    WHERE total_revenue > 0
                    GROUP BY current_tier, acquisition_source
                    ORDER BY avg_ltv DESC
                    LIMIT ?
                """
                
                df = pd.read_sql_query(query, conn, params=(limit,))
                
                return {
                    "ltv_by_tier_source": df.to_dict('records'),
                    "overall_avg_ltv": df['avg_ltv'].mean(),
                    "total_customers": df['customer_count'].sum(),
                    "total_revenue": df['total_revenue'].sum()
                }
        
        except Exception as e:
            logger.error(f"Failed to get LTV analysis: {str(e)}")
            return {}
    
    def generate_revenue_chart(self, start_date: datetime.date, end_date: datetime.date,
                             group_by: str = "daily") -> go.Figure:
        """Generate revenue chart"""
        revenue_data = self.get_revenue_analytics(start_date, end_date, group_by)
        
        if not revenue_data:
            return go.Figure()
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Revenue Over Time', 'Transaction Volume', 
                          'Revenue Breakdown', 'Growth Rate'),
            specs=[[{"secondary_y": True}, {"secondary_y": False}],
                   [{"type": "pie"}, {"secondary_y": False}]]
        )
        
        # Revenue over time
        fig.add_trace(
            go.Scatter(
                x=revenue_data['periods'],
                y=revenue_data['gross_revenue'],
                name='Gross Revenue',
                line=dict(color='#2E86C1', width=3)
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=revenue_data['periods'],
                y=revenue_data['net_revenue'],
                name='Net Revenue',
                line=dict(color='#28B463', width=3)
            ),
            row=1, col=1
        )
        
        # Transaction volume
        fig.add_trace(
            go.Bar(
                x=revenue_data['periods'],
                y=revenue_data['transactions'],
                name='Transactions',
                marker_color='#F39C12'
            ),
            row=1, col=2
        )
        
        # Revenue breakdown pie chart
        fig.add_trace(
            go.Pie(
                labels=['Gross Revenue', 'Refunds', 'Chargebacks'],
                values=[
                    revenue_data['total_gross_revenue'],
                    sum(revenue_data['refunds']),
                    sum(revenue_data['chargebacks'])
                ],
                name="Revenue Breakdown"
            ),
            row=2, col=1
        )
        
        # Growth rate
        if len(revenue_data['gross_revenue']) > 1:
            growth_rates = []
            for i in range(1, len(revenue_data['gross_revenue'])):
                if revenue_data['gross_revenue'][i-1] > 0:
                    growth = ((revenue_data['gross_revenue'][i] - revenue_data['gross_revenue'][i-1]) / 
                             revenue_data['gross_revenue'][i-1]) * 100
                    growth_rates.append(growth)
                else:
                    growth_rates.append(0)
            
            fig.add_trace(
                go.Scatter(
                    x=revenue_data['periods'][1:],
                    y=growth_rates,
                    name='Growth Rate (%)',
                    line=dict(color='#E74C3C', width=2)
                ),
                row=2, col=2
            )
        
        fig.update_layout(
            title="Revenue Analytics Dashboard",
            height=800,
            showlegend=True
        )
        
        return fig
    
    def generate_conversion_funnel_chart(self, start_date: datetime.date, end_date: datetime.date) -> go.Figure:
        """Generate conversion funnel chart"""
        funnel_data = self.get_conversion_funnel(start_date, end_date)
        
        if not funnel_data:
            return go.Figure()
        
        stages = [stage.stage for stage in funnel_data]
        users = [stage.users for stage in funnel_data]
        conversion_rates = [stage.conversion_rate for stage in funnel_data]
        
        fig = go.Figure()
        
        # Funnel chart
        fig.add_trace(go.Funnel(
            y=stages,
            x=users,
            textinfo="value+percent initial",
            marker=dict(
                color=["deepskyblue", "lightsalmon", "tan", "teal"],
                line=dict(width=2, color="wheat")
            ),
            connector=dict(line=dict(color="royalblue", dash="dot", width=3))
        ))
        
        fig.update_layout(
            title="Conversion Funnel Analysis",
            font=dict(size=16)
        )
        
        return fig


# Global analytics service instance
analytics_service = PaymentAnalyticsService()