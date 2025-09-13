"""
TalkingPhoto AI MVP - File Upload Routes
Secure file upload with validation, virus scanning, and cloud storage
"""

import os
import hashlib
import magic
from PIL import Image, ExifTags
from flask import Blueprint, request, jsonify, current_app
from flask_restful import Api, Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, validate, ValidationError
from werkzeug.utils import secure_filename
from datetime import datetime, timezone
import structlog
import uuid

from app import db, limiter
from models.user import User
from models.file import UploadedFile, FileStatus, FileType, StorageProvider
from models.usage import UsageLog, ActionType
from services.file_service import FileService
from services.ai_service import AIService
from utils.security import get_client_info
from utils.validators import validate_file_extension, validate_file_size

# Create blueprint and API
upload_bp = Blueprint('upload', __name__)
upload_api = Api(upload_bp)
logger = structlog.get_logger()

# Validation Schemas
class FileUploadSchema(Schema):
    """File upload validation schema"""
    enhance_image = fields.Bool(required=False, default=True)
    processing_options = fields.Dict(required=False)


class FileListSchema(Schema):
    """File list query parameters schema"""
    page = fields.Int(required=False, default=1, validate=validate.Range(min=1))
    per_page = fields.Int(required=False, default=20, validate=validate.Range(min=1, max=100))
    file_type = fields.Str(required=False, validate=validate.OneOf(['image', 'video', 'thumbnail']))
    status = fields.Str(required=False)


# File Upload Resources
class FileUploadResource(Resource):
    """File upload endpoint with image enhancement"""
    
    decorators = [jwt_required(), limiter.limit("20 per minute")]
    
    def post(self):
        """Upload and optionally enhance image files"""
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return {'error': 'User not found'}, 404
            
            # Check if file is in request
            if 'file' not in request.files:
                return {'error': 'No file provided'}, 400
            
            file = request.files['file']
            if file.filename == '':
                return {'error': 'No file selected'}, 400
            
            # Validate form data
            form_data = request.form.to_dict()
            schema = FileUploadSchema()
            options = schema.load(form_data)
            
            # Get client information
            client_info = get_client_info(request)
            
            # Start timing for performance tracking
            start_time = datetime.now(timezone.utc)
            
            # Validate file
            validation_result = self._validate_file(file)
            if validation_result['error']:
                return validation_result, 400
            
            # Read file content and calculate hash
            file_content = file.read()
            file.seek(0)  # Reset file pointer
            
            file_hash = hashlib.sha256(file_content).hexdigest()
            
            # Check for duplicate files
            existing_file = UploadedFile.query.filter_by(
                user_id=user.id,
                file_hash=file_hash
            ).first()
            
            if existing_file and existing_file.is_accessible():
                return {
                    'message': 'File already exists',
                    'file': existing_file.to_dict()
                }, 200
            
            # Create secure filename
            original_filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{original_filename}"
            
            # Detect MIME type
            mime_type = magic.from_buffer(file_content, mime=True)
            
            # Extract image dimensions and EXIF data
            dimensions = None
            exif_data = None
            
            if mime_type.startswith('image/'):
                try:
                    with Image.open(file) as img:
                        dimensions = {'width': img.width, 'height': img.height}
                        
                        # Extract EXIF data
                        if hasattr(img, '_getexif') and img._getexif():
                            exif_data = {}
                            for tag_id, value in img._getexif().items():
                                tag = ExifTags.TAGS.get(tag_id, tag_id)
                                exif_data[tag] = str(value)
                        
                        file.seek(0)  # Reset for storage
                except Exception as e:
                    logger.warning("Failed to extract image metadata", error=str(e))
            
            # Create file record
            uploaded_file = UploadedFile(
                user_id=user.id,
                original_filename=original_filename,
                filename=unique_filename,
                file_type=FileType.IMAGE if mime_type.startswith('image/') else FileType.VIDEO,
                mime_type=mime_type,
                file_size=len(file_content),
                file_hash=file_hash,
                width=dimensions['width'] if dimensions else None,
                height=dimensions['height'] if dimensions else None,
                exif_data=exif_data,
                storage_provider=StorageProvider.S3 if current_app.config.get('S3_BUCKET_NAME') else StorageProvider.LOCAL
            )
            
            db.session.add(uploaded_file)
            db.session.flush()  # Get ID without committing
            
            # Perform virus scan
            virus_scan_result = self._scan_for_virus(file_content)
            uploaded_file.mark_virus_scan_result(
                virus_scan_result['status'],
                virus_scan_result.get('result')
            )
            
            if virus_scan_result['status'] == 'infected':
                uploaded_file.soft_delete()
                db.session.commit()
                
                return {
                    'error': 'File rejected',
                    'message': 'File failed security scan'
                }, 400
            
            # Store file
            file_service = FileService()
            storage_result = file_service.store_file(
                file_content=file_content,
                filename=unique_filename,
                content_type=mime_type
            )
            
            if not storage_result['success']:
                return {
                    'error': 'Storage failed',
                    'message': storage_result['error']
                }, 500
            
            # Update file record with storage information
            uploaded_file.storage_path = storage_result['path']
            uploaded_file.storage_url = storage_result.get('url')
            uploaded_file.cdn_url = storage_result.get('cdn_url')
            
            # Process image enhancement if requested
            enhanced_file = None
            if (options.get('enhance_image', True) and 
                uploaded_file.is_image() and 
                virus_scan_result['status'] == 'clean'):
                
                try:
                    enhanced_file = self._enhance_image(uploaded_file, options.get('processing_options', {}))
                except Exception as e:
                    logger.error("Image enhancement failed", 
                               file_id=uploaded_file.id, error=str(e))
                    # Continue without enhancement
            
            db.session.commit()
            
            # Calculate processing time
            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            
            # Log upload activity
            UsageLog.log_action(
                user_id=user.id,
                action_type=ActionType.FILE_UPLOAD,
                resource_id=uploaded_file.id,
                resource_type='file',
                success=True,
                processing_time_ms=int(processing_time),
                ip_address=client_info['ip_address'],
                user_agent=client_info['user_agent']
            )
            
            logger.info("File uploaded successfully", 
                       user_id=user.id, 
                       file_id=uploaded_file.id,
                       filename=original_filename)
            
            response = {
                'message': 'File uploaded successfully',
                'file': uploaded_file.to_dict(),
                'processing_time_ms': int(processing_time)
            }
            
            if enhanced_file:
                response['enhanced_file'] = enhanced_file.to_dict()
            
            return response, 201
            
        except ValidationError as e:
            return {'error': 'Validation failed', 'details': e.messages}, 400
        except Exception as e:
            logger.error("File upload failed", error=str(e))
            return {'error': 'Upload failed', 'message': 'Internal server error'}, 500
    
    def _validate_file(self, file):
        """Validate uploaded file"""
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        max_size = current_app.config.get('MAX_CONTENT_LENGTH', 10485760)  # 10MB
        if file_size > max_size:
            return {
                'error': True,
                'message': f'File too large. Maximum size: {max_size / 1024 / 1024:.1f}MB'
            }
        
        # Check file extension
        if not validate_file_extension(file.filename):
            allowed = ', '.join(current_app.config.get('ALLOWED_EXTENSIONS', []))
            return {
                'error': True,
                'message': f'Invalid file type. Allowed: {allowed}'
            }
        
        return {'error': False}
    
    def _scan_for_virus(self, file_content):
        """Scan file for viruses (mock implementation)"""
        # In production, integrate with actual virus scanning service
        # like ClamAV, VirusTotal, or cloud-based solutions
        
        # Mock implementation - check for suspicious patterns
        if len(file_content) == 0:
            return {'status': 'infected', 'result': 'Empty file'}
        
        # Check for common malicious file headers
        malicious_signatures = [
            b'<script',
            b'javascript:',
            b'eval(',
            b'document.write'
        ]
        
        for signature in malicious_signatures:
            if signature in file_content[:1024]:  # Check first 1KB
                return {'status': 'infected', 'result': 'Suspicious content detected'}
        
        return {'status': 'clean', 'result': 'No threats detected'}
    
    def _enhance_image(self, uploaded_file, processing_options):
        """Enhance image using AI service"""
        uploaded_file.mark_processing_started()
        db.session.commit()
        
        try:
            ai_service = AIService()
            enhancement_result = ai_service.enhance_image(
                file_id=uploaded_file.id,
                options=processing_options
            )
            
            if enhancement_result['success']:
                # Create enhanced file record
                enhanced_file = UploadedFile(
                    user_id=uploaded_file.user_id,
                    original_filename=f"enhanced_{uploaded_file.original_filename}",
                    filename=enhancement_result['filename'],
                    file_type=FileType.IMAGE,
                    mime_type=uploaded_file.mime_type,
                    file_size=enhancement_result['file_size'],
                    file_hash=enhancement_result['file_hash'],
                    width=enhancement_result.get('width'),
                    height=enhancement_result.get('height'),
                    storage_provider=uploaded_file.storage_provider,
                    storage_path=enhancement_result['storage_path'],
                    storage_url=enhancement_result.get('storage_url'),
                    cdn_url=enhancement_result.get('cdn_url'),
                    status=FileStatus.ENHANCED,
                    enhancement_prompt=enhancement_result.get('prompt'),
                    enhancement_settings=processing_options
                )
                
                db.session.add(enhanced_file)
                db.session.flush()
                
                uploaded_file.mark_processing_completed(enhanced_file.id)
                
                # Log enhancement activity
                UsageLog.log_action(
                    user_id=uploaded_file.user_id,
                    action_type=ActionType.IMAGE_ENHANCEMENT,
                    resource_id=enhanced_file.id,
                    resource_type='enhanced_file',
                    success=True,
                    cost_incurred=enhancement_result.get('cost', 0),
                    api_provider='nano_banana'
                )
                
                return enhanced_file
            else:
                uploaded_file.mark_processing_failed(enhancement_result['error'])
                raise Exception(enhancement_result['error'])
                
        except Exception as e:
            uploaded_file.mark_processing_failed(str(e))
            db.session.commit()
            raise


class FileListResource(Resource):
    """List user's uploaded files"""
    
    decorators = [jwt_required()]
    
    def get(self):
        """Get paginated list of user's files"""
        try:
            current_user_id = get_jwt_identity()
            
            # Validate query parameters
            schema = FileListSchema()
            params = schema.load(request.args.to_dict())
            
            # Build query
            query = UploadedFile.query.filter_by(user_id=current_user_id)
            
            # Apply filters
            if params.get('file_type'):
                file_type_enum = FileType(params['file_type'])
                query = query.filter(UploadedFile.file_type == file_type_enum)
            
            if params.get('status'):
                status_enum = FileStatus(params['status'])
                query = query.filter(UploadedFile.status == status_enum)
            
            # Exclude deleted files by default
            query = query.filter(UploadedFile.status != FileStatus.DELETED)
            
            # Order by creation date (newest first)
            query = query.order_by(UploadedFile.created_at.desc())
            
            # Paginate results
            page = params['page']
            per_page = params['per_page']
            pagination = query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            files = [file.to_dict() for file in pagination.items]
            
            return {
                'files': files,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'has_prev': pagination.has_prev,
                    'has_next': pagination.has_next
                }
            }, 200
            
        except ValidationError as e:
            return {'error': 'Validation failed', 'details': e.messages}, 400
        except Exception as e:
            logger.error("File list retrieval failed", error=str(e))
            return {'error': 'Failed to retrieve files'}, 500


class FileDetailsResource(Resource):
    """Get details of a specific file"""
    
    decorators = [jwt_required()]
    
    def get(self, file_id):
        """Get detailed information about a file"""
        try:
            current_user_id = get_jwt_identity()
            
            file = UploadedFile.query.filter_by(
                id=file_id,
                user_id=current_user_id
            ).first()
            
            if not file:
                return {'error': 'File not found'}, 404
            
            if not file.is_accessible():
                return {'error': 'File not accessible'}, 410
            
            # Update access tracking
            file.increment_download_count()
            db.session.commit()
            
            return {
                'file': file.to_dict(include_sensitive=False)
            }, 200
            
        except Exception as e:
            logger.error("File details retrieval failed", 
                        file_id=file_id, error=str(e))
            return {'error': 'Failed to retrieve file details'}, 500
    
    def delete(self, file_id):
        """Soft delete a file"""
        try:
            current_user_id = get_jwt_identity()
            
            file = UploadedFile.query.filter_by(
                id=file_id,
                user_id=current_user_id
            ).first()
            
            if not file:
                return {'error': 'File not found'}, 404
            
            if file.status == FileStatus.DELETED:
                return {'error': 'File already deleted'}, 410
            
            # Soft delete the file
            file.soft_delete()
            db.session.commit()
            
            logger.info("File deleted", user_id=current_user_id, file_id=file_id)
            
            return {'message': 'File deleted successfully'}, 200
            
        except Exception as e:
            logger.error("File deletion failed", 
                        file_id=file_id, error=str(e))
            return {'error': 'Failed to delete file'}, 500


# Register API resources
upload_api.add_resource(FileUploadResource, '/file')
upload_api.add_resource(FileListResource, '/files')
upload_api.add_resource(FileDetailsResource, '/file/<string:file_id>')