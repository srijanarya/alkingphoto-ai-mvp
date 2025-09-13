"""
TalkingPhoto AI MVP - Authentication Routes
JWT-based authentication with rate limiting and security measures
"""

from flask import Blueprint, request, jsonify, current_app
from flask_restful import Api, Resource
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required, 
    get_jwt_identity, get_jwt, verify_jwt_in_request
)
from flask_limiter import Limiter
from marshmallow import Schema, fields, validate, ValidationError
from werkzeug.security import check_password_hash
from datetime import datetime, timezone, timedelta
import structlog
import uuid
import secrets
import string

from app import db, limiter
from models.user import User, UserSession, UserStatus
from models.usage import UsageLog, ActionType
from utils.validators import validate_email, validate_password
from utils.email_service import EmailService
from utils.security import get_client_info, is_suspicious_activity

# Create blueprint and API
auth_bp = Blueprint('auth', __name__)
auth_api = Api(auth_bp)
logger = structlog.get_logger()


# Validation Schemas
class RegistrationSchema(Schema):
    """User registration validation schema"""
    email = fields.Email(required=True, validate=validate.Length(max=255))
    password = fields.Str(required=True, validate=validate_password)
    first_name = fields.Str(required=False, validate=validate.Length(max=50))
    last_name = fields.Str(required=False, validate=validate.Length(max=50))
    gdpr_consent = fields.Bool(required=True)


class LoginSchema(Schema):
    """User login validation schema"""
    email = fields.Email(required=True)
    password = fields.Str(required=True)
    remember_me = fields.Bool(required=False, default=False)


class PasswordResetRequestSchema(Schema):
    """Password reset request validation schema"""
    email = fields.Email(required=True)


class PasswordResetSchema(Schema):
    """Password reset validation schema"""
    token = fields.Str(required=True)
    new_password = fields.Str(required=True, validate=validate_password)


class EmailVerificationSchema(Schema):
    """Email verification validation schema"""
    token = fields.Str(required=True)


# Authentication Resources
class RegisterResource(Resource):
    """User registration endpoint"""
    
    decorators = [limiter.limit("5 per minute")]
    
    def post(self):
        """Register a new user"""
        try:
            # Validate request data
            schema = RegistrationSchema()
            data = schema.load(request.get_json() or {})
            
            # Check GDPR consent
            if not data.get('gdpr_consent'):
                return {
                    'error': 'GDPR consent is required',
                    'message': 'You must consent to data processing to create an account'
                }, 400
            
            # Check if user already exists
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user:
                return {
                    'error': 'User already exists',
                    'message': 'An account with this email already exists'
                }, 409
            
            # Get client information for security
            client_info = get_client_info(request)
            
            # Create new user
            user = User(
                email=data['email'],
                password=data['password'],
                first_name=data.get('first_name'),
                last_name=data.get('last_name')
            )
            user.set_gdpr_consent()
            
            # Generate email verification token
            user.email_verification_token = secrets.token_urlsafe(32)
            
            db.session.add(user)
            db.session.commit()
            
            # Send verification email
            try:
                email_service = EmailService()
                email_service.send_verification_email(user.email, user.email_verification_token)
            except Exception as e:
                logger.error("Failed to send verification email", user_id=user.id, error=str(e))
            
            # Log registration activity
            UsageLog.log_action(
                user_id=user.id,
                action_type=ActionType.SUBSCRIPTION_UPGRADE,  # First registration
                success=True,
                ip_address=client_info['ip_address'],
                user_agent=client_info['user_agent']
            )
            
            logger.info("User registered successfully", user_id=user.id, email=user.email)
            
            return {
                'message': 'Registration successful',
                'user': user.to_dict(),
                'email_verification_sent': True
            }, 201
            
        except ValidationError as e:
            return {'error': 'Validation failed', 'details': e.messages}, 400
        except Exception as e:
            logger.error("Registration failed", error=str(e))
            return {'error': 'Registration failed', 'message': 'Internal server error'}, 500


class LoginResource(Resource):
    """User login endpoint"""
    
    decorators = [limiter.limit("10 per minute")]
    
    def post(self):
        """Authenticate user and return JWT tokens"""
        try:
            # Validate request data
            schema = LoginSchema()
            data = schema.load(request.get_json() or {})
            
            # Get client information
            client_info = get_client_info(request)
            
            # Check for suspicious activity
            if is_suspicious_activity(data['email'], client_info['ip_address']):
                logger.warning("Suspicious login activity detected", 
                             email=data['email'], 
                             ip=client_info['ip_address'])
                return {
                    'error': 'Security alert',
                    'message': 'Suspicious activity detected. Please try again later.'
                }, 429
            
            # Find user
            user = User.query.filter_by(email=data['email']).first()
            if not user or not user.check_password(data['password']):
                # Log failed login attempt
                if user:
                    UsageLog.log_action(
                        user_id=user.id,
                        action_type=ActionType.SUBSCRIPTION_UPGRADE,  # Login attempt
                        success=False,
                        error_message="Invalid credentials",
                        ip_address=client_info['ip_address'],
                        user_agent=client_info['user_agent']
                    )
                
                return {
                    'error': 'Invalid credentials',
                    'message': 'Email or password is incorrect'
                }, 401
            
            # Check user status
            if user.status != UserStatus.ACTIVE:
                return {
                    'error': 'Account inactive',
                    'message': 'Your account is not active. Please contact support.'
                }, 403
            
            # Generate JWT tokens
            tokens = user.generate_tokens()
            
            # Calculate token expiration
            access_expires = datetime.now(timezone.utc) + current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
            refresh_expires = datetime.now(timezone.utc) + current_app.config['JWT_REFRESH_TOKEN_EXPIRES']
            
            # Create session record
            session = UserSession(
                user_id=user.id,
                jwt_token_id=str(uuid.uuid4()),
                expires_at=access_expires,
                ip_address=client_info['ip_address'],
                user_agent=client_info['user_agent'],
                device_type=client_info.get('device_type')
            )
            
            # Update user last login
            user.last_login = datetime.now(timezone.utc)
            
            db.session.add(session)
            db.session.commit()
            
            # Log successful login
            UsageLog.log_action(
                user_id=user.id,
                action_type=ActionType.SUBSCRIPTION_UPGRADE,  # Successful login
                success=True,
                ip_address=client_info['ip_address'],
                user_agent=client_info['user_agent']
            )
            
            logger.info("User login successful", user_id=user.id, email=user.email)
            
            response = {
                'message': 'Login successful',
                'tokens': tokens,
                'user': user.to_dict(),
                'session': session.to_dict()
            }
            
            # Add warning if email not verified
            if not user.email_verified:
                response['warning'] = 'Please verify your email address'
                response['email_verification_required'] = True
            
            return response, 200
            
        except ValidationError as e:
            return {'error': 'Validation failed', 'details': e.messages}, 400
        except Exception as e:
            logger.error("Login failed", error=str(e))
            return {'error': 'Login failed', 'message': 'Internal server error'}, 500


class RefreshTokenResource(Resource):
    """Token refresh endpoint"""
    
    decorators = [jwt_required(refresh=True)]
    
    def post(self):
        """Refresh access token using refresh token"""
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user or user.status != UserStatus.ACTIVE:
                return {'error': 'User not found or inactive'}, 404
            
            # Generate new access token
            tokens = user.generate_tokens()
            
            logger.info("Token refreshed", user_id=user.id)
            
            return {
                'message': 'Token refreshed successfully',
                'tokens': tokens
            }, 200
            
        except Exception as e:
            logger.error("Token refresh failed", error=str(e))
            return {'error': 'Token refresh failed'}, 500


class LogoutResource(Resource):
    """User logout endpoint"""
    
    decorators = [jwt_required()]
    
    def post(self):
        """Logout user and revoke session"""
        try:
            current_user_id = get_jwt_identity()
            jti = get_jwt()['jti']  # JWT ID
            
            # Find and revoke session
            session = UserSession.query.filter_by(
                user_id=current_user_id,
                jwt_token_id=jti
            ).first()
            
            if session:
                session.revoke()
                db.session.commit()
            
            logger.info("User logout successful", user_id=current_user_id)
            
            return {'message': 'Logout successful'}, 200
            
        except Exception as e:
            logger.error("Logout failed", error=str(e))
            return {'error': 'Logout failed'}, 500


class VerifyEmailResource(Resource):
    """Email verification endpoint"""
    
    def post(self):
        """Verify user email with token"""
        try:
            schema = EmailVerificationSchema()
            data = schema.load(request.get_json() or {})
            
            # Find user with verification token
            user = User.query.filter_by(
                email_verification_token=data['token']
            ).first()
            
            if not user:
                return {
                    'error': 'Invalid token',
                    'message': 'Verification token is invalid or expired'
                }, 400
            
            # Mark email as verified
            user.mark_email_verified()
            db.session.commit()
            
            logger.info("Email verified successfully", user_id=user.id)
            
            return {
                'message': 'Email verified successfully',
                'user': user.to_dict()
            }, 200
            
        except ValidationError as e:
            return {'error': 'Validation failed', 'details': e.messages}, 400
        except Exception as e:
            logger.error("Email verification failed", error=str(e))
            return {'error': 'Email verification failed'}, 500


class RequestPasswordResetResource(Resource):
    """Password reset request endpoint"""
    
    decorators = [limiter.limit("3 per hour")]
    
    def post(self):
        """Request password reset email"""
        try:
            schema = PasswordResetRequestSchema()
            data = schema.load(request.get_json() or {})
            
            user = User.query.filter_by(email=data['email']).first()
            
            # Always return success to prevent email enumeration
            response = {
                'message': 'If an account exists with this email, a password reset link has been sent'
            }
            
            if user and user.status == UserStatus.ACTIVE:
                # Generate reset token
                user.password_reset_token = secrets.token_urlsafe(32)
                user.password_reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
                
                db.session.commit()
                
                # Send reset email
                try:
                    email_service = EmailService()
                    email_service.send_password_reset_email(user.email, user.password_reset_token)
                except Exception as e:
                    logger.error("Failed to send password reset email", 
                               user_id=user.id, error=str(e))
                
                logger.info("Password reset requested", user_id=user.id)
            
            return response, 200
            
        except ValidationError as e:
            return {'error': 'Validation failed', 'details': e.messages}, 400
        except Exception as e:
            logger.error("Password reset request failed", error=str(e))
            return {'error': 'Password reset request failed'}, 500


class ResetPasswordResource(Resource):
    """Password reset endpoint"""
    
    def post(self):
        """Reset password with token"""
        try:
            schema = PasswordResetSchema()
            data = schema.load(request.get_json() or {})
            
            # Find user with reset token
            user = User.query.filter_by(
                password_reset_token=data['token']
            ).first()
            
            if (not user or 
                not user.password_reset_expires or 
                datetime.now(timezone.utc) > user.password_reset_expires):
                return {
                    'error': 'Invalid or expired token',
                    'message': 'Password reset token is invalid or expired'
                }, 400
            
            # Update password
            user.set_password(data['new_password'])
            user.password_reset_token = None
            user.password_reset_expires = None
            
            db.session.commit()
            
            logger.info("Password reset successful", user_id=user.id)
            
            return {'message': 'Password reset successful'}, 200
            
        except ValidationError as e:
            return {'error': 'Validation failed', 'details': e.messages}, 400
        except ValueError as e:
            return {'error': 'Invalid password', 'message': str(e)}, 400
        except Exception as e:
            logger.error("Password reset failed", error=str(e))
            return {'error': 'Password reset failed'}, 500


# Register API resources
auth_api.add_resource(RegisterResource, '/register')
auth_api.add_resource(LoginResource, '/login')
auth_api.add_resource(RefreshTokenResource, '/refresh')
auth_api.add_resource(LogoutResource, '/logout')
auth_api.add_resource(VerifyEmailResource, '/verify-email')
auth_api.add_resource(RequestPasswordResetResource, '/request-password-reset')
auth_api.add_resource(ResetPasswordResource, '/reset-password')