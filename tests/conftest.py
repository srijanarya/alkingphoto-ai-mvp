"""
TalkingPhoto AI MVP - Test Configuration
Pytest fixtures and test setup
"""

import pytest
import os
import tempfile
from datetime import datetime, timezone

from app import create_app, db
from models.user import User, SubscriptionTier
from models.file import UploadedFile, FileType, FileStatus
from models.video import VideoGeneration, AIProvider, VideoQuality, AspectRatio
from models.subscription import Subscription
from config import TestingConfig


@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    app = create_app('testing')
    
    with app.app_context():
        yield app


@pytest.fixture(scope='session')
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    """Create database session for each test"""
    with app.app_context():
        db.create_all()
        yield db.session
        db.session.rollback()
        db.drop_all()


@pytest.fixture
def test_user(db_session):
    """Create test user"""
    user = User(
        email='test@example.com',
        password='TestPassword123!',
        first_name='Test',
        last_name='User',
        subscription_tier=SubscriptionTier.FREE
    )
    user.set_gdpr_consent()
    user.mark_email_verified()
    
    db_session.add(user)
    db_session.commit()
    
    return user


@pytest.fixture
def premium_user(db_session):
    """Create premium test user"""
    user = User(
        email='premium@example.com',
        password='PremiumPassword123!',
        first_name='Premium',
        last_name='User',
        subscription_tier=SubscriptionTier.PRO
    )
    user.set_gdpr_consent()
    user.mark_email_verified()
    
    db_session.add(user)
    db_session.commit()
    
    return user


@pytest.fixture
def test_subscription(db_session, premium_user):
    """Create test subscription"""
    subscription = Subscription(
        user_id=premium_user.id,
        plan_name='pro',
        amount=2999,
        video_generation_limit=100
    )
    
    db_session.add(subscription)
    db_session.commit()
    
    return subscription


@pytest.fixture
def test_file(db_session, test_user):
    """Create test uploaded file"""
    uploaded_file = UploadedFile(
        user_id=test_user.id,
        original_filename='test_image.jpg',
        filename='test_image_unique.jpg',
        file_type=FileType.IMAGE,
        mime_type='image/jpeg',
        file_size=1024000,  # 1MB
        file_hash='abc123def456',
        width=1920,
        height=1080
    )
    
    db_session.add(uploaded_file)
    db_session.commit()
    
    return uploaded_file


@pytest.fixture
def test_video_generation(db_session, test_user, test_file):
    """Create test video generation"""
    video_gen = VideoGeneration(
        user_id=test_user.id,
        source_file_id=test_file.id,
        script_text="Hello, this is a test video script for our AI video generation.",
        ai_provider=AIProvider.MOCK,
        video_quality=VideoQuality.STANDARD,
        aspect_ratio=AspectRatio.LANDSCAPE
    )
    
    db_session.add(video_gen)
    db_session.commit()
    
    return video_gen


@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers for API calls"""
    login_data = {
        'email': test_user.email,
        'password': 'TestPassword123!'
    }
    
    response = client.post('/api/auth/login', json=login_data)
    assert response.status_code == 200
    
    tokens = response.json['tokens']
    return {
        'Authorization': f'Bearer {tokens["access_token"]}',
        'Content-Type': 'application/json'
    }


@pytest.fixture
def premium_auth_headers(client, premium_user):
    """Get authentication headers for premium user"""
    login_data = {
        'email': premium_user.email,
        'password': 'PremiumPassword123!'
    }
    
    response = client.post('/api/auth/login', json=login_data)
    assert response.status_code == 200
    
    tokens = response.json['tokens']
    return {
        'Authorization': f'Bearer {tokens["access_token"]}',
        'Content-Type': 'application/json'
    }


@pytest.fixture
def sample_image_data():
    """Create sample image data for testing"""
    # Create a minimal JPEG header for testing
    jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb'
    sample_data = jpeg_header + b'\x00' * 1000  # Pad with zeros
    
    return sample_data


@pytest.fixture
def temp_upload_dir():
    """Create temporary upload directory"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_stripe_customer():
    """Mock Stripe customer data"""
    return {
        'id': 'cus_test123',
        'email': 'test@example.com',
        'created': int(datetime.now(timezone.utc).timestamp()),
        'default_source': 'card_test123'
    }


@pytest.fixture
def mock_stripe_subscription():
    """Mock Stripe subscription data"""
    return {
        'id': 'sub_test123',
        'customer': 'cus_test123',
        'status': 'active',
        'current_period_start': int(datetime.now(timezone.utc).timestamp()),
        'current_period_end': int((datetime.now(timezone.utc).timestamp()) + 2592000),  # 30 days
        'items': {
            'data': [{
                'price': {
                    'id': 'price_test123',
                    'unit_amount': 299900,  # $2999.00 in cents
                    'currency': 'inr'
                }
            }]
        }
    }


@pytest.fixture
def mock_ai_response():
    """Mock AI service response"""
    return {
        'success': True,
        'output_file_path': 'test/path/video.mp4',
        'file_size': 5000000,  # 5MB
        'duration': 30,
        'cost': 4.50,
        'quality_metrics': {
            'lip_sync_accuracy': 95.0,
            'video_resolution': '1920x1080',
            'audio_quality': 'high'
        }
    }


@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Reset rate limits between tests"""
    # In a real implementation, this would clear Redis rate limit counters
    # For testing, we can mock or disable rate limiting
    yield
    # Cleanup rate limit state


@pytest.fixture
def test_export_instructions():
    """Sample export instructions data"""
    return {
        'platform': 'instagram',
        'workflow_type': 'product_demo',
        'video_info': {
            'duration': '30 seconds',
            'aspect_ratio': '16:9',
            'quality': 'standard',
            'resolution': '1920x1080'
        },
        'step_by_step_guide': [
            {
                'step': 1,
                'title': 'Download Your Generated Video',
                'description': 'Download the high-quality talking video from your dashboard',
                'estimated_time': '2 minutes'
            }
        ],
        'optimization_tips': [
            'Post during peak engagement hours',
            'Use relevant hashtags'
        ]
    }


# Test data constants
TEST_USER_DATA = {
    'valid_user': {
        'email': 'newuser@example.com',
        'password': 'ValidPassword123!',
        'first_name': 'New',
        'last_name': 'User',
        'gdpr_consent': True
    },
    'invalid_user': {
        'email': 'invalid-email',
        'password': 'weak',
        'gdpr_consent': False
    }
}

TEST_VIDEO_SCRIPT = "Hello everyone, this is a professional talking video generated using AI technology. Our platform helps you create engaging content quickly and easily."

TEST_FILE_DATA = {
    'valid_image': {
        'filename': 'test_image.jpg',
        'content_type': 'image/jpeg',
        'size': 1024000
    },
    'invalid_file': {
        'filename': 'test_file.exe',
        'content_type': 'application/x-executable',
        'size': 50000000  # 50MB - too large
    }
}

# API endpoint constants
API_ENDPOINTS = {
    'auth': '/api/auth',
    'upload': '/api/upload', 
    'video': '/api/video',
    'export': '/api/export',
    'user': '/api/user',
    'payment': '/api/payment'
}