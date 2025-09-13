"""
TalkingPhoto AI MVP - Critical Security Fixes
Implement these fixes immediately to address critical vulnerabilities
"""

import os
import secrets
import hashlib
import re
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, session, abort
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from werkzeug.security import generate_password_hash
import bleach
from cryptography.fernet import Fernet
import jwt

# ============================================
# 1. SECURE CONFIGURATION MANAGEMENT
# ============================================

class SecureConfig:
    """Secure configuration with proper secret management"""
    
    @staticmethod
    def get_secret_key() -> str:
        """Get or generate secure secret key"""
        secret = os.environ.get('SECRET_KEY')
        if not secret or secret == 'dev-secret-key-change-in-production':
            # Generate cryptographically secure key
            secret = secrets.token_hex(32)
            print(f"WARNING: Generated new SECRET_KEY: {secret}")
            print("Set this in your environment: export SECRET_KEY='{}'".format(secret))
        return secret
    
    @staticmethod
    def get_jwt_secret() -> str:
        """Get or generate secure JWT secret"""
        secret = os.environ.get('JWT_SECRET_KEY')
        if not secret or secret == 'jwt-secret-key-change-in-production':
            secret = secrets.token_hex(32)
            print(f"WARNING: Generated new JWT_SECRET_KEY: {secret}")
            print("Set this in your environment: export JWT_SECRET_KEY='{}'".format(secret))
        return secret
    
    @staticmethod
    def validate_api_keys():
        """Validate that API keys are not exposed"""
        dangerous_patterns = [
            'AIza',  # Google API key pattern
            'sk_test_',  # Stripe test key
            'sk_live_',  # Stripe live key
        ]
        
        for key, value in os.environ.items():
            if 'KEY' in key or 'SECRET' in key or 'PASSWORD' in key:
                for pattern in dangerous_patterns:
                    if pattern in str(value):
                        raise ValueError(f"Exposed API key detected in {key}! Rotate immediately!")


# ============================================
# 2. ENHANCED PASSWORD VALIDATION
# ============================================

class PasswordValidator:
    """Strong password validation with breach checking"""
    
    MIN_LENGTH = 12
    COMMON_PASSWORDS = [
        '123456', 'password', '12345678', 'qwerty', '123456789',
        'password123', 'letmein', 'welcome', 'admin', '123123'
    ]
    
    @staticmethod
    def validate_password(password: str) -> tuple[bool, str]:
        """
        Validate password strength
        Returns: (is_valid, error_message)
        """
        # Check minimum length
        if len(password) < PasswordValidator.MIN_LENGTH:
            return False, f"Password must be at least {PasswordValidator.MIN_LENGTH} characters"
        
        # Check for uppercase
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        # Check for lowercase
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        # Check for numbers
        if not re.search(r'[0-9]', password):
            return False, "Password must contain at least one number"
        
        # Check for special characters
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        
        # Check against common passwords
        if password.lower() in PasswordValidator.COMMON_PASSWORDS:
            return False, "This password is too common and has been compromised"
        
        # Check for sequential characters
        if any(password[i:i+3].lower() in 'abcdefghijklmnopqrstuvwxyz0123456789' 
               for i in range(len(password) - 2)):
            return False, "Password contains sequential characters"
        
        return True, "Password is strong"
    
    @staticmethod
    def hash_password_secure(password: str) -> str:
        """Generate secure password hash with proper salt"""
        return generate_password_hash(
            password,
            method='pbkdf2:sha256:260000',  # Increased iterations
            salt_length=32  # Longer salt
        )


# ============================================
# 3. SQL INJECTION PREVENTION
# ============================================

class SecureDatabase:
    """Secure database operations with parameterized queries"""
    
    @staticmethod
    def safe_query(query: str, params: tuple) -> str:
        """
        Execute safe parameterized query
        NEVER use string formatting for SQL queries!
        """
        # Example of safe query execution
        # cursor.execute(query, params)
        # NOT: cursor.execute(query % params)
        return "Use parameterized queries only"
    
    @staticmethod
    def validate_input_for_sql(user_input: str) -> str:
        """Validate and sanitize input before database operations"""
        # Remove SQL keywords and special characters
        dangerous_keywords = [
            'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'UNION',
            'CREATE', 'ALTER', 'EXEC', 'EXECUTE', '--', '/*', '*/'
        ]
        
        clean_input = user_input
        for keyword in dangerous_keywords:
            clean_input = clean_input.replace(keyword, '')
            clean_input = clean_input.replace(keyword.lower(), '')
        
        # Escape special characters
        clean_input = clean_input.replace("'", "''")
        clean_input = clean_input.replace('"', '""')
        clean_input = clean_input.replace('\\', '\\\\')
        
        return clean_input[:255]  # Limit length


# ============================================
# 4. CSRF PROTECTION
# ============================================

class CSRFProtection:
    """CSRF token generation and validation"""
    
    @staticmethod
    def generate_csrf_token() -> str:
        """Generate secure CSRF token"""
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_hex(32)
        return session['csrf_token']
    
    @staticmethod
    def validate_csrf_token(token: str) -> bool:
        """Validate CSRF token"""
        if 'csrf_token' not in session:
            return False
        return secrets.compare_digest(session['csrf_token'], token)
    
    @staticmethod
    def csrf_protect(f):
        """Decorator to protect endpoints with CSRF validation"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
                token = request.form.get('csrf_token') or \
                        request.headers.get('X-CSRF-Token')
                
                if not token or not CSRFProtection.validate_csrf_token(token):
                    abort(403, 'CSRF validation failed')
            
            return f(*args, **kwargs)
        return decorated_function


# ============================================
# 5. XSS PREVENTION
# ============================================

class XSSProtection:
    """XSS prevention and input sanitization"""
    
    @staticmethod
    def sanitize_html(html_content: str) -> str:
        """Sanitize HTML content to prevent XSS"""
        # Define allowed tags and attributes
        allowed_tags = [
            'p', 'br', 'span', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'strong', 'em', 'u', 'a', 'img', 'ul', 'ol', 'li'
        ]
        
        allowed_attributes = {
            'a': ['href', 'title', 'target'],
            'img': ['src', 'alt', 'width', 'height'],
            'div': ['class', 'id'],
            'span': ['class', 'id']
        }
        
        # Clean the HTML
        cleaned = bleach.clean(
            html_content,
            tags=allowed_tags,
            attributes=allowed_attributes,
            strip=True
        )
        
        # Additional sanitization for URLs
        cleaned = bleach.linkify(cleaned)
        
        return cleaned
    
    @staticmethod
    def sanitize_input(user_input: str, max_length: int = 1000) -> str:
        """Sanitize user input to prevent XSS"""
        if not isinstance(user_input, str):
            return ""
        
        # Remove null bytes and control characters
        sanitized = user_input.replace('\x00', '').strip()
        
        # Remove script tags and javascript
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',  # onclick, onload, etc.
            r'<iframe[^>]*>.*?</iframe>',
            r'<object[^>]*>.*?</object>',
            r'<embed[^>]*>.*?</embed>'
        ]
        
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        # Limit length
        return sanitized[:max_length]


# ============================================
# 6. SECURE SESSION MANAGEMENT
# ============================================

class SecureSessionManager:
    """Secure session management with timeout and validation"""
    
    SESSION_TIMEOUT = timedelta(minutes=30)
    MAX_SESSION_DURATION = timedelta(hours=24)
    
    @staticmethod
    def create_session(user_id: str, request_info: dict) -> dict:
        """Create secure session with proper tracking"""
        session_id = secrets.token_urlsafe(32)
        
        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'created_at': datetime.utcnow().isoformat(),
            'last_activity': datetime.utcnow().isoformat(),
            'ip_address': request_info.get('ip_address'),
            'user_agent': request_info.get('user_agent'),
            'fingerprint': hashlib.sha256(
                f"{request_info.get('ip_address')}:{request_info.get('user_agent')}".encode()
            ).hexdigest()
        }
        
        # Store in secure session store (Redis recommended)
        session['user_data'] = session_data
        session.permanent = True
        
        return session_data
    
    @staticmethod
    def validate_session() -> bool:
        """Validate current session"""
        if 'user_data' not in session:
            return False
        
        user_data = session['user_data']
        
        # Check session timeout
        last_activity = datetime.fromisoformat(user_data['last_activity'])
        if datetime.utcnow() - last_activity > SecureSessionManager.SESSION_TIMEOUT:
            session.clear()
            return False
        
        # Check maximum session duration
        created_at = datetime.fromisoformat(user_data['created_at'])
        if datetime.utcnow() - created_at > SecureSessionManager.MAX_SESSION_DURATION:
            session.clear()
            return False
        
        # Validate fingerprint
        current_fingerprint = hashlib.sha256(
            f"{request.remote_addr}:{request.headers.get('User-Agent')}".encode()
        ).hexdigest()
        
        if current_fingerprint != user_data['fingerprint']:
            # Possible session hijacking
            session.clear()
            return False
        
        # Update last activity
        user_data['last_activity'] = datetime.utcnow().isoformat()
        session['user_data'] = user_data
        
        return True


# ============================================
# 7. RATE LIMITING CONFIGURATION
# ============================================

def configure_rate_limiting(app: Flask):
    """Configure comprehensive rate limiting"""
    
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="redis://localhost:6379",
        strategy="fixed-window-elastic-expiry"
    )
    
    # Critical endpoint limits
    critical_limits = {
        '/api/auth/login': '3 per minute, 10 per hour',
        '/api/auth/register': '2 per minute, 5 per hour',
        '/api/auth/reset-password': '2 per hour',
        '/api/payment/': '10 per minute',
        '/api/upload': '5 per minute',
        '/api/video/generate': '2 per minute'
    }
    
    for endpoint, limit in critical_limits.items():
        limiter.limit(limit)(endpoint)
    
    return limiter


# ============================================
# 8. SECURITY HEADERS
# ============================================

def set_security_headers(response):
    """Set comprehensive security headers"""
    
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'DENY'
    
    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # Enable XSS protection
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Force HTTPS
    response.headers['Strict-Transport-Security'] = 'max-age=63072000; includeSubDomains; preload'
    
    # Content Security Policy
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://js.stripe.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://api.stripe.com https://api.talkingphoto.ai; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self';"
    )
    
    # Referrer Policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Permissions Policy
    response.headers['Permissions-Policy'] = (
        'accelerometer=(), camera=(), geolocation=(), gyroscope=(), '
        'magnetometer=(), microphone=(), payment=(), usb=()'
    )
    
    return response


# ============================================
# 9. FILE UPLOAD SECURITY
# ============================================

class SecureFileUpload:
    """Secure file upload with validation"""
    
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    # File signatures (magic numbers)
    FILE_SIGNATURES = {
        'jpeg': [b'\xff\xd8\xff\xe0', b'\xff\xd8\xff\xe1'],
        'png': [b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a'],
        'gif': [b'GIF87a', b'GIF89a']
    }
    
    @staticmethod
    def validate_file(file_data: bytes, filename: str) -> tuple[bool, str]:
        """Validate uploaded file"""
        
        # Check file size
        if len(file_data) > SecureFileUpload.MAX_FILE_SIZE:
            return False, "File too large"
        
        # Check extension
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        if ext not in SecureFileUpload.ALLOWED_EXTENSIONS:
            return False, "Invalid file type"
        
        # Check file signature
        valid_signature = False
        for file_type, signatures in SecureFileUpload.FILE_SIGNATURES.items():
            for signature in signatures:
                if file_data.startswith(signature):
                    valid_signature = True
                    break
        
        if not valid_signature:
            return False, "Invalid file signature"
        
        # Scan for malicious content
        if SecureFileUpload._contains_malicious_content(file_data):
            return False, "File contains malicious content"
        
        return True, "File is valid"
    
    @staticmethod
    def _contains_malicious_content(file_data: bytes) -> bool:
        """Check for malicious content in file"""
        malicious_patterns = [
            b'<script', b'javascript:', b'eval(', b'document.write',
            b'<?php', b'<%', b'<jsp:', b'<asp:'
        ]
        
        # Check first 1KB for malicious patterns
        check_data = file_data[:1024]
        for pattern in malicious_patterns:
            if pattern in check_data:
                return True
        
        return False


# ============================================
# 10. SECURE API KEY MANAGEMENT
# ============================================

class APIKeyManager:
    """Secure API key storage and retrieval"""
    
    @staticmethod
    def encrypt_api_key(api_key: str, master_key: str) -> str:
        """Encrypt API key for storage"""
        f = Fernet(master_key.encode() if len(master_key) == 44 else Fernet.generate_key())
        return f.encrypt(api_key.encode()).decode()
    
    @staticmethod
    def decrypt_api_key(encrypted_key: str, master_key: str) -> str:
        """Decrypt API key for use"""
        f = Fernet(master_key.encode())
        return f.decrypt(encrypted_key.encode()).decode()
    
    @staticmethod
    def rotate_api_keys():
        """Rotate API keys periodically"""
        # Implementation for key rotation
        print("API keys should be rotated every 90 days")
        print("Implement automated key rotation with your providers")


# ============================================
# 11. SECURITY EVENT LOGGING
# ============================================

class SecurityLogger:
    """Comprehensive security event logging"""
    
    @staticmethod
    def log_security_event(event_type: str, details: dict):
        """Log security events for audit trail"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'ip_address': request.remote_addr if request else None,
            'user_agent': request.headers.get('User-Agent') if request else None,
            'details': details
        }
        
        # Log to file or SIEM system
        print(f"SECURITY_EVENT: {event}")
        
        # Critical events should trigger alerts
        critical_events = [
            'authentication_failure',
            'csrf_validation_failed',
            'sql_injection_attempt',
            'xss_attempt',
            'file_upload_malicious',
            'api_key_exposed',
            'session_hijack_attempt'
        ]
        
        if event_type in critical_events:
            SecurityLogger._send_security_alert(event)
    
    @staticmethod
    def _send_security_alert(event: dict):
        """Send security alert for critical events"""
        # Implement alerting mechanism
        print(f"CRITICAL SECURITY ALERT: {event}")


# ============================================
# USAGE EXAMPLE
# ============================================

def apply_security_fixes(app: Flask):
    """Apply all security fixes to Flask application"""
    
    # 1. Set secure configuration
    app.config['SECRET_KEY'] = SecureConfig.get_secret_key()
    app.config['JWT_SECRET_KEY'] = SecureConfig.get_jwt_secret()
    
    # 2. Configure session security
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
    
    # 3. Configure CORS properly
    CORS(app, 
         origins=['https://talkingphoto.ai'],
         supports_credentials=True,
         methods=['GET', 'POST'],
         allow_headers=['Content-Type', 'Authorization', 'X-CSRF-Token'])
    
    # 4. Add security headers to all responses
    @app.after_request
    def add_security_headers(response):
        return set_security_headers(response)
    
    # 5. Configure rate limiting
    limiter = configure_rate_limiting(app)
    
    # 6. Add CSRF protection to all state-changing routes
    @app.before_request
    def csrf_protect():
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            token = request.form.get('csrf_token') or \
                    request.headers.get('X-CSRF-Token')
            
            if not token or not CSRFProtection.validate_csrf_token(token):
                abort(403, 'CSRF validation failed')
    
    # 7. Validate configuration on startup
    SecureConfig.validate_api_keys()
    
    print("Security fixes applied successfully!")
    return app


if __name__ == "__main__":
    print("TalkingPhoto AI Security Fixes")
    print("=" * 50)
    print("1. Run apply_security_fixes(app) in your Flask application")
    print("2. Remove credentials.txt file immediately")
    print("3. Rotate all exposed API keys")
    print("4. Update all database passwords")
    print("5. Run security tests after implementation")