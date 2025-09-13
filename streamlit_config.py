"""
TalkingPhoto AI MVP - Streamlit Configuration
Epic 4: User Experience & Interface Configuration
"""

import os
import streamlit as st
from dotenv import load_dotenv
from typing import Dict, List, Optional, Any
from pathlib import Path

# Load environment variables
load_dotenv()

class StreamlitConfig:
    """Centralized configuration for Streamlit application"""
    
    # Application Settings
    APP_TITLE = "TalkingPhoto AI MVP"
    APP_ICON = "🎬"
    APP_DESCRIPTION = "Transform photos into engaging videos with AI"
    APP_VERSION = "1.0.0"
    
    # API Configuration
    API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000/api')
    WS_URL = os.getenv('WS_URL', 'ws://localhost:5000/ws')
    FLASK_APP_URL = os.getenv('FLASK_APP_URL', 'http://localhost:5000')
    
    # Authentication
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-here')
    JWT_ALGORITHM = 'HS256'
    SESSION_TIMEOUT = 3600  # 1 hour in seconds
    
    # File Upload Settings
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp', 'bmp', 'tiff']
    UPLOAD_FOLDER = Path('./uploads')
    
    # Text Processing
    CHARACTER_LIMIT = 500
    MIN_TEXT_LENGTH = 10
    MAX_TEMPLATES = 20
    
    # Voice Configuration
    AVAILABLE_VOICES = {
        'sarah_professional': {
            'name': 'Sarah (Professional)',
            'gender': 'female',
            'language': 'en-US',
            'style': 'professional',
            'premium': True
        },
        'michael_friendly': {
            'name': 'Michael (Friendly)',
            'gender': 'male',
            'language': 'en-US',
            'style': 'friendly',
            'premium': False
        },
        'emma_energetic': {
            'name': 'Emma (Energetic)',
            'gender': 'female',
            'language': 'en-US',
            'style': 'energetic',
            'premium': True
        },
        'david_authoritative': {
            'name': 'David (Authoritative)',
            'gender': 'male',
            'language': 'en-US',
            'style': 'authoritative',
            'premium': True
        },
        'lisa_warm': {
            'name': 'Lisa (Warm)',
            'gender': 'female',
            'language': 'en-US',
            'style': 'warm',
            'premium': False
        },
        'james_confident': {
            'name': 'James (Confident)',
            'gender': 'male',
            'language': 'en-US',
            'style': 'confident',
            'premium': True
        }
    }
    
    # Video Generation Settings
    DEFAULT_VIDEO_RESOLUTION = (1920, 1080)
    SUPPORTED_RESOLUTIONS = [
        (1920, 1080),  # Full HD
        (1280, 720),   # HD
        (854, 480),    # SD
        (640, 360),    # Mobile
    ]
    
    VIDEO_FORMATS = ['mp4', 'webm', 'avi']
    MAX_VIDEO_DURATION = 120  # 2 minutes
    
    # UI Theme Configuration
    THEME_CONFIG = {
        'primaryColor': '#667eea',
        'backgroundColor': '#ffffff',
        'secondaryBackgroundColor': '#f0f2f6',
        'textColor': '#262730',
        'font': 'Helvetica, Arial, sans-serif'
    }
    
    # Progress Tracking
    PROGRESS_UPDATE_INTERVAL = 2  # seconds
    MAX_QUEUE_SIZE = 100
    ESTIMATED_GENERATION_TIME = 5  # minutes
    
    # WebSocket Configuration
    WS_RECONNECT_ATTEMPTS = 3
    WS_TIMEOUT = 30
    WS_PING_INTERVAL = 25
    
    # Error Messages
    ERROR_MESSAGES = {
        'upload_failed': 'Failed to upload photo. Please try again.',
        'invalid_file_type': 'Invalid file type. Please upload JPG, PNG, or WebP images.',
        'file_too_large': f'File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB.',
        'no_face_detected': 'No face detected in the photo. Please upload a clear photo with visible face.',
        'generation_failed': 'Video generation failed. Please try again.',
        'network_error': 'Network error. Please check your connection.',
        'auth_required': 'Please sign in to continue.',
        'insufficient_credits': 'Insufficient credits. Please upgrade your plan.',
        'rate_limit_exceeded': 'Rate limit exceeded. Please try again later.'
    }
    
    # Success Messages
    SUCCESS_MESSAGES = {
        'upload_success': 'Photo uploaded successfully!',
        'generation_started': 'Video generation started successfully!',
        'generation_completed': 'Video generated successfully!',
        'profile_updated': 'Profile updated successfully!',
        'template_saved': 'Template saved successfully!'
    }
    
    # Navigation Configuration
    NAVIGATION_PAGES = {
        'upload': {
            'icon': '📤',
            'title': 'Upload Photo',
            'description': 'Upload and manage your photos'
        },
        'generate': {
            'icon': '🎬',
            'title': 'Generate Video',
            'description': 'Create talking videos from your photos'
        },
        'dashboard': {
            'icon': '📊',
            'title': 'Dashboard',
            'description': 'Monitor video generation progress'
        },
        'history': {
            'icon': '📋',
            'title': 'History',
            'description': 'View your generation history'
        },
        'account': {
            'icon': '👤',
            'title': 'Account',
            'description': 'Manage your account settings'
        }
    }
    
    # Pricing Configuration
    PRICING_TIERS = {
        'free': {
            'name': 'Free',
            'price': 0,
            'credits_per_month': 5,
            'features': ['Basic voices', 'Standard quality', 'Community support']
        },
        'pro': {
            'name': 'Pro',
            'price': 9.99,
            'credits_per_month': 50,
            'features': ['Premium voices', 'HD quality', 'Priority support', 'Custom templates']
        },
        'enterprise': {
            'name': 'Enterprise',
            'price': 29.99,
            'credits_per_month': 200,
            'features': ['All voices', '4K quality', 'Dedicated support', 'API access', 'White-label']
        }
    }
    
    # Generation Cost Calculation
    COST_STRUCTURE = {
        'base_cost': 0.50,  # Base cost per video
        'character_cost': 0.001,  # Cost per character
        'premium_voice_multiplier': 1.5,
        'hd_quality_multiplier': 1.2,
        '4k_quality_multiplier': 2.0
    }
    
    # Analytics Configuration
    ANALYTICS_EVENTS = [
        'photo_upload',
        'video_generation_start',
        'video_generation_complete',
        'video_download',
        'voice_preview',
        'template_save',
        'template_load',
        'share_video'
    ]
    
    # Cache Configuration
    CACHE_TTL = 3600  # 1 hour
    MAX_CACHE_SIZE = 100  # Maximum cached items
    
    # Mobile Responsive Breakpoints
    MOBILE_BREAKPOINT = 768
    TABLET_BREAKPOINT = 1024
    DESKTOP_BREAKPOINT = 1200
    
    # Default Templates
    DEFAULT_TEMPLATES = [
        "Hello! Welcome to our presentation.",
        "Thank you for watching our video.",
        "We're excited to share this with you.",
        "Don't forget to subscribe and follow us!",
        "This is an important announcement.",
        "Let's dive into today's topic.",
        "I hope you find this helpful.",
        "Please feel free to reach out with questions."
    ]
    
    # Validation Rules
    VALIDATION_RULES = {
        'photo': {
            'min_resolution': (512, 512),
            'max_resolution': (4096, 4096),
            'aspect_ratio_tolerance': 0.1,
            'quality_threshold': 0.7
        },
        'text': {
            'min_length': MIN_TEXT_LENGTH,
            'max_length': CHARACTER_LIMIT,
            'forbidden_words': [],  # Add any restricted words
            'required_encoding': 'utf-8'
        }
    }
    
    @classmethod
    def get_streamlit_config(cls) -> Dict[str, Any]:
        """Get Streamlit-specific configuration"""
        return {
            'page_title': cls.APP_TITLE,
            'page_icon': cls.APP_ICON,
            'layout': 'wide',
            'initial_sidebar_state': 'expanded',
            'menu_items': {
                'Get Help': None,
                'Report a bug': None,
                'About': cls.APP_DESCRIPTION
            }
        }
    
    @classmethod
    def get_theme_config(cls) -> Dict[str, str]:
        """Get theme configuration for Streamlit"""
        return cls.THEME_CONFIG
    
    @classmethod
    def get_voice_options(cls, premium_only: bool = False) -> Dict[str, str]:
        """Get available voice options"""
        voices = cls.AVAILABLE_VOICES
        if premium_only:
            voices = {k: v for k, v in voices.items() if v['premium']}
        return {k: v['name'] for k, v in voices.items()}
    
    @classmethod
    def calculate_video_cost(cls, text_length: int, voice_type: str, quality: str = 'standard') -> float:
        """Calculate video generation cost"""
        base_cost = cls.COST_STRUCTURE['base_cost']
        character_cost = text_length * cls.COST_STRUCTURE['character_cost']
        
        # Voice premium multiplier
        voice_multiplier = 1.0
        if voice_type in cls.AVAILABLE_VOICES and cls.AVAILABLE_VOICES[voice_type]['premium']:
            voice_multiplier = cls.COST_STRUCTURE['premium_voice_multiplier']
        
        # Quality multiplier
        quality_multiplier = 1.0
        if quality == 'hd':
            quality_multiplier = cls.COST_STRUCTURE['hd_quality_multiplier']
        elif quality == '4k':
            quality_multiplier = cls.COST_STRUCTURE['4k_quality_multiplier']
        
        total_cost = (base_cost + character_cost) * voice_multiplier * quality_multiplier
        return round(total_cost, 2)
    
    @classmethod
    def is_mobile_device(cls) -> bool:
        """Check if the current device is mobile (simplified)"""
        # In a real implementation, this would check user agent or screen size
        return False  # Placeholder
    
    @classmethod
    def get_upload_config(cls) -> Dict[str, Any]:
        """Get file upload configuration"""
        return {
            'max_file_size': cls.MAX_FILE_SIZE,
            'allowed_extensions': cls.ALLOWED_EXTENSIONS,
            'upload_folder': cls.UPLOAD_FOLDER
        }
    
    @classmethod
    def get_error_message(cls, error_type: str) -> str:
        """Get localized error message"""
        return cls.ERROR_MESSAGES.get(error_type, 'An unexpected error occurred.')
    
    @classmethod
    def get_success_message(cls, success_type: str) -> str:
        """Get localized success message"""
        return cls.SUCCESS_MESSAGES.get(success_type, 'Operation completed successfully.')


# Environment-specific configurations
class DevelopmentConfig(StreamlitConfig):
    """Development environment configuration"""
    DEBUG = True
    TESTING = False
    API_BASE_URL = 'http://localhost:5000/api'
    WS_URL = 'ws://localhost:5000/ws'


class ProductionConfig(StreamlitConfig):
    """Production environment configuration"""
    DEBUG = False
    TESTING = False
    API_BASE_URL = os.getenv('PROD_API_BASE_URL', 'https://api.talkingphoto.ai/api')
    WS_URL = os.getenv('PROD_WS_URL', 'wss://api.talkingphoto.ai/ws')


class TestingConfig(StreamlitConfig):
    """Testing environment configuration"""
    DEBUG = True
    TESTING = True
    API_BASE_URL = 'http://localhost:5001/api'
    WS_URL = 'ws://localhost:5001/ws'


def get_config() -> StreamlitConfig:
    """Get configuration based on environment"""
    env = os.getenv('STREAMLIT_ENV', 'development').lower()
    
    if env == 'production':
        return ProductionConfig()
    elif env == 'testing':
        return TestingConfig()
    else:
        return DevelopmentConfig()


# Initialize configuration
config = get_config()