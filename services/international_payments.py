"""
TalkingPhoto AI MVP - International Payment Support
Multi-currency, tax handling, and regional payment methods
"""

import stripe
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import sqlite3
import logging
from services.pricing_strategy import Currency, PricingTier
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = Config.STRIPE_SECRET_KEY


class PaymentMethod(Enum):
    """Supported payment methods by region"""
    CARD = "card"
    PAYPAL = "paypal"
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"
    SEPA_DEBIT = "sepa_debit"
    SOFORT = "sofort"
    IDEAL = "ideal"
    BANCONTACT = "bancontact"
    UPI = "upi"
    RAZORPAY = "razorpay"
    PAYTM = "paytm"
    PIX = "pix"
    BOLETO = "boleto"
    INTERAC = "interac"
    ALIPAY = "alipay"
    WECHAT_PAY = "wechat_pay"


class TaxType(Enum):
    """Tax types for different regions"""
    VAT = "vat"          # EU VAT
    GST = "gst"          # India GST, Canada GST
    HST = "hst"          # Canada HST
    SALES_TAX = "sales_tax"  # US Sales Tax
    IVA = "iva"          # Brazil IVA
    NONE = "none"        # No tax


@dataclass
class RegionalPaymentConfig:
    """Regional payment configuration"""
    country_code: str
    currency: Currency
    supported_payment_methods: List[PaymentMethod]
    tax_type: TaxType
    tax_rate: float
    tax_id_required: bool
    address_validation: bool
    local_regulations: List[str]
    preferred_languages: List[str]


@dataclass
class TaxCalculation:
    """Tax calculation result"""
    subtotal: float
    tax_amount: float
    tax_rate: float
    tax_type: TaxType
    total: float
    tax_breakdown: Dict[str, float]


@dataclass
class CurrencyExchange:
    """Currency exchange information"""
    from_currency: str
    to_currency: str
    rate: float
    provider: str
    timestamp: datetime


class InternationalPaymentService:
    """
    International payment service with multi-currency support
    Handles taxes, exchange rates, and regional payment methods
    """
    
    def __init__(self):
        self.db_path = "data/international_payments.db"
        self.init_database()
        self.regional_configs = self._load_regional_configurations()
        self.supported_countries = list(self.regional_configs.keys())
    
    def init_database(self):
        """Initialize international payments database"""
        import os
        os.makedirs("data", exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Currency exchange rates table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS exchange_rates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_currency TEXT NOT NULL,
                    to_currency TEXT NOT NULL,
                    rate REAL NOT NULL,
                    provider TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(from_currency, to_currency, provider)
                )
            """)
            
            # Tax calculations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tax_calculations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payment_id TEXT,
                    country_code TEXT NOT NULL,
                    tax_type TEXT NOT NULL,
                    subtotal REAL NOT NULL,
                    tax_rate REAL NOT NULL,
                    tax_amount REAL NOT NULL,
                    total_amount REAL NOT NULL,
                    tax_breakdown TEXT, -- JSON
                    tax_id_number TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Regional payment attempts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS regional_payment_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_email TEXT NOT NULL,
                    country_code TEXT NOT NULL,
                    payment_method TEXT NOT NULL,
                    currency TEXT NOT NULL,
                    amount REAL NOT NULL,
                    status TEXT NOT NULL, -- 'succeeded', 'failed', 'requires_action'
                    failure_reason TEXT,
                    stripe_payment_intent_id TEXT,
                    metadata TEXT, -- JSON
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Country compliance tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS compliance_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    country_code TEXT NOT NULL,
                    regulation_type TEXT NOT NULL,
                    compliance_status TEXT NOT NULL, -- 'compliant', 'non_compliant', 'pending'
                    last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(country_code, regulation_type)
                )
            """)
            
            conn.commit()
    
    def _load_regional_configurations(self) -> Dict[str, RegionalPaymentConfig]:
        """Load regional payment configurations"""
        return {
            # United States
            "US": RegionalPaymentConfig(
                country_code="US",
                currency=Currency.USD,
                supported_payment_methods=[
                    PaymentMethod.CARD, PaymentMethod.PAYPAL, 
                    PaymentMethod.APPLE_PAY, PaymentMethod.GOOGLE_PAY
                ],
                tax_type=TaxType.SALES_TAX,
                tax_rate=0.0,  # Varies by state
                tax_id_required=False,
                address_validation=True,
                local_regulations=["PCI DSS", "State Sales Tax"],
                preferred_languages=["en"]
            ),
            
            # Germany
            "DE": RegionalPaymentConfig(
                country_code="DE",
                currency=Currency.EUR,
                supported_payment_methods=[
                    PaymentMethod.CARD, PaymentMethod.PAYPAL, PaymentMethod.SEPA_DEBIT,
                    PaymentMethod.SOFORT, PaymentMethod.APPLE_PAY, PaymentMethod.GOOGLE_PAY
                ],
                tax_type=TaxType.VAT,
                tax_rate=0.19,  # German VAT
                tax_id_required=True,
                address_validation=True,
                local_regulations=["GDPR", "PSD2", "German Tax Law"],
                preferred_languages=["de", "en"]
            ),
            
            # United Kingdom
            "GB": RegionalPaymentConfig(
                country_code="GB",
                currency=Currency.GBP,
                supported_payment_methods=[
                    PaymentMethod.CARD, PaymentMethod.PAYPAL, 
                    PaymentMethod.APPLE_PAY, PaymentMethod.GOOGLE_PAY
                ],
                tax_type=TaxType.VAT,
                tax_rate=0.20,  # UK VAT
                tax_id_required=True,
                address_validation=True,
                local_regulations=["GDPR", "UK Tax Law"],
                preferred_languages=["en"]
            ),
            
            # India
            "IN": RegionalPaymentConfig(
                country_code="IN",
                currency=Currency.INR,
                supported_payment_methods=[
                    PaymentMethod.CARD, PaymentMethod.UPI, PaymentMethod.RAZORPAY,
                    PaymentMethod.PAYTM, PaymentMethod.GOOGLE_PAY
                ],
                tax_type=TaxType.GST,
                tax_rate=0.18,  # Indian GST
                tax_id_required=True,
                address_validation=True,
                local_regulations=["RBI Guidelines", "GST Law", "IT Act"],
                preferred_languages=["en", "hi", "ta", "te", "bn", "mr", "gu"]
            ),
            
            # Canada
            "CA": RegionalPaymentConfig(
                country_code="CA",
                currency=Currency.CAD,
                supported_payment_methods=[
                    PaymentMethod.CARD, PaymentMethod.PAYPAL, PaymentMethod.INTERAC,
                    PaymentMethod.APPLE_PAY, PaymentMethod.GOOGLE_PAY
                ],
                tax_type=TaxType.HST,  # Varies by province
                tax_rate=0.13,  # Average HST
                tax_id_required=True,
                address_validation=True,
                local_regulations=["Privacy Act", "Provincial Tax Laws"],
                preferred_languages=["en", "fr"]
            ),
            
            # Brazil
            "BR": RegionalPaymentConfig(
                country_code="BR",
                currency=Currency.BRL,
                supported_payment_methods=[
                    PaymentMethod.CARD, PaymentMethod.PIX, PaymentMethod.BOLETO
                ],
                tax_type=TaxType.IVA,
                tax_rate=0.15,
                tax_id_required=True,
                address_validation=True,
                local_regulations=["LGPD", "Brazilian Tax Law"],
                preferred_languages=["pt"]
            ),
            
            # Netherlands
            "NL": RegionalPaymentConfig(
                country_code="NL",
                currency=Currency.EUR,
                supported_payment_methods=[
                    PaymentMethod.CARD, PaymentMethod.IDEAL, PaymentMethod.SEPA_DEBIT,
                    PaymentMethod.PAYPAL, PaymentMethod.APPLE_PAY
                ],
                tax_type=TaxType.VAT,
                tax_rate=0.21,  # Dutch VAT
                tax_id_required=True,
                address_validation=True,
                local_regulations=["GDPR", "PSD2", "Dutch Tax Law"],
                preferred_languages=["nl", "en"]
            ),
            
            # France
            "FR": RegionalPaymentConfig(
                country_code="FR",
                currency=Currency.EUR,
                supported_payment_methods=[
                    PaymentMethod.CARD, PaymentMethod.SEPA_DEBIT, PaymentMethod.PAYPAL,
                    PaymentMethod.APPLE_PAY, PaymentMethod.GOOGLE_PAY
                ],
                tax_type=TaxType.VAT,
                tax_rate=0.20,  # French VAT
                tax_id_required=True,
                address_validation=True,
                local_regulations=["GDPR", "French Tax Law"],
                preferred_languages=["fr", "en"]
            ),
            
            # Belgium
            "BE": RegionalPaymentConfig(
                country_code="BE",
                currency=Currency.EUR,
                supported_payment_methods=[
                    PaymentMethod.CARD, PaymentMethod.BANCONTACT, PaymentMethod.SEPA_DEBIT,
                    PaymentMethod.PAYPAL, PaymentMethod.APPLE_PAY
                ],
                tax_type=TaxType.VAT,
                tax_rate=0.21,  # Belgian VAT
                tax_id_required=True,
                address_validation=True,
                local_regulations=["GDPR", "Belgian Tax Law"],
                preferred_languages=["nl", "fr", "de", "en"]
            ),
            
            # Australia
            "AU": RegionalPaymentConfig(
                country_code="AU",
                currency=Currency.AUD,
                supported_payment_methods=[
                    PaymentMethod.CARD, PaymentMethod.PAYPAL,
                    PaymentMethod.APPLE_PAY, PaymentMethod.GOOGLE_PAY
                ],
                tax_type=TaxType.GST,
                tax_rate=0.10,  # Australian GST
                tax_id_required=True,
                address_validation=True,
                local_regulations=["Privacy Act", "Australian Tax Law"],
                preferred_languages=["en"]
            )
        }
    
    def detect_customer_country(self, ip_address: str = None, 
                              billing_address: Dict = None) -> str:
        """Detect customer's country for payment processing"""
        try:
            # Priority: billing address > IP geolocation > default
            if billing_address and billing_address.get('country'):
                return billing_address['country'].upper()
            
            if ip_address:
                # Use IP geolocation service (implement with real service)
                country = self._get_country_from_ip(ip_address)
                if country:
                    return country.upper()
            
            # Default to US
            return "US"
        
        except Exception as e:
            logger.error(f"Failed to detect customer country: {str(e)}")
            return "US"
    
    def _get_country_from_ip(self, ip_address: str) -> Optional[str]:
        """Get country from IP address (implement with real geolocation service)"""
        try:
            # This is a placeholder - implement with real geolocation service
            # Examples: MaxMind GeoIP2, IPStack, ip-api.com
            response = requests.get(f"http://ip-api.com/json/{ip_address}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get('countryCode')
        except Exception as e:
            logger.error(f"IP geolocation failed: {str(e)}")
        
        return None
    
    def get_supported_payment_methods(self, country_code: str) -> List[str]:
        """Get supported payment methods for country"""
        config = self.regional_configs.get(country_code)
        if config:
            return [method.value for method in config.supported_payment_methods]
        
        # Default payment methods
        return [PaymentMethod.CARD.value, PaymentMethod.PAYPAL.value]
    
    def calculate_tax(self, amount: float, country_code: str, 
                     customer_type: str = "individual", 
                     tax_id: str = None) -> TaxCalculation:
        """Calculate tax for international payments"""
        try:
            config = self.regional_configs.get(country_code)
            if not config:
                # No tax for unsupported countries
                return TaxCalculation(
                    subtotal=amount,
                    tax_amount=0.0,
                    tax_rate=0.0,
                    tax_type=TaxType.NONE,
                    total=amount,
                    tax_breakdown={}
                )
            
            # Check for tax exemptions
            if self._is_tax_exempt(country_code, customer_type, tax_id):
                return TaxCalculation(
                    subtotal=amount,
                    tax_amount=0.0,
                    tax_rate=0.0,
                    tax_type=config.tax_type,
                    total=amount,
                    tax_breakdown={"exempt": True}
                )
            
            # Calculate tax
            tax_rate = config.tax_rate
            
            # Special handling for US (state-specific tax)
            if country_code == "US":
                tax_rate = self._get_us_state_tax_rate(tax_id)
            
            # Special handling for Canada (province-specific tax)
            elif country_code == "CA":
                tax_rate = self._get_canada_province_tax_rate(tax_id)
            
            tax_amount = amount * tax_rate
            total = amount + tax_amount
            
            # Create tax breakdown
            tax_breakdown = {
                config.tax_type.value: tax_amount
            }
            
            # Store tax calculation
            self._store_tax_calculation(
                country_code=country_code,
                tax_type=config.tax_type,
                subtotal=amount,
                tax_rate=tax_rate,
                tax_amount=tax_amount,
                total_amount=total,
                tax_breakdown=tax_breakdown,
                tax_id_number=tax_id
            )
            
            return TaxCalculation(
                subtotal=amount,
                tax_amount=tax_amount,
                tax_rate=tax_rate,
                tax_type=config.tax_type,
                total=total,
                tax_breakdown=tax_breakdown
            )
        
        except Exception as e:
            logger.error(f"Tax calculation failed: {str(e)}")
            # Return without tax on error
            return TaxCalculation(
                subtotal=amount,
                tax_amount=0.0,
                tax_rate=0.0,
                tax_type=TaxType.NONE,
                total=amount,
                tax_breakdown={"error": True}
            )
    
    def _is_tax_exempt(self, country_code: str, customer_type: str, tax_id: str) -> bool:
        """Check if customer is tax exempt"""
        # B2B transactions with valid tax ID in EU
        if country_code in ["DE", "FR", "NL", "BE", "IT", "ES"] and customer_type == "business" and tax_id:
            return self._validate_eu_vat_number(tax_id)
        
        return False
    
    def _validate_eu_vat_number(self, vat_number: str) -> bool:
        """Validate EU VAT number (implement with real validation service)"""
        # Placeholder - implement with EU VAT validation service
        return len(vat_number) > 8 and vat_number.startswith(('DE', 'FR', 'NL', 'BE'))
    
    def _get_us_state_tax_rate(self, state_code: str) -> float:
        """Get US state tax rate"""
        # Simplified state tax rates
        state_rates = {
            'CA': 0.0975,  # California
            'NY': 0.08,    # New York
            'TX': 0.0625,  # Texas
            'FL': 0.06,    # Florida
            'WA': 0.065,   # Washington
            'OR': 0.0,     # Oregon (no sales tax)
            'MT': 0.0,     # Montana (no sales tax)
            'NH': 0.0,     # New Hampshire (no sales tax)
            'DE': 0.0,     # Delaware (no sales tax)
        }
        
        return state_rates.get(state_code, 0.05)  # Default 5%
    
    def _get_canada_province_tax_rate(self, province_code: str) -> float:
        """Get Canada province tax rate"""
        # Simplified province tax rates
        province_rates = {
            'ON': 0.13,    # Ontario HST
            'BC': 0.12,    # British Columbia PST + GST
            'QC': 0.14975, # Quebec GST + QST
            'AB': 0.05,    # Alberta GST only
            'SK': 0.11,    # Saskatchewan PST + GST
            'MB': 0.12,    # Manitoba PST + GST
            'NS': 0.15,    # Nova Scotia HST
            'NB': 0.15,    # New Brunswick HST
            'NL': 0.15,    # Newfoundland HST
            'PE': 0.15,    # Prince Edward Island HST
        }
        
        return province_rates.get(province_code, 0.13)  # Default HST
    
    def get_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        """Get current exchange rate"""
        try:
            if from_currency == to_currency:
                return 1.0
            
            # Check cached rate (within 1 hour)
            cached_rate = self._get_cached_exchange_rate(from_currency, to_currency)
            if cached_rate:
                return cached_rate
            
            # Fetch new rate from external API
            rate = self._fetch_exchange_rate(from_currency, to_currency)
            if rate:
                self._cache_exchange_rate(from_currency, to_currency, rate)
                return rate
            
            # Fallback rates (update these regularly)
            fallback_rates = {
                ('USD', 'EUR'): 0.85,
                ('USD', 'GBP'): 0.75,
                ('USD', 'INR'): 83.0,
                ('USD', 'CAD'): 1.35,
                ('USD', 'AUD'): 1.55,
                ('USD', 'BRL'): 5.2,
                ('EUR', 'USD'): 1.18,
                ('GBP', 'USD'): 1.33,
            }
            
            return fallback_rates.get((from_currency, to_currency), 1.0)
        
        except Exception as e:
            logger.error(f"Exchange rate lookup failed: {str(e)}")
            return 1.0
    
    def _get_cached_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """Get cached exchange rate if recent"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT rate FROM exchange_rates 
                    WHERE from_currency = ? AND to_currency = ? 
                    AND created_at > datetime('now', '-1 hour')
                    ORDER BY created_at DESC LIMIT 1
                """, (from_currency, to_currency))
                
                result = cursor.fetchone()
                return result[0] if result else None
        
        except Exception as e:
            logger.error(f"Failed to get cached exchange rate: {str(e)}")
            return None
    
    def _fetch_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """Fetch exchange rate from external API"""
        try:
            # Use a free exchange rate API (implement with real service)
            # Examples: exchangerate-api.com, fixer.io, currencylayer.com
            
            api_url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
            response = requests.get(api_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                rates = data.get('rates', {})
                return rates.get(to_currency)
        
        except Exception as e:
            logger.error(f"Failed to fetch exchange rate: {str(e)}")
        
        return None
    
    def _cache_exchange_rate(self, from_currency: str, to_currency: str, rate: float):
        """Cache exchange rate"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO exchange_rates 
                    (from_currency, to_currency, rate, provider)
                    VALUES (?, ?, ?, 'api')
                """, (from_currency, to_currency, rate))
                conn.commit()
        
        except Exception as e:
            logger.error(f"Failed to cache exchange rate: {str(e)}")
    
    def create_international_payment_intent(self, customer_data: Dict, 
                                          payment_data: Dict) -> Dict:
        """Create payment intent with international support"""
        try:
            # Detect customer country
            country_code = self.detect_customer_country(
                ip_address=customer_data.get('ip_address'),
                billing_address=customer_data.get('billing_address')
            )
            
            # Get regional configuration
            config = self.regional_configs.get(country_code)
            if not config:
                return {"success": False, "message": f"Country {country_code} not supported"}
            
            # Calculate tax
            tax_calculation = self.calculate_tax(
                amount=payment_data['amount'],
                country_code=country_code,
                customer_type=customer_data.get('customer_type', 'individual'),
                tax_id=customer_data.get('tax_id')
            )
            
            # Convert currency if needed
            base_amount = payment_data['amount']
            target_currency = config.currency.value
            
            if payment_data.get('currency', 'USD').lower() != target_currency.lower():
                exchange_rate = self.get_exchange_rate(
                    payment_data.get('currency', 'USD').upper(),
                    target_currency.upper()
                )
                base_amount = base_amount * exchange_rate
            
            # Create Stripe payment intent
            payment_intent_data = {
                'amount': int(tax_calculation.total * 100),  # Convert to cents
                'currency': target_currency.lower(),
                'customer': customer_data.get('stripe_customer_id'),
                'payment_method_types': self.get_supported_payment_methods(country_code),
                'metadata': {
                    'country_code': country_code,
                    'tax_amount': str(tax_calculation.tax_amount),
                    'tax_rate': str(tax_calculation.tax_rate),
                    'tax_type': tax_calculation.tax_type.value,
                    'original_amount': str(payment_data['amount']),
                    'original_currency': payment_data.get('currency', 'USD')
                }
            }
            
            # Add automatic tax handling if supported
            if config.tax_type != TaxType.NONE:
                payment_intent_data['automatic_tax'] = {'enabled': True}
            
            # Create payment intent
            payment_intent = stripe.PaymentIntent.create(**payment_intent_data)
            
            # Record payment attempt
            self._record_payment_attempt(
                customer_email=customer_data.get('email'),
                country_code=country_code,
                payment_method='card',  # Default, will be updated based on actual method
                currency=target_currency,
                amount=tax_calculation.total,
                status='created',
                stripe_payment_intent_id=payment_intent.id,
                metadata={
                    'tax_calculation': tax_calculation.__dict__,
                    'config': config.__dict__
                }
            )
            
            return {
                "success": True,
                "payment_intent": payment_intent,
                "tax_calculation": tax_calculation,
                "supported_payment_methods": self.get_supported_payment_methods(country_code),
                "country_config": config
            }
        
        except Exception as e:
            logger.error(f"Failed to create international payment intent: {str(e)}")
            return {"success": False, "message": str(e)}
    
    def validate_international_address(self, address: Dict, country_code: str) -> Dict:
        """Validate international address"""
        try:
            config = self.regional_configs.get(country_code)
            if not config or not config.address_validation:
                return {"valid": True, "normalized_address": address}
            
            # Basic validation rules by country
            validation_rules = {
                "US": self._validate_us_address,
                "CA": self._validate_canada_address,
                "GB": self._validate_uk_address,
                "DE": self._validate_germany_address,
                "IN": self._validate_india_address
            }
            
            validator = validation_rules.get(country_code)
            if validator:
                return validator(address)
            
            # Default validation
            required_fields = ['line1', 'city', 'postal_code', 'country']
            missing_fields = [field for field in required_fields if not address.get(field)]
            
            if missing_fields:
                return {
                    "valid": False,
                    "errors": [f"Missing required field: {field}" for field in missing_fields]
                }
            
            return {"valid": True, "normalized_address": address}
        
        except Exception as e:
            logger.error(f"Address validation failed: {str(e)}")
            return {"valid": False, "errors": ["Address validation failed"]}
    
    def _validate_us_address(self, address: Dict) -> Dict:
        """Validate US address"""
        # Implement US-specific address validation
        if not address.get('state'):
            return {"valid": False, "errors": ["State is required for US addresses"]}
        
        # Validate ZIP code format
        postal_code = address.get('postal_code', '')
        if not (len(postal_code) == 5 or len(postal_code) == 10):
            return {"valid": False, "errors": ["Invalid US ZIP code format"]}
        
        return {"valid": True, "normalized_address": address}
    
    def _validate_canada_address(self, address: Dict) -> Dict:
        """Validate Canada address"""
        if not address.get('state'):  # Province
            return {"valid": False, "errors": ["Province is required for Canadian addresses"]}
        
        # Validate postal code format (A1A 1A1)
        postal_code = address.get('postal_code', '').replace(' ', '').upper()
        if len(postal_code) != 6:
            return {"valid": False, "errors": ["Invalid Canadian postal code format"]}
        
        return {"valid": True, "normalized_address": address}
    
    def _validate_uk_address(self, address: Dict) -> Dict:
        """Validate UK address"""
        # UK postcodes are complex, basic validation
        postal_code = address.get('postal_code', '')
        if len(postal_code) < 5 or len(postal_code) > 8:
            return {"valid": False, "errors": ["Invalid UK postcode format"]}
        
        return {"valid": True, "normalized_address": address}
    
    def _validate_germany_address(self, address: Dict) -> Dict:
        """Validate Germany address"""
        # German postal codes are 5 digits
        postal_code = address.get('postal_code', '')
        if not postal_code.isdigit() or len(postal_code) != 5:
            return {"valid": False, "errors": ["Invalid German postal code format"]}
        
        return {"valid": True, "normalized_address": address}
    
    def _validate_india_address(self, address: Dict) -> Dict:
        """Validate India address"""
        if not address.get('state'):
            return {"valid": False, "errors": ["State is required for Indian addresses"]}
        
        # Indian PIN codes are 6 digits
        postal_code = address.get('postal_code', '')
        if not postal_code.isdigit() or len(postal_code) != 6:
            return {"valid": False, "errors": ["Invalid Indian PIN code format"]}
        
        return {"valid": True, "normalized_address": address}
    
    def get_compliance_requirements(self, country_code: str) -> List[str]:
        """Get compliance requirements for country"""
        config = self.regional_configs.get(country_code)
        return config.local_regulations if config else []
    
    def _store_tax_calculation(self, **kwargs):
        """Store tax calculation in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO tax_calculations 
                    (country_code, tax_type, subtotal, tax_rate, tax_amount, 
                     total_amount, tax_breakdown, tax_id_number)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    kwargs['country_code'], kwargs['tax_type'].value, kwargs['subtotal'],
                    kwargs['tax_rate'], kwargs['tax_amount'], kwargs['total_amount'],
                    json.dumps(kwargs['tax_breakdown']), kwargs.get('tax_id_number')
                ))
                conn.commit()
        
        except Exception as e:
            logger.error(f"Failed to store tax calculation: {str(e)}")
    
    def _record_payment_attempt(self, **kwargs):
        """Record international payment attempt"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO regional_payment_attempts 
                    (customer_email, country_code, payment_method, currency, 
                     amount, status, stripe_payment_intent_id, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    kwargs['customer_email'], kwargs['country_code'], kwargs['payment_method'],
                    kwargs['currency'], kwargs['amount'], kwargs['status'],
                    kwargs['stripe_payment_intent_id'], json.dumps(kwargs['metadata'])
                ))
                conn.commit()
        
        except Exception as e:
            logger.error(f"Failed to record payment attempt: {str(e)}")


# Global international payment service instance
international_payment_service = InternationalPaymentService()