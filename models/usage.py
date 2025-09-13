"""
TalkingPhoto AI MVP - Usage Tracking Models
Comprehensive usage analytics and monitoring
"""

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
import uuid
from enum import Enum
from app import db


class ActionType(Enum):
    """User action type enumeration"""
    FILE_UPLOAD = 'file_upload'
    IMAGE_ENHANCEMENT = 'image_enhancement'
    VIDEO_GENERATION = 'video_generation'
    VIDEO_DOWNLOAD = 'video_download'
    EXPORT_INSTRUCTION = 'export_instruction'
    PAYMENT_MADE = 'payment_made'
    SUBSCRIPTION_UPGRADE = 'subscription_upgrade'
    SUBSCRIPTION_DOWNGRADE = 'subscription_downgrade'


class UsageLog(db.Model):
    """
    Comprehensive usage tracking for analytics and billing
    """
    __tablename__ = 'usage_logs'

    # Primary identification
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Action details
    action_type = db.Column(db.Enum(ActionType), nullable=False, index=True)
    resource_id = db.Column(db.String(36), nullable=True)  # ID of related resource (file, video, etc.)
    resource_type = db.Column(db.String(50), nullable=True)  # Type of resource
    
    # Request information
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    referer = db.Column(db.String(500), nullable=True)
    
    # Processing information
    processing_time_ms = db.Column(db.Integer, nullable=True)  # Processing time in milliseconds
    api_provider = db.Column(db.String(50), nullable=True)  # AI service provider used
    cost_incurred = db.Column(db.Numeric(10, 6), nullable=True)  # Cost in USD
    
    # Success/failure tracking
    success = db.Column(db.Boolean, nullable=False, default=True)
    error_message = db.Column(db.Text, nullable=True)
    error_code = db.Column(db.String(50), nullable=True)
    
    # Additional metadata
    metadata = db.Column(db.JSON, nullable=True)  # Store additional context
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    def __init__(self, user_id, action_type, **kwargs):
        """Initialize usage log entry"""
        self.user_id = user_id
        self.action_type = action_type
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    @classmethod
    def log_action(cls, user_id, action_type, success=True, **kwargs):
        """Create and save a usage log entry"""
        log_entry = cls(
            user_id=user_id,
            action_type=action_type,
            success=success,
            **kwargs
        )
        
        db.session.add(log_entry)
        db.session.commit()
        
        return log_entry

    @classmethod
    def get_user_usage_stats(cls, user_id, start_date=None, end_date=None):
        """Get usage statistics for a user"""
        query = cls.query.filter_by(user_id=user_id)
        
        if start_date:
            query = query.filter(cls.created_at >= start_date)
        if end_date:
            query = query.filter(cls.created_at <= end_date)
        
        logs = query.all()
        
        # Calculate statistics
        stats = {
            'total_actions': len(logs),
            'successful_actions': len([log for log in logs if log.success]),
            'failed_actions': len([log for log in logs if not log.success]),
            'action_breakdown': {},
            'total_cost': 0,
            'avg_processing_time': 0
        }
        
        # Action type breakdown
        for action_type in ActionType:
            count = len([log for log in logs if log.action_type == action_type])
            stats['action_breakdown'][action_type.value] = count
        
        # Cost calculation
        total_cost = sum([log.cost_incurred or 0 for log in logs])
        stats['total_cost'] = float(total_cost)
        
        # Average processing time
        processing_times = [log.processing_time_ms for log in logs if log.processing_time_ms]
        if processing_times:
            stats['avg_processing_time'] = sum(processing_times) / len(processing_times)
        
        return stats

    def to_dict(self):
        """Convert usage log to dictionary for API responses"""
        return {
            'id': self.id,
            'action_type': self.action_type.value,
            'resource_id': self.resource_id,
            'resource_type': self.resource_type,
            'processing_time_ms': self.processing_time_ms,
            'api_provider': self.api_provider,
            'cost_incurred': float(self.cost_incurred) if self.cost_incurred else None,
            'success': self.success,
            'error_message': self.error_message,
            'error_code': self.error_code,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<UsageLog {self.action_type.value} for User {self.user_id}>'