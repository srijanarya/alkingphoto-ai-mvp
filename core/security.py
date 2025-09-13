"""
TalkingPhoto AI MVP - Security Utilities

Input validation, sanitization, and security helpers.
Implements OWASP best practices without external dependencies.
"""

import re
import html
import hashlib
import secrets
from typing import Any, Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


class SecurityValidator:
    """Security validation and sanitization utilities"""
    
    # Regex patterns for validation
    PATTERNS = {
        'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
        'alphanumeric': re.compile(r'^[a-zA-Z0-9]+$'),
        'safe_filename': re.compile(r'^[a-zA-Z0-9._-]+$'),
        'sql_injection': re.compile(r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|CREATE|ALTER)\b)', re.I),
        'xss_tags': re.compile(r'<[^>]+>'),
    }
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Sanitize HTML to prevent XSS attacks
        
        Args:
            text: Input text to sanitize
            
        Returns:
            str: Sanitized text
        """
        if not text:
            return ""
        
        # Remove HTML tags
        text = SecurityValidator.PATTERNS['xss_tags'].sub('', text)
        
        # Escape HTML entities
        text = html.escape(text)
        
        return text.strip()
    
    @staticmethod
    def validate_filename(filename: str) -> tuple[bool, str]:
        """Validate filename for security
        
        Args:
            filename: Filename to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not filename:
            return False, "Filename cannot be empty"
        
        # Check length
        if len(filename) > 255:
            return False, "Filename too long (max 255 characters)"
        
        # Check for path traversal attempts
        if '..' in filename or '/' in filename or '\\' in filename:
            return False, "Invalid characters in filename"
        
        # Check against safe pattern
        if not SecurityValidator.PATTERNS['safe_filename'].match(filename):
            return False, "Filename contains invalid characters"
        
        # Check for dangerous extensions
        dangerous_extensions = ['.exe', '.bat', '.cmd', '.sh', '.ps1', '.vbs']
        if any(filename.lower().endswith(ext) for ext in dangerous_extensions):
            return False, "File type not allowed"
        
        return True, ""
    
    @staticmethod
    def validate_text_input(text: str, max_length: int = 1000) -> tuple[bool, str]:
        """Validate text input for security issues
        
        Args:
            text: Text to validate
            max_length: Maximum allowed length
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not text:
            return False, "Text cannot be empty"
        
        # Check length
        if len(text) > max_length:
            return False, f"Text too long (max {max_length} characters)"
        
        # Check for SQL injection patterns
        if SecurityValidator.PATTERNS['sql_injection'].search(text):
            logger.warning("Potential SQL injection attempt detected")
            return False, "Invalid characters detected"
        
        # Check for script tags (basic XSS prevention)
        if '<script' in text.lower() or 'javascript:' in text.lower():
            logger.warning("Potential XSS attempt detected")
            return False, "Invalid content detected"
        
        return True, ""
    
    @staticmethod
    def generate_csrf_token() -> str:
        """Generate a secure CSRF token
        
        Returns:
            str: CSRF token
        """
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def verify_csrf_token(token: str, stored_token: str) -> bool:
        """Verify CSRF token
        
        Args:
            token: Submitted token
            stored_token: Stored token
            
        Returns:
            bool: True if tokens match
        """
        if not token or not stored_token:
            return False
        
        # Constant-time comparison to prevent timing attacks
        return secrets.compare_digest(token, stored_token)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA256 (for demo purposes)
        
        Note: In production, use bcrypt or argon2
        
        Args:
            password: Plain text password
            
        Returns:
            str: Hashed password
        """
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
        return f"{salt}${password_hash}"
    
    @staticmethod
    def rate_limit_check(identifier: str, max_requests: int = 10, 
                        window_seconds: int = 60) -> bool:
        """Simple rate limiting check
        
        Args:
            identifier: User identifier (IP, session ID, etc.)
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            bool: True if within limits
        """
        # This is a simplified version
        # In production, use Redis or database for persistent storage
        return True  # For now, always allow in dev mode


class InputSanitizer:
    """Input sanitization utilities"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean text input for safe processing
        
        Args:
            text: Input text
            
        Returns:
            str: Cleaned text
        """
        if not text:
            return ""
        
        # Remove control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char == '\n')
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        # Remove potential SQL/NoSQL injection attempts
        dangerous_patterns = [
            r'\$where',
            r'\$regex',
            r'\.\./',
            r'<script',
            r'javascript:',
            r'on\w+\s*=',  # onclick, onload, etc.
        ]
        
        for pattern in dangerous_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    @staticmethod
    def clean_json_input(data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean JSON input recursively
        
        Args:
            data: Input dictionary
            
        Returns:
            dict: Cleaned dictionary
        """
        if not isinstance(data, dict):
            return {}
        
        cleaned = {}
        for key, value in data.items():
            # Clean key
            clean_key = InputSanitizer.clean_text(str(key))
            
            # Clean value based on type
            if isinstance(value, str):
                cleaned[clean_key] = InputSanitizer.clean_text(value)
            elif isinstance(value, dict):
                cleaned[clean_key] = InputSanitizer.clean_json_input(value)
            elif isinstance(value, list):
                cleaned[clean_key] = [
                    InputSanitizer.clean_text(str(item)) if isinstance(item, str) 
                    else item for item in value
                ]
            else:
                cleaned[clean_key] = value
        
        return cleaned


class SessionSecurity:
    """Session security utilities"""
    
    @staticmethod
    def generate_session_id() -> str:
        """Generate secure session ID
        
        Returns:
            str: Session ID
        """
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def validate_session(session_id: str, max_age_hours: int = 24) -> bool:
        """Validate session (simplified for demo)
        
        Args:
            session_id: Session ID to validate
            max_age_hours: Maximum session age in hours
            
        Returns:
            bool: True if valid
        """
        if not session_id:
            return False
        
        # Check format
        if len(session_id) < 32:
            return False
        
        # In production, check against database with timestamp
        return True


# Content Security Policy headers for production
CSP_HEADERS = {
    'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline';",
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
}