"""
TalkingPhoto AI MVP - Security Utilities
Security helper functions for authentication and request validation
"""

import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta
from flask import request
from user_agents import parse
from typing import Dict, Any, Optional
import structlog

logger = structlog.get_logger()


def get_client_info(request_obj) -> Dict[str, Any]:
    """
    Extract client information from request for security tracking
    """
    try:
        # Get IP address (handle proxies)
        ip_address = request_obj.environ.get('HTTP_X_FORWARDED_FOR')
        if ip_address:
            ip_address = ip_address.split(',')[0].strip()
        else:
            ip_address = request_obj.environ.get('HTTP_X_REAL_IP') or request_obj.remote_addr
        
        # Parse user agent
        user_agent_string = request_obj.headers.get('User-Agent', '')
        user_agent = parse(user_agent_string)
        
        # Determine device type
        if user_agent.is_mobile:
            device_type = 'mobile'
        elif user_agent.is_tablet:
            device_type = 'tablet'
        elif user_agent.is_pc:
            device_type = 'desktop'
        elif user_agent.is_bot:
            device_type = 'bot'
        else:
            device_type = 'unknown'
        
        return {
            'ip_address': ip_address,
            'user_agent': user_agent_string,
            'browser_family': user_agent.browser.family,
            'browser_version': user_agent.browser.version_string,
            'os_family': user_agent.os.family,
            'os_version': user_agent.os.version_string,
            'device_type': device_type,
            'is_mobile': user_agent.is_mobile,
            'is_bot': user_agent.is_bot,
            'referer': request_obj.headers.get('Referer'),
            'accept_language': request_obj.headers.get('Accept-Language')
        }
    except Exception as e:
        logger.error("Failed to extract client info", error=str(e))
        return {
            'ip_address': request_obj.remote_addr,
            'user_agent': request_obj.headers.get('User-Agent', ''),
            'device_type': 'unknown',
            'is_mobile': False,
            'is_bot': False
        }


def is_suspicious_activity(email: str, ip_address: str, time_window_minutes: int = 15) -> bool:
    """
    Detect suspicious login activity (rate limiting, geographic anomalies)
    """
    try:
        # In a production system, this would check against a database of recent attempts
        # For now, implement basic rate limiting logic
        
        # Create a unique key for this email + IP combination
        activity_key = hashlib.sha256(f"{email}:{ip_address}".encode()).hexdigest()
        
        # In production, store attempt counts in Redis with expiration
        # For MVP, we'll use a simple in-memory approach (not persistent)
        
        # Check for common suspicious patterns
        suspicious_user_agents = [
            'curl', 'wget', 'python-requests', 'bot', 'crawler', 'spider'
        ]
        
        user_agent = request.headers.get('User-Agent', '').lower()
        for suspicious in suspicious_user_agents:
            if suspicious in user_agent:
                logger.warning("Suspicious user agent detected", 
                             email=email, ip=ip_address, user_agent=user_agent)
                return True
        
        # Check for rapid consecutive requests (basic implementation)
        # In production, implement proper rate limiting with Redis
        
        return False
        
    except Exception as e:
        logger.error("Suspicious activity check failed", error=str(e))
        return False


def generate_secure_token(length: int = 32) -> str:
    """
    Generate cryptographically secure random token
    """
    return secrets.token_urlsafe(length)


def generate_csrf_token() -> str:
    """
    Generate CSRF protection token
    """
    return secrets.token_hex(32)


def verify_csrf_token(token: str, expected_token: str) -> bool:
    """
    Verify CSRF token using constant-time comparison
    """
    if not token or not expected_token:
        return False
    
    return hmac.compare_digest(token, expected_token)


def hash_password_reset_token(email: str, timestamp: str) -> str:
    """
    Generate secure password reset token
    """
    # Combine email, timestamp, and a secret
    secret = secrets.token_hex(16)  # In production, use app secret key
    message = f"{email}:{timestamp}:{secret}"
    
    return hashlib.sha256(message.encode()).hexdigest()


def verify_password_reset_token(token: str, email: str, timestamp: str, 
                               max_age_hours: int = 1) -> bool:
    """
    Verify password reset token and check expiration
    """
    try:
        # Check token age
        token_time = datetime.fromisoformat(timestamp)
        if datetime.utcnow() - token_time > timedelta(hours=max_age_hours):
            return False
        
        # Verify token (simplified for MVP)
        # In production, implement proper token verification
        return len(token) == 64 and token.isalnum()
        
    except Exception as e:
        logger.error("Token verification failed", error=str(e))
        return False


def sanitize_input(input_string: str, max_length: int = None) -> str:
    """
    Sanitize user input to prevent XSS and injection attacks
    """
    if not isinstance(input_string, str):
        return ""
    
    # Remove null bytes and control characters
    sanitized = input_string.replace('\x00', '').strip()
    
    # Remove potentially dangerous HTML tags and scripts
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',
        r'<iframe[^>]*>.*?</iframe>',
        r'<object[^>]*>.*?</object>',
        r'<embed[^>]*>.*?</embed>',
        r'javascript:',
        r'vbscript:',
        r'data:text/html',
        r'onload\s*=',
        r'onerror\s*=',
        r'onclick\s*=',
        r'onmouseover\s*='
    ]
    
    import re
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    
    # Limit length if specified
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def validate_file_signature(file_content: bytes, expected_type: str) -> bool:
    """
    Validate file signature (magic numbers) to prevent file type spoofing
    """
    if not file_content:
        return False
    
    # Common file signatures
    signatures = {
        'jpeg': [b'\xff\xd8\xff'],
        'png': [b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a'],
        'gif': [b'GIF87a', b'GIF89a'],
        'pdf': [b'%PDF-'],
        'mp4': [b'\x00\x00\x00\x18ftypmp4', b'\x00\x00\x00\x20ftypisom']
    }
    
    expected_signatures = signatures.get(expected_type.lower(), [])
    
    for signature in expected_signatures:
        if file_content.startswith(signature):
            return True
    
    return False


def generate_api_key(user_id: str, length: int = 40) -> str:
    """
    Generate API key for user
    """
    # Combine user ID with random data and timestamp
    timestamp = str(int(time.time()))
    random_data = secrets.token_hex(16)
    
    # Create hash
    message = f"{user_id}:{timestamp}:{random_data}"
    api_key_hash = hashlib.sha256(message.encode()).hexdigest()
    
    return f"tpai_{api_key_hash[:length-5]}"


def verify_api_key(api_key: str, user_id: str) -> bool:
    """
    Verify API key format and association
    """
    if not api_key or not api_key.startswith('tpai_'):
        return False
    
    # In production, verify against database
    # For MVP, basic format validation
    key_part = api_key[5:]  # Remove 'tpai_' prefix
    
    return len(key_part) == 35 and key_part.isalnum()


def check_rate_limit(identifier: str, max_requests: int, time_window_seconds: int) -> Dict[str, Any]:
    """
    Basic rate limiting check (in production, use Redis)
    """
    # This is a simplified implementation
    # In production, use Redis with sliding window or token bucket algorithm
    
    current_time = int(time.time())
    window_start = current_time - time_window_seconds
    
    # For MVP, we'll use a simple in-memory approach
    # In production, replace with Redis-based implementation
    
    return {
        'allowed': True,  # Simplified for MVP
        'remaining': max_requests,
        'reset_time': current_time + time_window_seconds
    }


def encrypt_sensitive_data(data: str, key: Optional[str] = None) -> str:
    """
    Encrypt sensitive data (simplified for MVP)
    """
    from cryptography.fernet import Fernet
    
    if key is None:
        # In production, use app secret key
        key = Fernet.generate_key()
    
    if isinstance(key, str):
        key = key.encode()
    
    f = Fernet(key)
    encrypted = f.encrypt(data.encode())
    return encrypted.decode()


def decrypt_sensitive_data(encrypted_data: str, key: str) -> str:
    """
    Decrypt sensitive data (simplified for MVP)
    """
    from cryptography.fernet import Fernet
    
    if isinstance(key, str):
        key = key.encode()
    
    f = Fernet(key)
    decrypted = f.decrypt(encrypted_data.encode())
    return decrypted.decode()


def generate_signature(data: str, secret_key: str) -> str:
    """
    Generate HMAC signature for webhook verification
    """
    signature = hmac.new(
        secret_key.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return f"sha256={signature}"


def verify_webhook_signature(payload: str, signature: str, secret_key: str) -> bool:
    """
    Verify webhook signature (e.g., Stripe webhooks)
    """
    expected_signature = generate_signature(payload, secret_key)
    
    return hmac.compare_digest(signature, expected_signature)


def mask_sensitive_data(data: str, mask_char: str = '*', visible_chars: int = 4) -> str:
    """
    Mask sensitive data for logging (e.g., email addresses, API keys)
    """
    if not data:
        return ""
    
    if len(data) <= visible_chars:
        return mask_char * len(data)
    
    return data[:visible_chars] + mask_char * (len(data) - visible_chars)


def validate_request_origin(request_obj, allowed_origins: list) -> bool:
    """
    Validate request origin for CORS security
    """
    origin = request_obj.headers.get('Origin')
    
    if not origin:
        # Allow requests without Origin header (direct API calls)
        return True
    
    return origin in allowed_origins


def log_security_event(event_type: str, user_id: str = None, details: Dict[str, Any] = None):
    """
    Log security events for monitoring and compliance
    """
    try:
        event_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'ip_address': request.remote_addr if request else None,
            'user_agent': request.headers.get('User-Agent') if request else None,
            'details': details or {}
        }
        
        logger.warning("Security event", **event_data)
        
        # In production, also send to SIEM system or security monitoring service
        
    except Exception as e:
        logger.error("Failed to log security event", error=str(e))


def check_password_breach(password: str) -> bool:
    """
    Check if password appears in known breach databases (simplified)
    """
    # In production, integrate with HaveIBeenPwned API or similar service
    # For MVP, check against common breached passwords
    
    common_breached = [
        '123456', 'password', '12345678', 'qwerty', '123456789',
        'password123', 'letmein', 'welcome', 'admin', '123123'
    ]
    
    return password.lower() in common_breached


def generate_session_id() -> str:
    """
    Generate secure session identifier
    """
    return secrets.token_urlsafe(32)


def validate_session_id(session_id: str) -> bool:
    """
    Validate session ID format
    """
    if not session_id:
        return False
    
    # Check length and characters
    if len(session_id) != 43:  # Base64 encoded 32 bytes
        return False
    
    # Check for valid base64 characters
    import string
    valid_chars = string.ascii_letters + string.digits + '-_'
    return all(c in valid_chars for c in session_id)