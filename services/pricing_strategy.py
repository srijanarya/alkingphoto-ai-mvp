"""
TalkingPhoto AI MVP - Pricing Strategy and Tier Management
Dynamic pricing, regional adjustments, and promotional campaigns
"""

import json
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Currency(Enum):
    """Supported currencies"""
    USD = "usd"
    EUR = "eur"
    GBP = "gbp"
    INR = "inr"
    CAD = "cad"
    AUD = "aud"
    JPY = "jpy"
    BRL = "brl"
    MXN = "mxn"


class PricingTier(Enum):
    """Pricing tiers"""
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass
class RegionalPricing:
    """Regional pricing configuration"""
    currency: Currency
    country_codes: List[str]
    price_multiplier: float
    tax_rate: float
    payment_methods: List[str]
    local_features: List[str]


@dataclass
class PromotionalCampaign:
    """Promotional campaign configuration"""
    campaign_id: str
    name: str
    discount_percentage: float
    discount_amount: float
    applicable_tiers: List[PricingTier]
    start_date: datetime
    end_date: datetime
    max_uses: int
    current_uses: int
    promo_code: str
    target_regions: List[str]
    is_active: bool


class PricingStrategy:
    """
    Comprehensive pricing strategy management
    Handles regional pricing, promotions, and dynamic adjustments
    """
    
    def __init__(self):
        self.db_path = "data/pricing.db"
        self.init_database()
        self.load_regional_configurations()
        self.base_pricing = self._load_base_pricing()
    
    def init_database(self):
        """Initialize pricing database"""
        import os
        os.makedirs("data", exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Regional pricing table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS regional_pricing (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    currency TEXT NOT NULL,
                    country_code TEXT NOT NULL,
                    tier TEXT NOT NULL,
                    monthly_price REAL NOT NULL,
                    yearly_price REAL NOT NULL,
                    price_multiplier REAL DEFAULT 1.0,
                    tax_rate REAL DEFAULT 0.0,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Promotional campaigns table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS promotional_campaigns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    discount_percentage REAL DEFAULT 0,
                    discount_amount REAL DEFAULT 0,
                    applicable_tiers TEXT, -- JSON array
                    start_date TIMESTAMP NOT NULL,
                    end_date TIMESTAMP NOT NULL,
                    max_uses INTEGER DEFAULT -1,
                    current_uses INTEGER DEFAULT 0,
                    promo_code TEXT UNIQUE,
                    target_regions TEXT, -- JSON array
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Pricing analytics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pricing_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tier TEXT NOT NULL,
                    currency TEXT NOT NULL,
                    country_code TEXT,
                    price_paid REAL NOT NULL,
                    original_price REAL NOT NULL,
                    discount_applied REAL DEFAULT 0,
                    campaign_id TEXT,
                    conversion_source TEXT,
                    user_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Dynamic pricing rules table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dynamic_pricing_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_name TEXT NOT NULL,
                    condition_type TEXT NOT NULL, -- 'time_based', 'volume_based', 'demand_based'
                    condition_params TEXT, -- JSON
                    price_adjustment REAL NOT NULL, -- percentage adjustment
                    applicable_tiers TEXT, -- JSON array
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def load_regional_configurations(self):
        """Load regional pricing configurations"""
        self.regional_configs = {
            Currency.USD: RegionalPricing(
                currency=Currency.USD,
                country_codes=["US", "PR", "VI"],
                price_multiplier=1.0,
                tax_rate=0.0,  # Sales tax varies by state
                payment_methods=["card", "paypal", "apple_pay", "google_pay"],
                local_features=["USD pricing", "English support"]
            ),
            Currency.EUR: RegionalPricing(
                currency=Currency.EUR,
                country_codes=["DE", "FR", "IT", "ES", "NL", "BE", "AT", "PT", "IE"],
                price_multiplier=0.95,  # Slightly lower due to competition
                tax_rate=0.20,  # Average EU VAT
                payment_methods=["card", "paypal", "sepa", "sofort"],
                local_features=["EUR pricing", "GDPR compliance", "Multi-language"]
            ),
            Currency.GBP: RegionalPricing(
                currency=Currency.GBP,
                country_codes=["GB"],
                price_multiplier=0.92,
                tax_rate=0.20,  # UK VAT
                payment_methods=["card", "paypal", "apple_pay", "google_pay"],
                local_features=["GBP pricing", "UK support"]
            ),
            Currency.INR: RegionalPricing(
                currency=Currency.INR,
                country_codes=["IN"],
                price_multiplier=0.3,  # Purchasing power adjustment
                tax_rate=0.18,  # GST
                payment_methods=["card", "upi", "razorpay", "paytm"],
                local_features=["INR pricing", "Hindi support", "Regional languages"]
            ),
            Currency.CAD: RegionalPricing(
                currency=Currency.CAD,
                country_codes=["CA"],
                price_multiplier=1.05,
                tax_rate=0.13,  # Average Canadian tax
                payment_methods=["card", "paypal", "interac"],
                local_features=["CAD pricing", "Bilingual support"]
            ),
            Currency.BRL: RegionalPricing(
                currency=Currency.BRL,
                country_codes=["BR"],
                price_multiplier=0.4,  # Economic adjustment
                tax_rate=0.15,
                payment_methods=["card", "pix", "boleto"],
                local_features=["BRL pricing", "Portuguese support"]
            )
        }
    
    def _load_base_pricing(self) -> Dict:
        """Load base pricing structure"""
        return {
            PricingTier.FREE: {
                "monthly_price": 0.0,
                "yearly_price": 0.0,
                "credits": 3,
                "features": [
                    "3 video generations per month",
                    "720p quality",
                    "Basic voice options",
                    "Community support"
                ]
            },
            PricingTier.STARTER: {
                "monthly_price": 19.99,
                "yearly_price": 199.99,  # 2 months free
                "credits": 30,
                "features": [
                    "30 video generations per month",
                    "1080p HD quality",
                    "Premium voice options",
                    "Priority support",
                    "Commercial usage rights"
                ]
            },
            PricingTier.PRO: {
                "monthly_price": 49.99,
                "yearly_price": 499.99,  # 2 months free
                "credits": 100,
                "features": [
                    "100 video generations per month",
                    "4K ultra-HD quality",
                    "All voice options + voice cloning",
                    "Priority support",
                    "Commercial usage rights",
                    "Custom branding",
                    "API access"
                ]
            },
            PricingTier.ENTERPRISE: {
                "monthly_price": 199.99,
                "yearly_price": 1999.99,  # 2 months free
                "credits": 500,
                "features": [
                    "500 video generations per month",
                    "4K ultra-HD quality",
                    "All premium features",
                    "Dedicated support",
                    "White-label solution",
                    "Custom integrations",
                    "SLA guarantee"
                ]
            }
        }
    
    def get_regional_price(self, tier: PricingTier, currency: Currency, 
                          country_code: str = None, billing_cycle: str = "monthly") -> Dict:
        """Get price for specific region and currency"""
        try:
            base_price = self.base_pricing[tier]
            price_key = f"{billing_cycle}_price"
            base_amount = base_price[price_key]
            
            if tier == PricingTier.FREE:
                return {
                    "amount": 0.0,
                    "currency": currency.value,
                    "original_amount": 0.0,
                    "tax_amount": 0.0,
                    "total_amount": 0.0
                }
            
            # Get regional configuration
            regional_config = self.regional_configs.get(currency)
            if not regional_config:
                # Fallback to USD
                regional_config = self.regional_configs[Currency.USD]
            
            # Apply regional multiplier
            regional_price = base_amount * regional_config.price_multiplier
            
            # Apply dynamic pricing rules
            dynamic_adjustment = self.calculate_dynamic_pricing(tier, currency, country_code)
            adjusted_price = regional_price * (1 + dynamic_adjustment)
            
            # Calculate tax
            tax_amount = adjusted_price * regional_config.tax_rate
            total_amount = adjusted_price + tax_amount
            
            return {
                "amount": round(adjusted_price, 2),
                "currency": currency.value,
                "original_amount": round(base_amount, 2),
                "tax_amount": round(tax_amount, 2),
                "total_amount": round(total_amount, 2),
                "price_multiplier": regional_config.price_multiplier,
                "tax_rate": regional_config.tax_rate,
                "dynamic_adjustment": dynamic_adjustment
            }
        
        except Exception as e:
            logger.error(f"Failed to calculate regional price: {str(e)}")
            return self._get_fallback_price(tier, billing_cycle)
    
    def calculate_dynamic_pricing(self, tier: PricingTier, currency: Currency, 
                                country_code: str = None) -> float:
        """Calculate dynamic pricing adjustments"""
        try:
            total_adjustment = 0.0
            
            # Time-based pricing (Black Friday, holidays, etc.)
            time_adjustment = self._calculate_time_based_pricing()
            total_adjustment += time_adjustment
            
            # Demand-based pricing
            demand_adjustment = self._calculate_demand_based_pricing(tier)
            total_adjustment += demand_adjustment
            
            # Volume-based pricing (bulk discounts for annual plans)
            volume_adjustment = self._calculate_volume_based_pricing(tier)
            total_adjustment += volume_adjustment
            
            # Limit total adjustment to prevent extreme pricing
            return max(-0.5, min(0.3, total_adjustment))  # -50% to +30%
        
        except Exception as e:
            logger.error(f"Dynamic pricing calculation failed: {str(e)}")
            return 0.0
    
    def _calculate_time_based_pricing(self) -> float:
        """Calculate time-based pricing adjustments"""
        now = datetime.now()
        
        # Black Friday (November 25-29)
        if now.month == 11 and 25 <= now.day <= 29:
            return -0.3  # 30% discount
        
        # New Year promotion (January 1-7)
        if now.month == 1 and 1 <= now.day <= 7:
            return -0.25  # 25% discount
        
        # Summer promotion (July)
        if now.month == 7:
            return -0.15  # 15% discount
        
        # Weekend pricing boost (for premium tiers)
        if now.weekday() >= 5:  # Saturday, Sunday
            return 0.05  # 5% increase
        
        return 0.0
    
    def _calculate_demand_based_pricing(self, tier: PricingTier) -> float:
        """Calculate demand-based pricing adjustments"""
        # Simulate demand calculation
        # In production, this would analyze recent subscription trends
        
        # High demand for Pro tier (example)
        if tier == PricingTier.PRO:
            return 0.1  # 10% increase due to high demand
        
        # Lower demand for Enterprise tier
        if tier == PricingTier.ENTERPRISE:
            return -0.1  # 10% discount to increase adoption
        
        return 0.0
    
    def _calculate_volume_based_pricing(self, tier: PricingTier) -> float:
        """Calculate volume-based pricing adjustments"""
        # Annual plans already have built-in discounts
        # Additional discounts for enterprise tiers
        
        if tier == PricingTier.ENTERPRISE:
            return -0.05  # Additional 5% for enterprise volume
        
        return 0.0
    
    def create_promotional_campaign(self, campaign_data: Dict) -> str:
        """Create new promotional campaign"""
        try:
            campaign_id = f"promo_{int(time.time())}"
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO promotional_campaigns 
                    (campaign_id, name, discount_percentage, discount_amount, 
                     applicable_tiers, start_date, end_date, max_uses, 
                     promo_code, target_regions)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    campaign_id,
                    campaign_data['name'],
                    campaign_data.get('discount_percentage', 0),
                    campaign_data.get('discount_amount', 0),
                    json.dumps(campaign_data.get('applicable_tiers', [])),
                    campaign_data['start_date'],
                    campaign_data['end_date'],
                    campaign_data.get('max_uses', -1),
                    campaign_data.get('promo_code'),
                    json.dumps(campaign_data.get('target_regions', []))
                ))
                conn.commit()
            
            logger.info(f"Created promotional campaign: {campaign_id}")
            return campaign_id
        
        except Exception as e:
            logger.error(f"Failed to create promotional campaign: {str(e)}")
            raise
    
    def apply_promotional_discount(self, promo_code: str, tier: PricingTier, 
                                 amount: float, currency: Currency) -> Dict:
        """Apply promotional discount to price"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT campaign_id, discount_percentage, discount_amount, 
                           applicable_tiers, max_uses, current_uses, start_date, end_date
                    FROM promotional_campaigns 
                    WHERE promo_code = ? AND is_active = 1
                """, (promo_code,))
                
                result = cursor.fetchone()
                
                if not result:
                    return {"success": False, "message": "Invalid promo code"}
                
                (campaign_id, discount_percentage, discount_amount, 
                 applicable_tiers, max_uses, current_uses, start_date, end_date) = result
                
                # Check if campaign is active
                now = datetime.now()
                if now < datetime.fromisoformat(start_date) or now > datetime.fromisoformat(end_date):
                    return {"success": False, "message": "Promo code expired"}
                
                # Check usage limits
                if max_uses > 0 and current_uses >= max_uses:
                    return {"success": False, "message": "Promo code usage limit reached"}
                
                # Check if tier is applicable
                applicable_tier_list = json.loads(applicable_tiers)
                if tier.value not in applicable_tier_list:
                    return {"success": False, "message": "Promo code not applicable to this plan"}
                
                # Calculate discount
                if discount_percentage > 0:
                    discount = amount * (discount_percentage / 100)
                else:
                    discount = discount_amount
                
                # Ensure discount doesn't exceed price
                discount = min(discount, amount)
                final_amount = amount - discount
                
                # Update usage count
                cursor.execute("""
                    UPDATE promotional_campaigns 
                    SET current_uses = current_uses + 1 
                    WHERE campaign_id = ?
                """, (campaign_id,))
                conn.commit()
                
                return {
                    "success": True,
                    "original_amount": amount,
                    "discount_amount": discount,
                    "final_amount": final_amount,
                    "campaign_id": campaign_id
                }
        
        except Exception as e:
            logger.error(f"Failed to apply promotional discount: {str(e)}")
            return {"success": False, "message": "Failed to apply discount"}
    
    def get_optimal_pricing_display(self, user_country: str = None, 
                                  user_currency: str = None) -> Dict:
        """Get optimal pricing display for user's region"""
        try:
            # Determine user's currency
            currency = Currency.USD  # Default
            if user_currency:
                try:
                    currency = Currency(user_currency.lower())
                except ValueError:
                    pass
            
            # Get pricing for all tiers
            pricing_display = {}
            
            for tier in PricingTier:
                monthly_price = self.get_regional_price(tier, currency, user_country, "monthly")
                yearly_price = self.get_regional_price(tier, currency, user_country, "yearly")
                
                # Calculate yearly savings
                yearly_savings = 0
                if monthly_price['total_amount'] > 0 and yearly_price['total_amount'] > 0:
                    annual_monthly_cost = monthly_price['total_amount'] * 12
                    yearly_savings = annual_monthly_cost - yearly_price['total_amount']
                    savings_percentage = (yearly_savings / annual_monthly_cost) * 100
                else:
                    savings_percentage = 0
                
                pricing_display[tier.value] = {
                    "monthly": monthly_price,
                    "yearly": yearly_price,
                    "yearly_savings": round(yearly_savings, 2),
                    "savings_percentage": round(savings_percentage, 0),
                    "credits": self.base_pricing[tier]["credits"],
                    "features": self.base_pricing[tier]["features"]
                }
            
            return pricing_display
        
        except Exception as e:
            logger.error(f"Failed to get optimal pricing display: {str(e)}")
            return self._get_fallback_pricing_display()
    
    def _get_fallback_price(self, tier: PricingTier, billing_cycle: str) -> Dict:
        """Get fallback price in case of errors"""
        base_price = self.base_pricing[tier]
        amount = base_price[f"{billing_cycle}_price"]
        
        return {
            "amount": amount,
            "currency": "usd",
            "original_amount": amount,
            "tax_amount": 0.0,
            "total_amount": amount
        }
    
    def _get_fallback_pricing_display(self) -> Dict:
        """Get fallback pricing display"""
        return {tier.value: {"monthly": self._get_fallback_price(tier, "monthly")} 
                for tier in PricingTier}
    
    def track_pricing_analytics(self, tier: str, currency: str, country_code: str,
                              price_paid: float, original_price: float, 
                              discount_applied: float = 0, campaign_id: str = None,
                              user_id: int = None):
        """Track pricing analytics for optimization"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO pricing_analytics 
                    (tier, currency, country_code, price_paid, original_price, 
                     discount_applied, campaign_id, user_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (tier, currency, country_code, price_paid, original_price,
                      discount_applied, campaign_id, user_id))
                conn.commit()
        
        except Exception as e:
            logger.error(f"Failed to track pricing analytics: {str(e)}")
    
    def get_pricing_recommendations(self, tier: PricingTier, 
                                  user_behavior: Dict = None) -> List[Dict]:
        """Get pricing recommendations based on user behavior"""
        recommendations = []
        
        # Upgrade recommendations
        if tier == PricingTier.FREE:
            recommendations.append({
                "type": "upgrade",
                "target_tier": PricingTier.STARTER.value,
                "message": "Upgrade to Starter for unlimited HD videos",
                "urgency": "medium"
            })
        
        elif tier == PricingTier.STARTER:
            recommendations.append({
                "type": "upgrade",
                "target_tier": PricingTier.PRO.value,
                "message": "Upgrade to Pro for 4K quality and voice cloning",
                "urgency": "medium"
            })
        
        # Annual plan recommendations
        recommendations.append({
            "type": "billing_cycle",
            "target_cycle": "yearly",
            "message": "Save 17% with annual billing",
            "urgency": "low"
        })
        
        # Limited time offers
        now = datetime.now()
        if now.month == 11 and 25 <= now.day <= 29:  # Black Friday
            recommendations.append({
                "type": "promotion",
                "discount": 30,
                "message": "Black Friday: 30% off all plans!",
                "urgency": "high",
                "expires": "November 29th"
            })
        
        return recommendations


# Global pricing strategy instance
pricing_strategy = PricingStrategy()