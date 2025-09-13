"""
TalkingPhoto AI MVP - Video Generation Routes
AI-powered video generation with fallback providers and cost optimization
"""

from flask import Blueprint, request, jsonify, current_app
from flask_restful import Api, Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, validate, ValidationError
from datetime import datetime, timezone
import structlog
import uuid

from app import db, limiter
from models.user import User
from models.file import UploadedFile, FileStatus, FileType
from models.video import VideoGeneration, VideoStatus, VideoQuality, AspectRatio, AIProvider
from models.usage import UsageLog, ActionType
from services.ai_service import AIService
from services.queue_service import QueueService
from utils.security import get_client_info

# Create blueprint and API
video_bp = Blueprint('video', __name__)
video_api = Api(video_bp)
logger = structlog.get_logger()

# Validation Schemas
class VideoGenerationSchema(Schema):
    """Video generation request validation schema"""
    source_file_id = fields.Str(required=True, validate=validate.Length(equal=36))
    script_text = fields.Str(required=True, validate=validate.Length(min=1, max=500))
    video_quality = fields.Str(required=False, default='standard', 
                              validate=validate.OneOf(['economy', 'standard', 'premium']))
    aspect_ratio = fields.Str(required=False, default='16:9', 
                             validate=validate.OneOf(['1:1', '9:16', '16:9']))
    voice_settings = fields.Dict(required=False)
    ai_provider = fields.Str(required=False, 
                            validate=validate.OneOf(['veo3', 'runway', 'auto']))


class VideoListSchema(Schema):
    """Video list query parameters schema"""
    page = fields.Int(required=False, default=1, validate=validate.Range(min=1))
    per_page = fields.Int(required=False, default=20, validate=validate.Range(min=1, max=100))
    status = fields.Str(required=False)
    ai_provider = fields.Str(required=False)


# Video Generation Resources
class GenerateVideoResource(Resource):
    """Video generation endpoint with AI service routing"""
    
    decorators = [jwt_required(), limiter.limit("10 per hour")]
    
    def post(self):
        """Generate talking video from photo and script"""
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return {'error': 'User not found'}, 404
            
            # Check if user can generate more videos
            if not user.can_generate_video():
                return {
                    'error': 'Quota exceeded',
                    'message': f'You have reached your monthly limit of {user.subscription_tier.value} videos',
                    'upgrade_required': True
                }, 403
            
            # Validate request data
            schema = VideoGenerationSchema()
            data = schema.load(request.get_json() or {})
            
            # Get client information
            client_info = get_client_info(request)
            
            # Verify source file exists and belongs to user
            source_file = UploadedFile.query.filter_by(
                id=data['source_file_id'],
                user_id=current_user_id
            ).first()
            
            if not source_file:
                return {'error': 'Source file not found'}, 404
            
            if not source_file.is_accessible() or source_file.file_type != FileType.IMAGE:
                return {'error': 'Invalid source file'}, 400
            
            if source_file.status == FileStatus.PROCESSING:
                return {
                    'error': 'Source file still processing',
                    'message': 'Please wait for image enhancement to complete'
                }, 409
            
            # Determine AI provider
            ai_provider = self._select_ai_provider(
                data.get('ai_provider', 'auto'),
                data['video_quality']
            )
            
            # Create video generation record
            video_generation = VideoGeneration(
                user_id=current_user_id,
                source_file_id=source_file.id,
                script_text=data['script_text'],
                ai_provider=ai_provider,
                video_quality=VideoQuality(data['video_quality']),
                aspect_ratio=AspectRatio(data['aspect_ratio']),
                voice_settings=data.get('voice_settings', {}),
                generation_settings={
                    'client_info': client_info,
                    'request_timestamp': datetime.now(timezone.utc).isoformat(),
                    'source_file_info': {
                        'filename': source_file.filename,
                        'dimensions': f"{source_file.width}x{source_file.height}" if source_file.width else None
                    }
                }
            )
            
            db.session.add(video_generation)
            db.session.flush()  # Get ID without committing
            
            # Queue video generation job
            try:
                queue_service = QueueService()
                job_id = queue_service.queue_video_generation(video_generation.id)
                video_generation.provider_job_id = job_id
                
                # Estimate completion time based on provider and quality
                estimated_duration = self._estimate_processing_time(ai_provider, data['video_quality'])
                video_generation.estimated_completion_time = (
                    datetime.now(timezone.utc) + estimated_duration
                )
                
            except Exception as e:
                logger.error("Failed to queue video generation", 
                           video_id=video_generation.id, error=str(e))
                return {
                    'error': 'Generation queue failed',
                    'message': 'Unable to process request at this time'
                }, 503
            
            # Update user video count
            user.increment_video_count()
            
            db.session.commit()
            
            # Log generation request
            UsageLog.log_action(
                user_id=current_user_id,
                action_type=ActionType.VIDEO_GENERATION,
                resource_id=video_generation.id,
                resource_type='video_generation',
                success=True,
                api_provider=ai_provider.value,
                ip_address=client_info['ip_address'],
                user_agent=client_info['user_agent']
            )
            
            logger.info("Video generation queued", 
                       user_id=current_user_id,
                       video_id=video_generation.id,
                       ai_provider=ai_provider.value)
            
            return {
                'message': 'Video generation started',
                'video_generation': video_generation.to_dict(),
                'estimated_completion': video_generation.estimated_completion_time.isoformat()
            }, 202
            
        except ValidationError as e:
            return {'error': 'Validation failed', 'details': e.messages}, 400
        except Exception as e:
            logger.error("Video generation request failed", error=str(e))
            return {'error': 'Generation request failed', 'message': 'Internal server error'}, 500
    
    def _select_ai_provider(self, requested_provider, quality):
        """Select optimal AI provider based on request and availability"""
        if requested_provider != 'auto':
            try:
                return AIProvider(requested_provider)
            except ValueError:
                pass  # Fall back to auto selection
        
        # Auto selection based on cost and quality
        if quality == 'economy':
            # Prefer cheapest option
            return AIProvider.NANO_BANANA
        elif quality == 'premium':
            # Prefer highest quality
            return AIProvider.RUNWAY
        else:
            # Balance of cost and quality
            return AIProvider.VEO3
    
    def _estimate_processing_time(self, ai_provider, quality):
        """Estimate processing time based on provider and quality"""
        from datetime import timedelta
        
        base_times = {
            AIProvider.VEO3: timedelta(seconds=45),
            AIProvider.RUNWAY: timedelta(seconds=60),
            AIProvider.NANO_BANANA: timedelta(seconds=30),
            AIProvider.MOCK: timedelta(seconds=5)
        }
        
        quality_multipliers = {
            'economy': 0.8,
            'standard': 1.0,
            'premium': 1.5
        }
        
        base_time = base_times.get(ai_provider, timedelta(seconds=45))
        multiplier = quality_multipliers.get(quality, 1.0)
        
        return timedelta(seconds=int(base_time.total_seconds() * multiplier))


class VideoListResource(Resource):
    """List user's video generations"""
    
    decorators = [jwt_required()]
    
    def get(self):
        """Get paginated list of user's video generations"""
        try:
            current_user_id = get_jwt_identity()
            
            # Validate query parameters
            schema = VideoListSchema()
            params = schema.load(request.args.to_dict())
            
            # Build query
            query = VideoGeneration.query.filter_by(user_id=current_user_id)
            
            # Apply filters
            if params.get('status'):
                try:
                    status_enum = VideoStatus(params['status'])
                    query = query.filter(VideoGeneration.status == status_enum)
                except ValueError:
                    return {'error': 'Invalid status filter'}, 400
            
            if params.get('ai_provider'):
                try:
                    provider_enum = AIProvider(params['ai_provider'])
                    query = query.filter(VideoGeneration.ai_provider == provider_enum)
                except ValueError:
                    return {'error': 'Invalid provider filter'}, 400
            
            # Order by creation date (newest first)
            query = query.order_by(VideoGeneration.created_at.desc())
            
            # Paginate results
            page = params['page']
            per_page = params['per_page']
            pagination = query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            videos = [video.to_dict() for video in pagination.items]
            
            return {
                'videos': videos,
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
            logger.error("Video list retrieval failed", error=str(e))
            return {'error': 'Failed to retrieve videos'}, 500


class VideoDetailsResource(Resource):
    """Get details of a specific video generation"""
    
    decorators = [jwt_required()]
    
    def get(self, video_id):
        """Get detailed information about a video generation"""
        try:
            current_user_id = get_jwt_identity()
            
            video = VideoGeneration.query.filter_by(
                id=video_id,
                user_id=current_user_id
            ).first()
            
            if not video:
                return {'error': 'Video generation not found'}, 404
            
            # Update access tracking if completed
            if video.is_completed():
                video.increment_download_count()
                db.session.commit()
            
            return {
                'video_generation': video.to_dict()
            }, 200
            
        except Exception as e:
            logger.error("Video details retrieval failed", 
                        video_id=video_id, error=str(e))
            return {'error': 'Failed to retrieve video details'}, 500


class VideoStatusResource(Resource):
    """Get real-time status of video generation"""
    
    decorators = [jwt_required()]
    
    def get(self, video_id):
        """Get current status and progress of video generation"""
        try:
            current_user_id = get_jwt_identity()
            
            video = VideoGeneration.query.filter_by(
                id=video_id,
                user_id=current_user_id
            ).first()
            
            if not video:
                return {'error': 'Video generation not found'}, 404
            
            # Get updated status from AI provider if still processing
            if video.is_processing():
                try:
                    ai_service = AIService()
                    updated_status = ai_service.get_generation_status(video)
                    
                    if updated_status['status_changed']:
                        # Update database with new status
                        if updated_status['status'] == 'completed':
                            video.mark_processing_completed(
                                output_file_id=updated_status['output_file_id'],
                                **updated_status.get('quality_metrics', {})
                            )
                        elif updated_status['status'] == 'failed':
                            video.mark_processing_failed(
                                updated_status['error_message'],
                                updated_status.get('error_code')
                            )
                        
                        db.session.commit()
                except Exception as e:
                    logger.error("Failed to get updated status from AI provider", 
                               video_id=video_id, error=str(e))
            
            return {
                'video_id': video_id,
                'status': video.status.value,
                'progress_percentage': video.get_progress_percentage(),
                'estimated_completion_time': video.estimated_completion_time.isoformat() if video.estimated_completion_time else None,
                'processing_duration': video.get_processing_duration(),
                'error_message': video.error_message if video.is_failed() else None
            }, 200
            
        except Exception as e:
            logger.error("Video status retrieval failed", 
                        video_id=video_id, error=str(e))
            return {'error': 'Failed to retrieve video status'}, 500


class VideoDownloadResource(Resource):
    """Download completed video"""
    
    decorators = [jwt_required()]
    
    def get(self, video_id):
        """Get download URL for completed video"""
        try:
            current_user_id = get_jwt_identity()
            
            video = VideoGeneration.query.filter_by(
                id=video_id,
                user_id=current_user_id
            ).first()
            
            if not video:
                return {'error': 'Video generation not found'}, 404
            
            if not video.is_completed():
                return {
                    'error': 'Video not ready',
                    'message': 'Video generation is not completed',
                    'status': video.status.value
                }, 409
            
            if not video.output_file:
                return {'error': 'Output file not found'}, 404
            
            # Generate signed download URL
            download_url = video.output_file.get_public_url()
            
            if not download_url:
                return {'error': 'Download URL generation failed'}, 500
            
            # Update download tracking
            video.increment_download_count()
            video.output_file.increment_download_count()
            
            db.session.commit()
            
            # Log download activity
            UsageLog.log_action(
                user_id=current_user_id,
                action_type=ActionType.VIDEO_DOWNLOAD,
                resource_id=video_id,
                resource_type='video_generation',
                success=True
            )
            
            return {
                'download_url': download_url,
                'filename': video.output_file.original_filename,
                'file_size': video.output_file.file_size,
                'expires_in_hours': 1  # URL expiration time
            }, 200
            
        except Exception as e:
            logger.error("Video download failed", 
                        video_id=video_id, error=str(e))
            return {'error': 'Download failed'}, 500


class RetryVideoResource(Resource):
    """Retry failed video generation"""
    
    decorators = [jwt_required()]
    
    def post(self, video_id):
        """Retry a failed video generation"""
        try:
            current_user_id = get_jwt_identity()
            
            video = VideoGeneration.query.filter_by(
                id=video_id,
                user_id=current_user_id
            ).first()
            
            if not video:
                return {'error': 'Video generation not found'}, 404
            
            if not video.can_retry():
                return {
                    'error': 'Cannot retry',
                    'message': f'Video cannot be retried (status: {video.status.value}, retries: {video.retry_count}/{video.max_retries})'
                }, 400
            
            # Increment retry count and reset status
            video.increment_retry_count()
            
            # Consider using fallback provider for retry
            if video.retry_count > 1 and not video.fallback_used:
                # Switch to fallback provider
                fallback_provider = self._get_fallback_provider(video.ai_provider)
                if fallback_provider:
                    video.mark_fallback_used(fallback_provider)
            
            # Queue retry job
            queue_service = QueueService()
            job_id = queue_service.queue_video_generation(video_id)
            video.provider_job_id = job_id
            
            db.session.commit()
            
            logger.info("Video generation retry queued", 
                       video_id=video_id, retry_count=video.retry_count)
            
            return {
                'message': 'Video generation retry queued',
                'video_generation': video.to_dict()
            }, 200
            
        except Exception as e:
            logger.error("Video retry failed", 
                        video_id=video_id, error=str(e))
            return {'error': 'Retry failed'}, 500
    
    def _get_fallback_provider(self, current_provider):
        """Get fallback provider for retry"""
        fallbacks = {
            AIProvider.VEO3: AIProvider.RUNWAY,
            AIProvider.RUNWAY: AIProvider.NANO_BANANA,
            AIProvider.NANO_BANANA: AIProvider.VEO3
        }
        return fallbacks.get(current_provider)


# Register API resources
video_api.add_resource(GenerateVideoResource, '/generate')
video_api.add_resource(VideoListResource, '/list')
video_api.add_resource(VideoDetailsResource, '/details/<string:video_id>')
video_api.add_resource(VideoStatusResource, '/status/<string:video_id>')
video_api.add_resource(VideoDownloadResource, '/download/<string:video_id>')
video_api.add_resource(RetryVideoResource, '/retry/<string:video_id>')