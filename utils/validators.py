"""
TalkingPhoto AI MVP - Validation Utilities
Input validation functions for security and data integrity
"""

import re
import os
from marshmallow import ValidationError
from flask import current_app
from typing import List, Optional


def validate_email(email: str) -> bool:
    """
    Validate email format using RFC 5322 compliant regex
    """
    if not email or len(email) > 254:
        return False
    
    pattern = re.compile(
        r'^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}'
        r'[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
    )
    
    return bool(pattern.match(email))


def validate_password(password: str) -> str:
    """
    Validate password strength and return error message if invalid
    """
    if not password:
        raise ValidationError("Password is required")
    
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long")
    
    if len(password) > 128:
        raise ValidationError("Password must be less than 128 characters")
    
    # Check for at least one lowercase letter
    if not re.search(r'[a-z]', password):
        raise ValidationError("Password must contain at least one lowercase letter")
    
    # Check for at least one uppercase letter
    if not re.search(r'[A-Z]', password):
        raise ValidationError("Password must contain at least one uppercase letter")
    
    # Check for at least one digit
    if not re.search(r'\d', password):
        raise ValidationError("Password must contain at least one number")
    
    # Check for at least one special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValidationError("Password must contain at least one special character")
    
    # Check for common weak passwords
    weak_passwords = [
        'password', '12345678', 'qwerty123', 'admin123', 'welcome123',
        'password123', 'letmein123', 'monkey123', 'dragon123'
    ]
    
    if password.lower() in weak_passwords:
        raise ValidationError("This password is too common. Please choose a stronger password")
    
    return password


def validate_file_extension(filename: str) -> bool:
    """
    Validate file extension against allowed extensions
    """
    if not filename:
        return False
    
    allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'jpg', 'jpeg', 'png'})
    
    if '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in allowed_extensions


def validate_file_size(file_size: int) -> bool:
    """
    Validate file size against maximum allowed size
    """
    max_size = current_app.config.get('MAX_CONTENT_LENGTH', 10485760)  # 10MB default
    return 0 < file_size <= max_size


def validate_script_text(script: str) -> str:
    """
    Validate video script text
    """
    if not script:
        raise ValidationError("Script text is required")
    
    script = script.strip()
    
    if len(script) < 10:
        raise ValidationError("Script must be at least 10 characters long")
    
    if len(script) > 500:
        raise ValidationError("Script must be less than 500 characters")
    
    # Check for potentially harmful content
    harmful_patterns = [
        r'<script[^>]*>.*?</script>',  # JavaScript
        r'javascript:',               # JavaScript protocol
        r'data:text/html',           # Data URL with HTML
        r'vbscript:',                # VBScript
        r'onload=',                  # Event handlers
        r'onerror=',
        r'onclick=',
    ]
    
    for pattern in harmful_patterns:
        if re.search(pattern, script, re.IGNORECASE):
            raise ValidationError("Script contains potentially harmful content")
    
    return script


def validate_phone_number(phone: str, country_code: str = 'IN') -> str:
    """
    Validate phone number format (primarily for Indian numbers)
    """
    if not phone:
        raise ValidationError("Phone number is required")
    
    # Remove all non-digit characters
    phone_digits = re.sub(r'[^\d]', '', phone)
    
    if country_code == 'IN':
        # Indian mobile numbers: 10 digits starting with 6-9
        if len(phone_digits) == 10 and phone_digits[0] in '6789':
            return f"+91{phone_digits}"
        # With country code
        elif len(phone_digits) == 12 and phone_digits.startswith('91') and phone_digits[2] in '6789':
            return f"+{phone_digits}"
        else:
            raise ValidationError("Invalid Indian phone number format")
    
    # For other countries, basic validation
    if len(phone_digits) < 10 or len(phone_digits) > 15:
        raise ValidationError("Invalid phone number format")
    
    return phone_digits


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal and other attacks
    """
    if not filename:
        return "unnamed_file"
    
    # Remove path components
    filename = os.path.basename(filename)
    
    # Remove or replace dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = re.sub(r'\.{2,}', '.', filename)  # Remove multiple dots
    filename = filename.strip('. ')  # Remove leading/trailing dots and spaces
    
    # Ensure filename is not empty after sanitization
    if not filename or filename == '.':
        filename = "unnamed_file"
    
    # Limit filename length
    name, ext = os.path.splitext(filename)
    if len(name) > 100:
        name = name[:100]
        filename = name + ext
    
    return filename


def validate_url(url: str, allowed_schemes: Optional[List[str]] = None) -> str:
    """
    Validate URL format and scheme
    """
    if not url:
        raise ValidationError("URL is required")
    
    if allowed_schemes is None:
        allowed_schemes = ['http', 'https']
    
    url_pattern = re.compile(
        r'^(?:(?P<scheme>https?):\/\/)'  # scheme
        r'(?:(?P<user>[^\s:@\/]+)(?::(?P<password>[^\s@\/]+))?@)?'  # user info
        r'(?P<host>(?:[^\s:\/]+\.)*[^\s:\/]+)'  # host
        r'(?::(?P<port>\d+))?'  # port
        r'(?P<path>\/[^\s?#]*)?'  # path
        r'(?:\?(?P<query>[^\s#]*))?'  # query
        r'(?:#(?P<fragment>[^\s]*))?$'  # fragment
    )
    
    match = url_pattern.match(url)
    if not match:
        raise ValidationError("Invalid URL format")
    
    scheme = match.group('scheme')
    if scheme and scheme not in allowed_schemes:
        raise ValidationError(f"URL scheme must be one of: {', '.join(allowed_schemes)}")
    
    return url


def validate_color_code(color: str) -> str:
    """
    Validate hexadecimal color code
    """
    if not color:
        raise ValidationError("Color code is required")
    
    # Add # if missing
    if not color.startswith('#'):
        color = f"#{color}"
    
    # Validate hex color format
    if not re.match(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', color):
        raise ValidationError("Invalid color code format. Use #RRGGBB or #RGB")
    
    return color


def validate_json_data(data: str) -> dict:
    """
    Validate and parse JSON data
    """
    import json
    
    if not data:
        raise ValidationError("JSON data is required")
    
    try:
        parsed_data = json.loads(data)
        return parsed_data
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON format: {str(e)}")


def validate_aspect_ratio(ratio: str) -> str:
    """
    Validate video aspect ratio format
    """
    valid_ratios = ['1:1', '9:16', '16:9', '4:3', '21:9']
    
    if ratio not in valid_ratios:
        raise ValidationError(f"Invalid aspect ratio. Must be one of: {', '.join(valid_ratios)}")
    
    return ratio


def validate_duration(seconds: int) -> int:
    """
    Validate video duration
    """
    if not isinstance(seconds, int) or seconds <= 0:
        raise ValidationError("Duration must be a positive integer")
    
    if seconds > 300:  # 5 minutes max
        raise ValidationError("Duration cannot exceed 300 seconds")
    
    if seconds < 5:  # 5 seconds minimum
        raise ValidationError("Duration must be at least 5 seconds")
    
    return seconds


def validate_coordinate(lat: float, lng: float) -> tuple:
    """
    Validate latitude and longitude coordinates
    """
    if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
        raise ValidationError("Coordinates must be numeric values")
    
    if not (-90 <= lat <= 90):
        raise ValidationError("Latitude must be between -90 and 90")
    
    if not (-180 <= lng <= 180):
        raise ValidationError("Longitude must be between -180 and 180")
    
    return (lat, lng)


def validate_timezone(tz_string: str) -> str:
    """
    Validate timezone string
    """
    import pytz
    
    if not tz_string:
        raise ValidationError("Timezone is required")
    
    try:
        pytz.timezone(tz_string)
        return tz_string
    except pytz.exceptions.UnknownTimeZoneError:
        raise ValidationError("Invalid timezone")


def validate_language_code(lang_code: str) -> str:
    """
    Validate ISO 639-1 language code
    """
    valid_codes = [
        'en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh',
        'hi', 'ar', 'bn', 'ur', 'te', 'ta', 'mr', 'gu', 'kn', 'ml'
    ]
    
    if lang_code.lower() not in valid_codes:
        raise ValidationError(f"Invalid language code. Must be one of: {', '.join(valid_codes)}")
    
    return lang_code.lower()


def validate_currency_code(currency: str) -> str:
    """
    Validate ISO 4217 currency code
    """
    valid_currencies = [
        'USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'CNY',
        'INR', 'BRL', 'RUB', 'KRW', 'SGD', 'HKD', 'NOK', 'SEK'
    ]
    
    currency = currency.upper()
    
    if currency not in valid_currencies:
        raise ValidationError(f"Invalid currency code. Must be one of: {', '.join(valid_currencies)}")
    
    return currency


def validate_positive_integer(value: int, field_name: str = "Value") -> int:
    """
    Validate positive integer
    """
    if not isinstance(value, int) or value <= 0:
        raise ValidationError(f"{field_name} must be a positive integer")
    
    return value


def validate_non_negative_integer(value: int, field_name: str = "Value") -> int:
    """
    Validate non-negative integer
    """
    if not isinstance(value, int) or value < 0:
        raise ValidationError(f"{field_name} must be a non-negative integer")
    
    return value