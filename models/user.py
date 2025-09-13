"""
TalkingPhoto AI MVP - User Authentication Models
GDPR-compliant user management with secure password handling
"""

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token
import uuid
from enum import Enum
from app import db


class UserStatus(Enum):
    """User account status enumeration"""
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    SUSPENDED = 'suspended'
    DELETED = 'deleted'


class SubscriptionTier(Enum):
    """User subscription tier enumeration"""
    FREE = 'free'
    STARTER = 'starter'
    PRO = 'pro'
    ENTERPRISE = 'enterprise'


class User(db.Model):
    """
    User model with GDPR compliance and secure authentication
    """
    __tablename__ = 'users'

    # Primary identification
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    
    # Profile information
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    profile_image_url = db.Column(db.String(255), nullable=True)
    
    # Account status and subscription
    status = db.Column(db.Enum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    subscription_tier = db.Column(db.Enum(SubscriptionTier), default=SubscriptionTier.FREE, nullable=False)
    
    # Authentication and security
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    email_verification_token = db.Column(db.String(128), nullable=True)
    password_reset_token = db.Column(db.String(128), nullable=True)
    password_reset_expires = db.Column(db.DateTime, nullable=True)
    
    # Usage tracking
    total_videos_generated = db.Column(db.Integer, default=0, nullable=False)
    monthly_videos_generated = db.Column(db.Integer, default=0, nullable=False)
    last_video_generation = db.Column(db.DateTime, nullable=True)
    
    # GDPR compliance
    gdpr_consent = db.Column(db.Boolean, default=False, nullable=False)
    gdpr_consent_date = db.Column(db.DateTime, nullable=True)
    data_retention_date = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    sessions = db.relationship('UserSession', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    uploaded_files = db.relationship('UploadedFile', backref='user', lazy='dynamic')
    video_generations = db.relationship('VideoGeneration', backref='user', lazy='dynamic')
    subscriptions = db.relationship('Subscription', backref='user', lazy='dynamic')
    usage_logs = db.relationship('UsageLog', backref='user', lazy='dynamic')

    def __init__(self, email, password, **kwargs):
        """Initialize user with secure password hashing"""
        self.email = email.lower().strip()
        self.set_password(password)
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def set_password(self, password):
        """Hash and set password securely"""
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        self.password_hash = generate_password_hash(
            password, 
            method='pbkdf2:sha256',
            salt_length=16
        )

    def check_password(self, password):
        """Verify password against hash"""
        return check_password_hash(self.password_hash, password)

    def generate_tokens(self):
        """Generate JWT access and refresh tokens"""
        additional_claims = {
            'user_id': self.id,
            'subscription_tier': self.subscription_tier.value,
            'email_verified': self.email_verified
        }
        
        access_token = create_access_token(
            identity=self.id,
            additional_claims=additional_claims
        )
        refresh_token = create_refresh_token(identity=self.id)
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token
        }

    def can_generate_video(self):
        """Check if user can generate another video based on subscription tier"""
        limits = {
            SubscriptionTier.FREE: 3,
            SubscriptionTier.STARTER: 30,
            SubscriptionTier.PRO: 100,
            SubscriptionTier.ENTERPRISE: float('inf')
        }
        
        monthly_limit = limits.get(self.subscription_tier, 0)
        return self.monthly_videos_generated < monthly_limit

    def increment_video_count(self):
        """Increment video generation counters"""
        self.total_videos_generated += 1
        self.monthly_videos_generated += 1
        self.last_video_generation = datetime.now(timezone.utc)

    def reset_monthly_usage(self):
        """Reset monthly usage counter (called by scheduled task)"""
        self.monthly_videos_generated = 0

    def mark_email_verified(self):
        """Mark user email as verified"""
        self.email_verified = True
        self.email_verification_token = None

    def set_gdpr_consent(self):
        """Record GDPR consent"""
        self.gdpr_consent = True
        self.gdpr_consent_date = datetime.now(timezone.utc)

    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary for API responses"""
        data = {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'profile_image_url': self.profile_image_url,
            'status': self.status.value,
            'subscription_tier': self.subscription_tier.value,
            'email_verified': self.email_verified,
            'total_videos_generated': self.total_videos_generated,
            'monthly_videos_generated': self.monthly_videos_generated,
            'last_video_generation': self.last_video_generation.isoformat() if self.last_video_generation else None,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
        
        if include_sensitive:
            data.update({
                'gdpr_consent': self.gdpr_consent,
                'gdpr_consent_date': self.gdpr_consent_date.isoformat() if self.gdpr_consent_date else None
            })
        
        return data

    def __repr__(self):
        return f'<User {self.email}>'


class UserSession(db.Model):
    """
    User session tracking for security and analytics
    """
    __tablename__ = 'user_sessions'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Session information
    jwt_token_id = db.Column(db.String(128), nullable=False, unique=True, index=True)
    refresh_token_id = db.Column(db.String(128), nullable=True, index=True)
    
    # Client information
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 support
    user_agent = db.Column(db.Text, nullable=True)
    device_type = db.Column(db.String(50), nullable=True)
    
    # Session status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    revoked_at = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    last_activity = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

    def __init__(self, user_id, jwt_token_id, expires_at, **kwargs):
        self.user_id = user_id
        self.jwt_token_id = jwt_token_id
        self.expires_at = expires_at
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def is_valid(self):
        """Check if session is valid and not expired"""
        return (
            self.is_active and 
            not self.revoked_at and 
            datetime.now(timezone.utc) < self.expires_at
        )

    def revoke(self):
        """Revoke the session"""
        self.is_active = False
        self.revoked_at = datetime.now(timezone.utc)

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now(timezone.utc)

    def to_dict(self):
        """Convert session to dictionary"""
        return {
            'id': self.id,
            'ip_address': self.ip_address,
            'device_type': self.device_type,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'expires_at': self.expires_at.isoformat()
        }

    def __repr__(self):
        return f'<UserSession {self.id} for User {self.user_id}>'