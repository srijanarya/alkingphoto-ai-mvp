"""
TalkingPhoto AI MVP - Security Service
PCI DSS compliance, fraud detection, and payment security
"""

import hashlib
import hmac
import secrets
import re
import json
import time
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import ipaddress
import requests
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security levels for different operations"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(Enum):
    """Types of security threats"""
    FRAUD = "fraud"
    BRUTE_FORCE = "brute_force"
    CARD_TESTING = "card_testing"
    VELOCITY_ABUSE = "velocity_abuse"
    SUSPICIOUS_LOCATION = "suspicious_location"
    INVALID_CVV = "invalid_cvv"
    CHARGEBACK_RISK = "chargeback_risk"


@dataclass
class SecurityRule:
    """Security rule configuration"""
    rule_id: str
    name: str
    threat_type: ThreatType
    condition: str
    threshold: float
    action: str  # 'block', 'challenge', 'monitor'
    is_active: bool
    severity: SecurityLevel


@dataclass
class FraudSignal:
    """Fraud detection signal"""
    signal_type: str
    value: float
    threshold: float
    weight: float
    description: str


class SecurityService:
    """
    Comprehensive security service for payment processing
    Implements PCI DSS compliance and fraud detection
    """
    
    def __init__(self):
        self.db_path = "data/security.db"
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        self.init_database()
        self.security_rules = self._load_security_rules()
        self.blocked_ips = set()
        self.rate_limits = {}
    
    def init_database(self):
        """Initialize security database"""
        import os
        os.makedirs("data", exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Security events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS security_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    threat_type TEXT,
                    severity TEXT NOT NULL,
                    user_id INTEGER,
                    ip_address TEXT,
                    user_agent TEXT,
                    event_data TEXT, -- JSON
                    fraud_score REAL DEFAULT 0,
                    action_taken TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Fraud detection signals table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fraud_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    session_id TEXT,
                    signal_type TEXT NOT NULL,
                    signal_value REAL NOT NULL,
                    threshold_value REAL NOT NULL,
                    weight REAL DEFAULT 1.0,
                    payment_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Blocked entities table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blocked_entities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_type TEXT NOT NULL, -- 'ip', 'email', 'card_fingerprint'
                    entity_value TEXT NOT NULL,
                    reason TEXT,
                    blocked_until TIMESTAMP,
                    is_permanent INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Rate limiting table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rate_limits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_type TEXT NOT NULL,
                    entity_value TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    attempt_count INTEGER DEFAULT 1,
                    window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_attempt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # PCI compliance audit table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pci_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    user_id INTEGER,
                    data_accessed TEXT, -- What PCI data was accessed
                    access_method TEXT,
                    ip_address TEXT,
                    compliance_status TEXT,
                    audit_trail TEXT, -- JSON
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for sensitive data"""
        key_file = "data/.encryption_key"
        
        try:
            with open(key_file, 'rb') as f:
                return f.read()
        except FileNotFoundError:
            # Generate new key
            password = Config.SECRET_KEY.encode()
            salt = secrets.token_bytes(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password))
            
            # Save key securely
            import os
            os.makedirs("data", exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key)
            
            # Set restrictive permissions
            os.chmod(key_file, 0o600)
            
            return key
    
    def _load_security_rules(self) -> List[SecurityRule]:
        """Load security rules configuration"""
        return [
            SecurityRule(
                rule_id="velocity_check",
                name="Payment Velocity Check",
                threat_type=ThreatType.VELOCITY_ABUSE,
                condition="payments_per_hour > 5",
                threshold=5.0,
                action="challenge",
                is_active=True,
                severity=SecurityLevel.MEDIUM
            ),
            SecurityRule(
                rule_id="card_testing",
                name="Card Testing Detection",
                threat_type=ThreatType.CARD_TESTING,
                condition="failed_payments_per_hour > 3",
                threshold=3.0,
                action="block",
                is_active=True,
                severity=SecurityLevel.HIGH
            ),
            SecurityRule(
                rule_id="suspicious_location",
                name="Suspicious Location Check",
                threat_type=ThreatType.SUSPICIOUS_LOCATION,
                condition="location_risk_score > 0.7",
                threshold=0.7,
                action="challenge",
                is_active=True,
                severity=SecurityLevel.MEDIUM
            ),
            SecurityRule(
                rule_id="fraud_score",
                name="Overall Fraud Score",
                threat_type=ThreatType.FRAUD,
                condition="fraud_score > 0.8",
                threshold=0.8,
                action="block",
                is_active=True,
                severity=SecurityLevel.CRITICAL
            ),
            SecurityRule(
                rule_id="brute_force",
                name="Brute Force Protection",
                threat_type=ThreatType.BRUTE_FORCE,
                condition="failed_attempts_per_hour > 10",
                threshold=10.0,
                action="block",
                is_active=True,
                severity=SecurityLevel.HIGH
            )
        ]
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data for PCI compliance"""
        try:
            encrypted_data = self.cipher.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.cipher.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise
    
    def validate_payment_request(self, request_data: Dict, user_id: int = None, 
                                ip_address: str = None) -> Dict:
        """Validate payment request for security threats"""
        try:
            validation_result = {
                "is_valid": True,
                "fraud_score": 0.0,
                "security_actions": [],
                "risk_factors": [],
                "recommendation": "allow"
            }
            
            # Collect fraud signals
            fraud_signals = self._collect_fraud_signals(request_data, user_id, ip_address)
            
            # Calculate fraud score
            fraud_score = self._calculate_fraud_score(fraud_signals)
            validation_result["fraud_score"] = fraud_score
            
            # Apply security rules
            for rule in self.security_rules:
                if not rule.is_active:
                    continue
                
                rule_triggered = self._evaluate_security_rule(rule, fraud_signals, request_data)
                
                if rule_triggered:
                    validation_result["security_actions"].append({
                        "rule": rule.name,
                        "action": rule.action,
                        "severity": rule.severity.value
                    })
                    
                    if rule.action == "block":
                        validation_result["is_valid"] = False
                        validation_result["recommendation"] = "block"
                    elif rule.action == "challenge":
                        validation_result["recommendation"] = "challenge"
            
            # Store fraud signals
            self._store_fraud_signals(fraud_signals, user_id)
            
            # Log security event
            self._log_security_event(
                event_type="payment_validation",
                severity=SecurityLevel.MEDIUM if fraud_score > 0.5 else SecurityLevel.LOW,
                user_id=user_id,
                ip_address=ip_address,
                event_data=request_data,
                fraud_score=fraud_score
            )
            
            return validation_result
        
        except Exception as e:
            logger.error(f"Payment validation failed: {str(e)}")
            return {
                "is_valid": False,
                "fraud_score": 1.0,
                "security_actions": [],
                "risk_factors": ["validation_error"],
                "recommendation": "block"
            }
    
    def _collect_fraud_signals(self, request_data: Dict, user_id: int = None, 
                             ip_address: str = None) -> List[FraudSignal]:
        """Collect fraud detection signals"""
        signals = []
        
        # Velocity signals
        if user_id:
            payment_velocity = self._get_payment_velocity(user_id)
            signals.append(FraudSignal(
                signal_type="payment_velocity",
                value=payment_velocity,
                threshold=5.0,
                weight=0.3,
                description=f"Payments per hour: {payment_velocity}"
            ))
        
        # IP reputation signals
        if ip_address:
            ip_risk_score = self._get_ip_risk_score(ip_address)
            signals.append(FraudSignal(
                signal_type="ip_reputation",
                value=ip_risk_score,
                threshold=0.7,
                weight=0.4,
                description=f"IP risk score: {ip_risk_score}"
            ))
        
        # Device fingerprint signals
        device_fingerprint = request_data.get('device_fingerprint')
        if device_fingerprint:
            device_risk = self._analyze_device_fingerprint(device_fingerprint)
            signals.append(FraudSignal(
                signal_type="device_risk",
                value=device_risk,
                threshold=0.6,
                weight=0.2,
                description=f"Device risk: {device_risk}"
            ))
        
        # Time-based signals
        time_risk = self._analyze_time_patterns(user_id)
        signals.append(FraudSignal(
            signal_type="time_pattern",
            value=time_risk,
            threshold=0.5,
            weight=0.1,
            description=f"Time pattern risk: {time_risk}"
        ))
        
        return signals
    
    def _calculate_fraud_score(self, signals: List[FraudSignal]) -> float:
        """Calculate overall fraud score from signals"""
        total_score = 0.0
        total_weight = 0.0
        
        for signal in signals:
            if signal.value > signal.threshold:
                normalized_score = min(signal.value / signal.threshold, 2.0)
                weighted_score = normalized_score * signal.weight
                total_score += weighted_score
                total_weight += signal.weight
        
        if total_weight > 0:
            return min(total_score / total_weight, 1.0)
        else:
            return 0.0
    
    def _evaluate_security_rule(self, rule: SecurityRule, signals: List[FraudSignal], 
                               request_data: Dict) -> bool:
        """Evaluate if security rule is triggered"""
        if rule.threat_type == ThreatType.VELOCITY_ABUSE:
            velocity_signal = next((s for s in signals if s.signal_type == "payment_velocity"), None)
            return velocity_signal and velocity_signal.value > rule.threshold
        
        elif rule.threat_type == ThreatType.FRAUD:
            fraud_score = self._calculate_fraud_score(signals)
            return fraud_score > rule.threshold
        
        elif rule.threat_type == ThreatType.SUSPICIOUS_LOCATION:
            ip_signal = next((s for s in signals if s.signal_type == "ip_reputation"), None)
            return ip_signal and ip_signal.value > rule.threshold
        
        elif rule.threat_type == ThreatType.CARD_TESTING:
            # Check for card testing patterns
            return self._detect_card_testing_pattern(request_data)
        
        return False
    
    def _get_payment_velocity(self, user_id: int) -> float:
        """Get payment velocity for user (payments per hour)"""
        try:
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM fraud_signals 
                    WHERE user_id = ? AND signal_type = 'payment_attempt' 
                    AND created_at > ?
                """, (user_id, one_hour_ago))
                
                result = cursor.fetchone()
                return result[0] if result else 0.0
        
        except Exception as e:
            logger.error(f"Failed to get payment velocity: {str(e)}")
            return 0.0
    
    def _get_ip_risk_score(self, ip_address: str) -> float:
        """Get IP reputation risk score"""
        try:
            # Check if IP is in private ranges
            ip = ipaddress.ip_address(ip_address)
            if ip.is_private:
                return 0.1  # Low risk for private IPs
            
            # Check against known threat feeds (implement with real services)
            # For demo, simulate risk based on IP characteristics
            
            # Simple heuristics
            risk_score = 0.0
            
            # Check if IP is frequently changing
            if self._is_ip_frequently_changing(ip_address):
                risk_score += 0.3
            
            # Check geographic consistency
            if self._is_geographic_inconsistency(ip_address):
                risk_score += 0.4
            
            # Check if IP is known proxy/VPN
            if self._is_proxy_or_vpn(ip_address):
                risk_score += 0.5
            
            return min(risk_score, 1.0)
        
        except Exception as e:
            logger.error(f"IP risk analysis failed: {str(e)}")
            return 0.5  # Medium risk on error
    
    def _analyze_device_fingerprint(self, device_fingerprint: str) -> float:
        """Analyze device fingerprint for risk"""
        try:
            # Simple device fingerprint analysis
            # In production, use advanced device fingerprinting
            
            risk_score = 0.0
            
            # Check for suspicious user agents
            if 'bot' in device_fingerprint.lower() or 'crawler' in device_fingerprint.lower():
                risk_score += 0.8
            
            # Check for common automation tools
            automation_indicators = ['selenium', 'phantomjs', 'headless', 'automation']
            if any(indicator in device_fingerprint.lower() for indicator in automation_indicators):
                risk_score += 0.7
            
            return min(risk_score, 1.0)
        
        except Exception as e:
            logger.error(f"Device fingerprint analysis failed: {str(e)}")
            return 0.0
    
    def _analyze_time_patterns(self, user_id: int) -> float:
        """Analyze time-based patterns for anomalies"""
        try:
            # Check for unusual activity times
            current_hour = datetime.now().hour
            
            # Higher risk for activity between 2-6 AM
            if 2 <= current_hour <= 6:
                return 0.6
            
            # Check for rapid successive attempts
            if user_id:
                recent_attempts = self._get_recent_attempts(user_id, minutes=5)
                if recent_attempts > 3:
                    return 0.8
            
            return 0.1
        
        except Exception as e:
            logger.error(f"Time pattern analysis failed: {str(e)}")
            return 0.0
    
    def _detect_card_testing_pattern(self, request_data: Dict) -> bool:
        """Detect card testing patterns"""
        # Look for rapid small-amount transactions
        # Multiple cards from same IP
        # Rapid-fire attempts with different CVV codes
        
        # Placeholder implementation
        return False
    
    def _store_fraud_signals(self, signals: List[FraudSignal], user_id: int = None):
        """Store fraud signals for analysis"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for signal in signals:
                    cursor.execute("""
                        INSERT INTO fraud_signals 
                        (user_id, signal_type, signal_value, threshold_value, weight)
                        VALUES (?, ?, ?, ?, ?)
                    """, (user_id, signal.signal_type, signal.value, 
                          signal.threshold, signal.weight))
                
                conn.commit()
        
        except Exception as e:
            logger.error(f"Failed to store fraud signals: {str(e)}")
    
    def _log_security_event(self, event_type: str, severity: SecurityLevel,
                           user_id: int = None, ip_address: str = None,
                           event_data: Dict = None, fraud_score: float = 0.0,
                           action_taken: str = None):
        """Log security event"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO security_events 
                    (event_type, severity, user_id, ip_address, event_data, 
                     fraud_score, action_taken)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (event_type, severity.value, user_id, ip_address,
                      json.dumps(event_data) if event_data else None,
                      fraud_score, action_taken))
                conn.commit()
        
        except Exception as e:
            logger.error(f"Failed to log security event: {str(e)}")
    
    def check_rate_limit(self, entity_type: str, entity_value: str, 
                        action_type: str, limit: int, window_minutes: int = 60) -> bool:
        """Check rate limiting"""
        try:
            current_time = datetime.utcnow()
            window_start = current_time - timedelta(minutes=window_minutes)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get current count in window
                cursor.execute("""
                    SELECT attempt_count FROM rate_limits 
                    WHERE entity_type = ? AND entity_value = ? AND action_type = ?
                    AND window_start > ?
                """, (entity_type, entity_value, action_type, window_start))
                
                result = cursor.fetchone()
                current_count = result[0] if result else 0
                
                if current_count >= limit:
                    return False  # Rate limit exceeded
                
                # Update or insert rate limit record
                cursor.execute("""
                    INSERT OR REPLACE INTO rate_limits 
                    (entity_type, entity_value, action_type, attempt_count, 
                     window_start, last_attempt)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (entity_type, entity_value, action_type, current_count + 1,
                      window_start if current_count > 0 else current_time, current_time))
                
                conn.commit()
                return True
        
        except Exception as e:
            logger.error(f"Rate limit check failed: {str(e)}")
            return False  # Fail closed
    
    def block_entity(self, entity_type: str, entity_value: str, reason: str,
                    duration_hours: int = None):
        """Block entity (IP, email, etc.)"""
        try:
            blocked_until = None
            is_permanent = 0
            
            if duration_hours:
                blocked_until = datetime.utcnow() + timedelta(hours=duration_hours)
            else:
                is_permanent = 1
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO blocked_entities 
                    (entity_type, entity_value, reason, blocked_until, is_permanent)
                    VALUES (?, ?, ?, ?, ?)
                """, (entity_type, entity_value, reason, blocked_until, is_permanent))
                conn.commit()
            
            logger.warning(f"Blocked {entity_type}: {entity_value} - {reason}")
        
        except Exception as e:
            logger.error(f"Failed to block entity: {str(e)}")
    
    def is_entity_blocked(self, entity_type: str, entity_value: str) -> bool:
        """Check if entity is blocked"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT blocked_until, is_permanent FROM blocked_entities 
                    WHERE entity_type = ? AND entity_value = ?
                """, (entity_type, entity_value))
                
                result = cursor.fetchone()
                
                if result:
                    blocked_until, is_permanent = result
                    
                    if is_permanent:
                        return True
                    
                    if blocked_until and datetime.fromisoformat(blocked_until) > datetime.utcnow():
                        return True
                
                return False
        
        except Exception as e:
            logger.error(f"Failed to check if entity is blocked: {str(e)}")
            return False
    
    def validate_pci_compliance(self, operation: str, data_fields: List[str],
                              user_id: int = None, ip_address: str = None) -> Dict:
        """Validate PCI DSS compliance for operations"""
        try:
            compliance_result = {
                "compliant": True,
                "violations": [],
                "recommendations": []
            }
            
            # Check for PAN (Primary Account Number) exposure
            sensitive_fields = ['card_number', 'pan', 'ccn']
            for field in data_fields:
                if any(sensitive in field.lower() for sensitive in sensitive_fields):
                    compliance_result["violations"].append(
                        f"Potential PAN exposure in field: {field}"
                    )
                    compliance_result["compliant"] = False
            
            # Check for CVV storage (never allowed)
            cvv_fields = ['cvv', 'cvc', 'cvv2', 'cid']
            for field in data_fields:
                if any(cvv in field.lower() for cvv in cvv_fields):
                    compliance_result["violations"].append(
                        f"CVV data detected in field: {field} (storage prohibited)"
                    )
                    compliance_result["compliant"] = False
            
            # Log compliance audit
            self._log_pci_audit(operation, user_id, data_fields, ip_address, compliance_result)
            
            return compliance_result
        
        except Exception as e:
            logger.error(f"PCI compliance validation failed: {str(e)}")
            return {"compliant": False, "violations": ["validation_error"], "recommendations": []}
    
    def _log_pci_audit(self, operation: str, user_id: int, data_fields: List[str],
                      ip_address: str, compliance_result: Dict):
        """Log PCI compliance audit"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO pci_audit_log 
                    (event_type, user_id, data_accessed, ip_address, 
                     compliance_status, audit_trail)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (operation, user_id, json.dumps(data_fields), ip_address,
                      "compliant" if compliance_result["compliant"] else "violation",
                      json.dumps(compliance_result)))
                conn.commit()
        
        except Exception as e:
            logger.error(f"Failed to log PCI audit: {str(e)}")
    
    # Helper methods for risk analysis
    def _is_ip_frequently_changing(self, ip_address: str) -> bool:
        """Check if user frequently changes IP"""
        # Implement logic to check IP change frequency
        return False
    
    def _is_geographic_inconsistency(self, ip_address: str) -> bool:
        """Check for geographic inconsistencies"""
        # Implement geolocation checking
        return False
    
    def _is_proxy_or_vpn(self, ip_address: str) -> bool:
        """Check if IP is proxy or VPN"""
        # Implement proxy/VPN detection
        return False
    
    def _get_recent_attempts(self, user_id: int, minutes: int = 5) -> int:
        """Get recent attempts count"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM fraud_signals 
                    WHERE user_id = ? AND created_at > ?
                """, (user_id, cutoff_time))
                
                result = cursor.fetchone()
                return result[0] if result else 0
        
        except Exception as e:
            logger.error(f"Failed to get recent attempts: {str(e)}")
            return 0
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate cryptographically secure token"""
        return secrets.token_urlsafe(length)
    
    def hash_sensitive_identifier(self, identifier: str) -> str:
        """Hash sensitive identifier for storage"""
        return hashlib.sha256(identifier.encode()).hexdigest()


# Global security service instance
security_service = SecurityService()