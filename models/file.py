"""
TalkingPhoto AI MVP - File Upload Models
Secure file handling with metadata tracking and cloud storage
"""

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
import uuid
from enum import Enum
from app import db


class FileStatus(Enum):
    """File processing status enumeration"""
    UPLOADED = 'uploaded'
    PROCESSING = 'processing'
    ENHANCED = 'enhanced'
    FAILED = 'failed'
    DELETED = 'deleted'


class FileType(Enum):
    """File type enumeration"""
    IMAGE = 'image'
    VIDEO = 'video'
    THUMBNAIL = 'thumbnail'


class StorageProvider(Enum):
    """Storage provider enumeration"""
    LOCAL = 'local'
    S3 = 's3'
    CLOUDINARY = 'cloudinary'


class UploadedFile(db.Model):
    """
    File upload model with comprehensive metadata and security tracking
    """
    __tablename__ = 'uploaded_files'

    # Primary identification
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    
    # File information
    original_filename = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255), nullable=False)  # Sanitized/unique filename
    file_type = db.Column(db.Enum(FileType), nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    file_extension = db.Column(db.String(10), nullable=False)
    
    # File size and dimensions
    file_size = db.Column(db.Integer, nullable=False)  # Size in bytes
    width = db.Column(db.Integer, nullable=True)
    height = db.Column(db.Integer, nullable=True)
    duration = db.Column(db.Float, nullable=True)  # For videos, in seconds
    
    # Storage information
    storage_provider = db.Column(db.Enum(StorageProvider), default=StorageProvider.LOCAL, nullable=False)
    storage_path = db.Column(db.String(500), nullable=False)  # Local path or S3 key
    storage_url = db.Column(db.String(500), nullable=True)  # Public URL if applicable
    cdn_url = db.Column(db.String(500), nullable=True)  # CDN URL for fast delivery
    
    # Processing information
    status = db.Column(db.Enum(FileStatus), default=FileStatus.UPLOADED, nullable=False)
    processing_started_at = db.Column(db.DateTime, nullable=True)
    processing_completed_at = db.Column(db.DateTime, nullable=True)
    processing_error = db.Column(db.Text, nullable=True)
    
    # Enhancement data (for processed images)
    enhanced_file_id = db.Column(db.String(36), db.ForeignKey('uploaded_files.id'), nullable=True)
    enhancement_prompt = db.Column(db.Text, nullable=True)
    enhancement_settings = db.Column(db.JSON, nullable=True)
    
    # Security and validation
    file_hash = db.Column(db.String(128), nullable=False, index=True)  # SHA-256 hash
    virus_scan_status = db.Column(db.String(20), nullable=True)  # clean, infected, pending
    virus_scan_result = db.Column(db.Text, nullable=True)
    
    # Metadata
    exif_data = db.Column(db.JSON, nullable=True)  # EXIF data for images
    metadata = db.Column(db.JSON, nullable=True)  # Additional metadata
    
    # Usage tracking
    download_count = db.Column(db.Integer, default=0, nullable=False)
    last_accessed = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=True)  # Auto-deletion date
    deleted_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    enhanced_file = db.relationship('UploadedFile', remote_side=[id], backref='original_file')
    video_generations = db.relationship('VideoGeneration', backref='source_file', lazy='dynamic')

    def __init__(self, user_id, original_filename, filename, file_type, mime_type, file_size, file_hash, **kwargs):
        """Initialize uploaded file with required parameters"""
        self.user_id = user_id
        self.original_filename = original_filename
        self.filename = filename
        self.file_type = file_type
        self.mime_type = mime_type
        self.file_size = file_size
        self.file_hash = file_hash
        
        # Extract file extension
        if '.' in original_filename:
            self.file_extension = original_filename.rsplit('.', 1)[1].lower()
        else:
            self.file_extension = ''
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def mark_processing_started(self):
        """Mark file processing as started"""
        self.status = FileStatus.PROCESSING
        self.processing_started_at = datetime.now(timezone.utc)

    def mark_processing_completed(self, enhanced_file_id=None):
        """Mark file processing as completed"""
        self.status = FileStatus.ENHANCED
        self.processing_completed_at = datetime.now(timezone.utc)
        if enhanced_file_id:
            self.enhanced_file_id = enhanced_file_id

    def mark_processing_failed(self, error_message):
        """Mark file processing as failed"""
        self.status = FileStatus.FAILED
        self.processing_completed_at = datetime.now(timezone.utc)
        self.processing_error = error_message

    def mark_virus_scan_result(self, status, result=None):
        """Record virus scan results"""
        self.virus_scan_status = status
        self.virus_scan_result = result

    def increment_download_count(self):
        """Increment download counter and update last accessed"""
        self.download_count += 1
        self.last_accessed = datetime.now(timezone.utc)

    def get_file_size_mb(self):
        """Get file size in megabytes"""
        return round(self.file_size / (1024 * 1024), 2)

    def get_processing_duration(self):
        """Get processing duration in seconds"""
        if self.processing_started_at and self.processing_completed_at:
            return (self.processing_completed_at - self.processing_started_at).total_seconds()
        return None

    def is_image(self):
        """Check if file is an image"""
        return self.file_type == FileType.IMAGE

    def is_video(self):
        """Check if file is a video"""
        return self.file_type == FileType.VIDEO

    def is_processed(self):
        """Check if file has been processed"""
        return self.status in [FileStatus.ENHANCED, FileStatus.FAILED]

    def is_accessible(self):
        """Check if file is accessible (not deleted or expired)"""
        if self.status == FileStatus.DELETED or self.deleted_at:
            return False
        
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return False
        
        return True

    def get_public_url(self):
        """Get public URL for file access"""
        if self.cdn_url:
            return self.cdn_url
        elif self.storage_url:
            return self.storage_url
        else:
            # Generate signed URL for private files
            return self.generate_signed_url()

    def generate_signed_url(self, expiration_hours=1):
        """Generate signed URL for secure file access"""
        # Implementation depends on storage provider
        # For S3, use boto3 to generate presigned URLs
        # For local storage, implement token-based access
        pass

    def soft_delete(self):
        """Soft delete the file"""
        self.status = FileStatus.DELETED
        self.deleted_at = datetime.now(timezone.utc)

    def to_dict(self, include_sensitive=False):
        """Convert file to dictionary for API responses"""
        data = {
            'id': self.id,
            'original_filename': self.original_filename,
            'filename': self.filename,
            'file_type': self.file_type.value,
            'mime_type': self.mime_type,
            'file_extension': self.file_extension,
            'file_size': self.file_size,
            'file_size_mb': self.get_file_size_mb(),
            'width': self.width,
            'height': self.height,
            'duration': self.duration,
            'status': self.status.value,
            'public_url': self.get_public_url() if self.is_accessible() else None,
            'download_count': self.download_count,
            'created_at': self.created_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None
        }
        
        if include_sensitive:
            data.update({
                'storage_provider': self.storage_provider.value,
                'storage_path': self.storage_path,
                'file_hash': self.file_hash,
                'virus_scan_status': self.virus_scan_status,
                'processing_error': self.processing_error,
                'exif_data': self.exif_data,
                'metadata': self.metadata
            })
        
        return data

    def __repr__(self):
        return f'<UploadedFile {self.filename} ({self.file_type.value})>'