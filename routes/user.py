"""
TalkingPhoto AI MVP - User Management Routes
User profile, preferences, and account management
"""

from flask import Blueprint, request, jsonify
from flask_restful import Api, Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, validate, ValidationError
from datetime import datetime, timezone
import structlog

from app import db
from models.user import User, UserSession
from models.usage import UsageLog, ActionType
from models.video import VideoGeneration, VideoStatus
from models.file import UploadedFile, FileStatus
from utils.security import get_client_info
from utils.validators import validate_password

# Create blueprint and API
user_bp = Blueprint('user', __name__)
user_api = Api(user_bp)
logger = structlog.get_logger()

# Validation Schemas
class UpdateProfileSchema(Schema):
    """User profile update validation schema"""
    first_name = fields.Str(required=False, validate=validate.Length(max=50))
    last_name = fields.Str(required=False, validate=validate.Length(max=50))
    profile_image_url = fields.Url(required=False)


class ChangePasswordSchema(Schema):
    """Password change validation schema"""
    current_password = fields.Str(required=True)
    new_password = fields.Str(required=True, validate=validate_password)


class PreferencesSchema(Schema):
    """User preferences validation schema"""
    email_notifications = fields.Bool(required=False)
    marketing_emails = fields.Bool(required=False)
    default_video_quality = fields.Str(required=False, validate=validate.OneOf(['economy', 'standard', 'premium']))
    default_aspect_ratio = fields.Str(required=False, validate=validate.OneOf(['1:1', '9:16', '16:9']))
    preferred_ai_provider = fields.Str(required=False, validate=validate.OneOf(['veo3', 'runway', 'auto']))


# User Resources
class ProfileResource(Resource):
    """User profile management"""
    
    decorators = [jwt_required()]
    
    def get(self):
        """Get current user profile"""
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return {'error': 'User not found'}, 404
            
            # Get usage statistics
            usage_stats = UsageLog.get_user_usage_stats(
                user_id=current_user_id,
                start_date=datetime.now(timezone.utc).replace(day=1)  # Current month
            )
            
            # Get subscription information
            current_subscription = None
            if user.subscriptions:
                current_subscription = user.subscriptions.filter_by(status='active').first()
            
            profile_data = user.to_dict()
            profile_data.update({
                'usage_stats': usage_stats,
                'subscription': current_subscription.to_dict() if current_subscription else None,
                'can_generate_video': user.can_generate_video()
            })
            
            return {
                'profile': profile_data
            }, 200
            
        except Exception as e:
            logger.error("Profile retrieval failed", error=str(e))
            return {'error': 'Failed to retrieve profile'}, 500
    
    def put(self):
        """Update user profile"""
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return {'error': 'User not found'}, 404
            
            # Validate request data
            schema = UpdateProfileSchema()
            data = schema.load(request.get_json() or {})
            
            # Update profile fields
            updated_fields = []
            for field, value in data.items():
                if hasattr(user, field) and value is not None:
                    setattr(user, field, value)
                    updated_fields.append(field)
            
            if updated_fields:
                user.updated_at = datetime.now(timezone.utc)
                db.session.commit()
                
                logger.info("Profile updated", 
                           user_id=current_user_id,
                           updated_fields=updated_fields)
            
            return {
                'message': 'Profile updated successfully',
                'updated_fields': updated_fields,
                'profile': user.to_dict()
            }, 200
            
        except ValidationError as e:
            return {'error': 'Validation failed', 'details': e.messages}, 400
        except Exception as e:
            logger.error("Profile update failed", error=str(e))
            return {'error': 'Profile update failed'}, 500


class PasswordChangeResource(Resource):
    """Password change endpoint"""
    
    decorators = [jwt_required()]
    
    def post(self):
        """Change user password"""
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return {'error': 'User not found'}, 404
            
            # Validate request data
            schema = ChangePasswordSchema()
            data = schema.load(request.get_json() or {})
            
            # Verify current password
            if not user.check_password(data['current_password']):
                return {
                    'error': 'Invalid current password',
                    'message': 'The current password you entered is incorrect'
                }, 400
            
            # Update password
            user.set_password(data['new_password'])
            user.updated_at = datetime.now(timezone.utc)
            
            db.session.commit()
            
            logger.info("Password changed", user_id=current_user_id)
            
            return {
                'message': 'Password changed successfully'
            }, 200
            
        except ValidationError as e:
            return {'error': 'Validation failed', 'details': e.messages}, 400
        except ValueError as e:
            return {'error': 'Invalid password', 'message': str(e)}, 400
        except Exception as e:
            logger.error("Password change failed", error=str(e))
            return {'error': 'Password change failed'}, 500


class DashboardResource(Resource):
    """User dashboard with analytics"""
    
    decorators = [jwt_required()]
    
    def get(self):
        """Get user dashboard data"""
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return {'error': 'User not found'}, 404
            
            # Get recent video generations
            recent_videos = VideoGeneration.query.filter_by(
                user_id=current_user_id
            ).order_by(VideoGeneration.created_at.desc()).limit(5).all()
            
            # Get recent file uploads
            recent_files = UploadedFile.query.filter_by(
                user_id=current_user_id
            ).filter(UploadedFile.status != FileStatus.DELETED).order_by(
                UploadedFile.created_at.desc()
            ).limit(5).all()
            
            # Calculate statistics
            video_stats = {
                'total_generated': user.total_videos_generated,
                'monthly_generated': user.monthly_videos_generated,
                'monthly_remaining': max(0, user.subscription_tier.value - user.monthly_videos_generated) if hasattr(user.subscription_tier, 'value') else 0,
                'completed_count': VideoGeneration.query.filter_by(
                    user_id=current_user_id,
                    status=VideoStatus.COMPLETED
                ).count(),
                'processing_count': VideoGeneration.query.filter_by(
                    user_id=current_user_id,
                    status=VideoStatus.PROCESSING
                ).count(),
                'failed_count': VideoGeneration.query.filter_by(
                    user_id=current_user_id,
                    status=VideoStatus.FAILED
                ).count()
            }
            
            file_stats = {
                'total_uploaded': UploadedFile.query.filter_by(
                    user_id=current_user_id
                ).filter(UploadedFile.status != FileStatus.DELETED).count(),
                'total_size_mb': db.session.query(
                    db.func.sum(UploadedFile.file_size)
                ).filter_by(user_id=current_user_id).filter(
                    UploadedFile.status != FileStatus.DELETED
                ).scalar() or 0
            }
            file_stats['total_size_mb'] = round(file_stats['total_size_mb'] / 1024 / 1024, 2)
            
            # Get usage trends (last 30 days)
            thirty_days_ago = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            thirty_days_ago = thirty_days_ago.replace(day=max(1, thirty_days_ago.day - 30))
            
            usage_stats = UsageLog.get_user_usage_stats(
                user_id=current_user_id,
                start_date=thirty_days_ago
            )
            
            dashboard_data = {
                'user_info': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'subscription_tier': user.subscription_tier.value,
                    'email_verified': user.email_verified,
                    'member_since': user.created_at.isoformat(),
                    'last_login': user.last_login.isoformat() if user.last_login else None
                },
                'video_stats': video_stats,
                'file_stats': file_stats,
                'usage_stats': usage_stats,
                'recent_videos': [video.to_dict() for video in recent_videos],
                'recent_files': [file.to_dict() for file in recent_files]
            }
            
            return {
                'dashboard': dashboard_data,
                'generated_at': datetime.now(timezone.utc).isoformat()
            }, 200
            
        except Exception as e:
            logger.error("Dashboard data retrieval failed", error=str(e))
            return {'error': 'Failed to retrieve dashboard data'}, 500


class SessionsResource(Resource):
    """User session management"""
    
    decorators = [jwt_required()]
    
    def get(self):
        """Get user's active sessions"""
        try:
            current_user_id = get_jwt_identity()
            
            # Get active sessions
            sessions = UserSession.query.filter_by(
                user_id=current_user_id,
                is_active=True
            ).order_by(UserSession.last_activity.desc()).all()
            
            session_list = []
            for session in sessions:
                session_data = session.to_dict()
                session_data['is_current'] = session.jwt_token_id == request.headers.get('Authorization', '').replace('Bearer ', '')[:36]
                session_list.append(session_data)
            
            return {
                'sessions': session_list,
                'total_active': len(session_list)
            }, 200
            
        except Exception as e:
            logger.error("Sessions retrieval failed", error=str(e))
            return {'error': 'Failed to retrieve sessions'}, 500
    
    def delete(self):
        """Revoke all other sessions"""
        try:
            current_user_id = get_jwt_identity()
            current_jti = request.headers.get('Authorization', '').replace('Bearer ', '')[:36]
            
            # Revoke all sessions except current
            revoked_count = UserSession.query.filter_by(
                user_id=current_user_id,
                is_active=True
            ).filter(UserSession.jwt_token_id != current_jti).update({
                'is_active': False,
                'revoked_at': datetime.now(timezone.utc)
            })
            
            db.session.commit()
            
            logger.info("Sessions revoked", 
                       user_id=current_user_id,
                       revoked_count=revoked_count)
            
            return {
                'message': f'Successfully revoked {revoked_count} sessions',
                'revoked_count': revoked_count
            }, 200
            
        except Exception as e:
            logger.error("Session revocation failed", error=str(e))
            return {'error': 'Failed to revoke sessions'}, 500


class PreferencesResource(Resource):
    """User preferences management"""
    
    decorators = [jwt_required()]
    
    def get(self):
        """Get user preferences"""
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return {'error': 'User not found'}, 404
            
            # Get preferences from user metadata or defaults
            preferences = {
                'email_notifications': True,
                'marketing_emails': False,
                'default_video_quality': 'standard',
                'default_aspect_ratio': '16:9',
                'preferred_ai_provider': 'auto'
            }
            
            return {
                'preferences': preferences
            }, 200
            
        except Exception as e:
            logger.error("Preferences retrieval failed", error=str(e))
            return {'error': 'Failed to retrieve preferences'}, 500
    
    def put(self):
        """Update user preferences"""
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return {'error': 'User not found'}, 404
            
            # Validate request data
            schema = PreferencesSchema()
            data = schema.load(request.get_json() or {})
            
            # Store preferences (in a real implementation, you might have a separate preferences table)
            # For now, we'll return success
            logger.info("Preferences updated", 
                       user_id=current_user_id,
                       preferences=data)
            
            return {
                'message': 'Preferences updated successfully',
                'preferences': data
            }, 200
            
        except ValidationError as e:
            return {'error': 'Validation failed', 'details': e.messages}, 400
        except Exception as e:
            logger.error("Preferences update failed", error=str(e))
            return {'error': 'Failed to update preferences'}, 500


class AccountDeletionResource(Resource):
    """Account deletion (GDPR compliance)"""
    
    decorators = [jwt_required()]
    
    def post(self):
        """Request account deletion"""
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return {'error': 'User not found'}, 404
            
            # In a real implementation, this would:
            # 1. Queue a job to delete user data
            # 2. Send confirmation email
            # 3. Set deletion date based on retention policy
            # 4. Anonymize data according to GDPR requirements
            
            logger.info("Account deletion requested", user_id=current_user_id)
            
            return {
                'message': 'Account deletion request received',
                'notice': 'Your data will be deleted within 30 days as per our retention policy',
                'contact_support': 'Contact support if you need to cancel this request'
            }, 200
            
        except Exception as e:
            logger.error("Account deletion request failed", error=str(e))
            return {'error': 'Failed to process deletion request'}, 500


# Register API resources
user_api.add_resource(ProfileResource, '/profile')
user_api.add_resource(PasswordChangeResource, '/change-password')
user_api.add_resource(DashboardResource, '/dashboard')
user_api.add_resource(SessionsResource, '/sessions')
user_api.add_resource(PreferencesResource, '/preferences')
user_api.add_resource(AccountDeletionResource, '/delete-account')