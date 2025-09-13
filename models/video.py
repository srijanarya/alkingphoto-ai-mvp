"""
TalkingPhoto AI MVP - Video Generation Models
Video processing workflow tracking and metadata
"""

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
import uuid
from enum import Enum
from app import db


class VideoStatus(Enum):
    """Video generation status enumeration"""
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


class VideoQuality(Enum):
    """Video quality tiers"""
    ECONOMY = 'economy'
    STANDARD = 'standard' 
    PREMIUM = 'premium'


class AspectRatio(Enum):
    """Video aspect ratios"""
    SQUARE = '1:1'
    PORTRAIT = '9:16'
    LANDSCAPE = '16:9'


class AIProvider(Enum):
    """AI service providers"""
    VEO3 = 'veo3'
    RUNWAY = 'runway'
    NANO_BANANA = 'nano_banana'
    MOCK = 'mock'  # For testing


class VideoGeneration(db.Model):
    """
    Video generation tracking with comprehensive metadata and cost analysis
    """
    __tablename__ = 'video_generations'

    # Primary identification
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    source_file_id = db.Column(db.String(36), db.ForeignKey('uploaded_files.id'), nullable=False)
    
    # Generation request parameters
    script_text = db.Column(db.Text, nullable=False)
    voice_settings = db.Column(db.JSON, nullable=True)
    video_quality = db.Column(db.Enum(VideoQuality), default=VideoQuality.STANDARD, nullable=False)
    aspect_ratio = db.Column(db.Enum(AspectRatio), default=AspectRatio.LANDSCAPE, nullable=False)
    duration_seconds = db.Column(db.Integer, default=30, nullable=False)
    
    # AI Provider information
    ai_provider = db.Column(db.Enum(AIProvider), nullable=False)
    provider_request_id = db.Column(db.String(255), nullable=True)
    provider_job_id = db.Column(db.String(255), nullable=True)
    fallback_used = db.Column(db.Boolean, default=False, nullable=False)
    
    # Processing status and timing
    status = db.Column(db.Enum(VideoStatus), default=VideoStatus.PENDING, nullable=False)
    processing_started_at = db.Column(db.DateTime, nullable=True)
    processing_completed_at = db.Column(db.DateTime, nullable=True)
    estimated_completion_time = db.Column(db.DateTime, nullable=True)
    
    # Results
    output_file_id = db.Column(db.String(36), db.ForeignKey('uploaded_files.id'), nullable=True)
    thumbnail_file_id = db.Column(db.String(36), db.ForeignKey('uploaded_files.id'), nullable=True)
    
    # Quality metrics
    lip_sync_accuracy = db.Column(db.Float, nullable=True)  # Percentage 0-100
    video_resolution = db.Column(db.String(20), nullable=True)  # e.g., "1920x1080"
    video_bitrate = db.Column(db.Integer, nullable=True)  # kbps
    audio_quality = db.Column(db.String(50), nullable=True)
    
    # Cost tracking
    processing_cost = db.Column(db.Numeric(10, 4), nullable=True)  # USD
    api_calls_made = db.Column(db.Integer, default=0, nullable=False)
    tokens_used = db.Column(db.Integer, nullable=True)
    
    # Error handling
    error_message = db.Column(db.Text, nullable=True)
    error_code = db.Column(db.String(50), nullable=True)
    retry_count = db.Column(db.Integer, default=0, nullable=False)
    max_retries = db.Column(db.Integer, default=3, nullable=False)
    
    # Metadata and settings
    generation_settings = db.Column(db.JSON, nullable=True)
    provider_response = db.Column(db.JSON, nullable=True)  # Store full provider response
    
    # Analytics
    download_count = db.Column(db.Integer, default=0, nullable=False)
    share_count = db.Column(db.Integer, default=0, nullable=False)
    last_accessed = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=True)  # Auto-deletion date
    
    # Relationships
    output_file = db.relationship('UploadedFile', foreign_keys=[output_file_id], backref='video_outputs')
    thumbnail_file = db.relationship('UploadedFile', foreign_keys=[thumbnail_file_id], backref='video_thumbnails')

    def __init__(self, user_id, source_file_id, script_text, ai_provider, **kwargs):
        """Initialize video generation request"""
        self.user_id = user_id
        self.source_file_id = source_file_id
        self.script_text = script_text
        self.ai_provider = ai_provider
        
        # Set defaults based on script length
        script_length = len(script_text)
        if script_length <= 100:
            self.duration_seconds = 15
        elif script_length <= 300:
            self.duration_seconds = 30
        else:
            self.duration_seconds = 60
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def mark_processing_started(self, provider_job_id=None, estimated_completion=None):
        """Mark video processing as started"""
        self.status = VideoStatus.PROCESSING
        self.processing_started_at = datetime.now(timezone.utc)
        
        if provider_job_id:
            self.provider_job_id = provider_job_id
        
        if estimated_completion:
            self.estimated_completion_time = estimated_completion

    def mark_processing_completed(self, output_file_id, thumbnail_file_id=None, **kwargs):
        """Mark video processing as completed"""
        self.status = VideoStatus.COMPLETED
        self.processing_completed_at = datetime.now(timezone.utc)
        self.output_file_id = output_file_id
        
        if thumbnail_file_id:
            self.thumbnail_file_id = thumbnail_file_id
        
        # Update quality metrics if provided
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def mark_processing_failed(self, error_message, error_code=None):
        """Mark video processing as failed"""
        self.status = VideoStatus.FAILED
        self.processing_completed_at = datetime.now(timezone.utc)
        self.error_message = error_message
        self.error_code = error_code

    def can_retry(self):
        """Check if generation can be retried"""
        return (
            self.status == VideoStatus.FAILED and 
            self.retry_count < self.max_retries
        )

    def increment_retry_count(self):
        """Increment retry counter"""
        self.retry_count += 1
        self.status = VideoStatus.PENDING  # Reset to pending for retry

    def mark_fallback_used(self, new_provider):
        """Mark that fallback provider was used"""
        self.fallback_used = True
        self.ai_provider = new_provider

    def get_processing_duration(self):
        """Get processing duration in seconds"""
        if self.processing_started_at and self.processing_completed_at:
            return (self.processing_completed_at - self.processing_started_at).total_seconds()
        return None

    def get_estimated_cost(self):
        """Calculate estimated cost based on provider and settings"""
        cost_per_second = {
            AIProvider.VEO3: 0.15,
            AIProvider.RUNWAY: 0.20,
            AIProvider.NANO_BANANA: 0.039,
            AIProvider.MOCK: 0.0
        }
        
        base_cost = cost_per_second.get(self.ai_provider, 0) * self.duration_seconds
        
        # Quality multiplier
        quality_multiplier = {
            VideoQuality.ECONOMY: 0.8,
            VideoQuality.STANDARD: 1.0,
            VideoQuality.PREMIUM: 1.5
        }
        
        return base_cost * quality_multiplier.get(self.video_quality, 1.0)

    def increment_download_count(self):
        """Increment download counter"""
        self.download_count += 1
        self.last_accessed = datetime.now(timezone.utc)

    def increment_share_count(self):
        """Increment share counter"""
        self.share_count += 1

    def is_completed(self):
        """Check if generation is completed successfully"""
        return self.status == VideoStatus.COMPLETED

    def is_processing(self):
        """Check if generation is currently processing"""
        return self.status == VideoStatus.PROCESSING

    def is_failed(self):
        """Check if generation failed"""
        return self.status == VideoStatus.FAILED

    def get_progress_percentage(self):
        """Get estimated progress percentage"""
        if self.status == VideoStatus.COMPLETED:
            return 100
        elif self.status == VideoStatus.FAILED:
            return -1
        elif self.status == VideoStatus.PROCESSING:
            if self.processing_started_at and self.estimated_completion_time:
                total_duration = (self.estimated_completion_time - self.processing_started_at).total_seconds()
                elapsed = (datetime.now(timezone.utc) - self.processing_started_at).total_seconds()
                return min(int((elapsed / total_duration) * 100), 95)
            else:
                return 50  # Generic processing percentage
        else:
            return 0

    def to_dict(self, include_sensitive=False):
        """Convert video generation to dictionary for API responses"""
        data = {
            'id': self.id,
            'script_text': self.script_text,
            'video_quality': self.video_quality.value,
            'aspect_ratio': self.aspect_ratio.value,
            'duration_seconds': self.duration_seconds,
            'ai_provider': self.ai_provider.value,
            'status': self.status.value,
            'processing_started_at': self.processing_started_at.isoformat() if self.processing_started_at else None,
            'processing_completed_at': self.processing_completed_at.isoformat() if self.processing_completed_at else None,
            'estimated_completion_time': self.estimated_completion_time.isoformat() if self.estimated_completion_time else None,
            'progress_percentage': self.get_progress_percentage(),
            'processing_duration': self.get_processing_duration(),
            'lip_sync_accuracy': self.lip_sync_accuracy,
            'video_resolution': self.video_resolution,
            'estimated_cost': float(self.get_estimated_cost()),
            'processing_cost': float(self.processing_cost) if self.processing_cost else None,
            'download_count': self.download_count,
            'share_count': self.share_count,
            'retry_count': self.retry_count,
            'fallback_used': self.fallback_used,
            'created_at': self.created_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None
        }
        
        if self.error_message:
            data['error_message'] = self.error_message
            data['error_code'] = self.error_code
        
        if include_sensitive:
            data.update({
                'provider_request_id': self.provider_request_id,
                'provider_job_id': self.provider_job_id,
                'api_calls_made': self.api_calls_made,
                'tokens_used': self.tokens_used,
                'generation_settings': self.generation_settings,
                'provider_response': self.provider_response
            })
        
        return data

    def __repr__(self):
        return f'<VideoGeneration {self.id} ({self.status.value})>'