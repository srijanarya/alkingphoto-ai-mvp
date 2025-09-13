"""
TalkingPhoto AI MVP - Configuration Management
Environment-specific configuration classes
"""

import os
from datetime import timedelta


class Config:
    """Base configuration class"""
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/talkingphoto_mvp')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'pool_size': 10,
        'max_overflow': 20
    }
    
    # Redis Configuration
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 10485760))  # 10MB
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    ALLOWED_EXTENSIONS = set(os.getenv('ALLOWED_EXTENSIONS', 'jpg,jpeg,png').split(','))
    
    # Cloudinary Configuration (Primary Storage)
    CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME')
    CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY')
    CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET')
    
    # AWS Configuration (Optional/Future)
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
    CLOUDFRONT_DOMAIN = os.getenv('CLOUDFRONT_DOMAIN')
    
    # AI Service Configuration - ALL GOOGLE APIs ENABLED!
    GOOGLE_AI_API_KEY = os.getenv('GOOGLE_AI_API_KEY')  # Main Google AI key
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', os.getenv('GOOGLE_AI_API_KEY'))  # Gemini/Nano Banana
    NANO_BANANA_API_KEY = os.getenv('NANO_BANANA_API_KEY', os.getenv('GEMINI_API_KEY'))
    VEO3_API_KEY = os.getenv('VEO3_API_KEY')
    RUNWAY_API_KEY = os.getenv('RUNWAY_API_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Google Cloud APIs Status
    GOOGLE_VISION_ENABLED = os.getenv('GOOGLE_VISION_ENABLED', 'true').lower() == 'true'
    GOOGLE_TTS_ENABLED = os.getenv('GOOGLE_TTS_ENABLED', 'true').lower() == 'true'
    VEO3_ENABLED = os.getenv('VEO3_ENABLED', 'false').lower() == 'true'
    
    # Feature Flags based on API availability
    FEATURES_ENABLED = {
        'photo_enhancement': bool(GOOGLE_AI_API_KEY or GEMINI_API_KEY),
        'face_detection': bool(GEMINI_API_KEY),  # Using Gemini Vision instead of Cloud Vision
        'text_to_speech': GOOGLE_TTS_ENABLED and bool(GOOGLE_AI_API_KEY),
        'video_generation': VEO3_ENABLED and bool(VEO3_API_KEY),
        'ai_export_guidance': bool(GOOGLE_AI_API_KEY or GEMINI_API_KEY),
        'script_generation': bool(GEMINI_API_KEY),
        'voice_cloning': False,  # Premium feature for later
        'lip_sync': bool(GEMINI_API_KEY),  # Basic lip sync with Gemini
        'storage': bool(CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY),
    }
    
    # Stripe Configuration
    STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
    
    # Rate Limiting
    RATELIMIT_REQUESTS_PER_MINUTE = int(os.getenv('RATE_LIMIT_REQUESTS_PER_MINUTE', 100))
    RATELIMIT_REQUESTS_PER_HOUR = int(os.getenv('RATE_LIMIT_REQUESTS_PER_HOUR', 1000))
    
    # Celery Configuration
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/1')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2')
    
    # JWT Configuration
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
    
    # Email Configuration
    SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
    FROM_EMAIL = os.getenv('FROM_EMAIL', 'noreply@talkingphoto.ai')
    
    # Monitoring Configuration
    PROMETHEUS_METRICS_PORT = int(os.getenv('PROMETHEUS_METRICS_PORT', 8000))
    
    # Business Logic Configuration
    FREE_TIER_LIMIT = 3  # Free video generations
    STARTER_TIER_LIMIT = 30  # Starter tier limit
    PRO_TIER_LIMIT = 100  # Pro tier limit
    
    # Processing Configuration
    IMAGE_PROCESSING_TIMEOUT = 10  # seconds
    VIDEO_PROCESSING_TIMEOUT = 120  # seconds
    MAX_SCRIPT_LENGTH = 500  # characters


class DevelopmentConfig(Config):
    """Development environment configuration"""
    
    DEBUG = True
    TESTING = False
    
    # Relaxed security for development
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)
    
    # Development-specific settings
    SQLALCHEMY_ECHO = True  # Log SQL queries
    
    # File upload settings for development
    UPLOAD_FOLDER = 'uploads/dev'
    

class TestingConfig(Config):
    """Testing environment configuration"""
    
    TESTING = True
    DEBUG = True
    
    # Use in-memory database for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False
    
    # Fast token expiration for testing
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    
    # Mock external services
    MOCK_AI_SERVICES = True
    MOCK_STRIPE = True
    MOCK_S3 = True


class ProductionConfig(Config):
    """Production environment configuration"""
    
    DEBUG = False
    TESTING = False
    
    # Enhanced security for production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Strict CORS policy
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'https://talkingphoto.ai').split(',')
    
    # Production database optimizations
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'pool_size': 20,
        'max_overflow': 40
    }
    
    # Production file upload settings
    UPLOAD_FOLDER = '/app/uploads'
    
    # Stricter rate limiting
    RATELIMIT_REQUESTS_PER_MINUTE = 50
    RATELIMIT_REQUESTS_PER_HOUR = 500


class StagingConfig(ProductionConfig):
    """Staging environment configuration (inherits from Production)"""
    
    DEBUG = True  # Enable debug for staging testing
    
    # Less strict rate limiting for testing
    RATELIMIT_REQUESTS_PER_MINUTE = 100
    RATELIMIT_REQUESTS_PER_HOUR = 1000


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'staging': StagingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}