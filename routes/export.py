"""
TalkingPhoto AI MVP - Export Workflow Routes
Platform-specific export instructions and workflow templates
"""

from flask import Blueprint, request, jsonify
from flask_restful import Api, Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, validate, ValidationError
from datetime import datetime, timezone
import structlog

from app import db
from models.user import User
from models.video import VideoGeneration
from models.usage import UsageLog, ActionType
from services.export_service import ExportService
from utils.security import get_client_info

# Create blueprint and API
export_bp = Blueprint('export', __name__)
export_api = Api(export_bp)
logger = structlog.get_logger()

# Validation Schemas
class ExportInstructionsSchema(Schema):
    """Export instructions request validation schema"""
    video_id = fields.Str(required=True, validate=validate.Length(equal=36))
    platform = fields.Str(required=True, validate=validate.OneOf([
        'instagram', 'youtube', 'linkedin', 'tiktok', 'twitter', 'facebook'
    ]))
    workflow_type = fields.Str(required=True, validate=validate.OneOf([
        'product_demo', 'avatar_presentation', 'lifestyle_content', 'testimonial'
    ]))
    additional_options = fields.Dict(required=False)


class WorkflowTemplateSchema(Schema):
    """Workflow template query parameters schema"""
    platform = fields.Str(required=False)
    workflow_type = fields.Str(required=False)
    category = fields.Str(required=False)


# Export Resources
class ExportInstructionsResource(Resource):
    """Generate platform-specific export instructions"""
    
    decorators = [jwt_required()]
    
    def post(self):
        """Generate detailed export instructions for completed video"""
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return {'error': 'User not found'}, 404
            
            # Validate request data
            schema = ExportInstructionsSchema()
            data = schema.load(request.get_json() or {})
            
            # Get client information
            client_info = get_client_info(request)
            
            # Verify video generation exists and belongs to user
            video = VideoGeneration.query.filter_by(
                id=data['video_id'],
                user_id=current_user_id
            ).first()
            
            if not video:
                return {'error': 'Video generation not found'}, 404
            
            if not video.is_completed():
                return {
                    'error': 'Video not ready',
                    'message': 'Video generation must be completed first',
                    'status': video.status.value
                }, 409
            
            # Generate export instructions
            export_service = ExportService()
            instructions = export_service.generate_instructions(
                video_generation=video,
                platform=data['platform'],
                workflow_type=data['workflow_type'],
                additional_options=data.get('additional_options', {})
            )
            
            if not instructions['success']:
                return {
                    'error': 'Instructions generation failed',
                    'message': instructions['error']
                }, 500
            
            # Log export instruction usage
            UsageLog.log_action(
                user_id=current_user_id,
                action_type=ActionType.EXPORT_INSTRUCTION,
                resource_id=video.id,
                resource_type='video_generation',
                success=True,
                metadata={
                    'platform': data['platform'],
                    'workflow_type': data['workflow_type']
                },
                ip_address=client_info['ip_address'],
                user_agent=client_info['user_agent']
            )
            
            logger.info("Export instructions generated", 
                       user_id=current_user_id,
                       video_id=video.id,
                       platform=data['platform'],
                       workflow_type=data['workflow_type'])
            
            return {
                'message': 'Export instructions generated successfully',
                'instructions': instructions['data'],
                'metadata': {
                    'platform': data['platform'],
                    'workflow_type': data['workflow_type'],
                    'generated_at': datetime.now(timezone.utc).isoformat(),
                    'video_info': {
                        'id': video.id,
                        'duration': video.duration_seconds,
                        'aspect_ratio': video.aspect_ratio.value,
                        'quality': video.video_quality.value
                    }
                }
            }, 200
            
        except ValidationError as e:
            return {'error': 'Validation failed', 'details': e.messages}, 400
        except Exception as e:
            logger.error("Export instructions generation failed", error=str(e))
            return {'error': 'Instructions generation failed', 'message': 'Internal server error'}, 500


class WorkflowTemplatesResource(Resource):
    """Get available workflow templates"""
    
    decorators = [jwt_required()]
    
    def get(self):
        """Get list of available workflow templates"""
        try:
            # Validate query parameters
            schema = WorkflowTemplateSchema()
            params = schema.load(request.args.to_dict())
            
            export_service = ExportService()
            templates = export_service.get_workflow_templates(
                platform=params.get('platform'),
                workflow_type=params.get('workflow_type'),
                category=params.get('category')
            )
            
            return {
                'templates': templates,
                'total_count': len(templates)
            }, 200
            
        except ValidationError as e:
            return {'error': 'Validation failed', 'details': e.messages}, 400
        except Exception as e:
            logger.error("Workflow templates retrieval failed", error=str(e))
            return {'error': 'Failed to retrieve templates'}, 500


class PlatformRequirementsResource(Resource):
    """Get platform-specific requirements"""
    
    decorators = [jwt_required()]
    
    def get(self, platform):
        """Get technical requirements for a specific platform"""
        try:
            valid_platforms = [
                'instagram', 'youtube', 'linkedin', 'tiktok', 'twitter', 'facebook'
            ]
            
            if platform not in valid_platforms:
                return {
                    'error': 'Invalid platform',
                    'valid_platforms': valid_platforms
                }, 400
            
            export_service = ExportService()
            requirements = export_service.get_platform_requirements(platform)
            
            return {
                'platform': platform,
                'requirements': requirements,
                'last_updated': requirements.get('last_updated')
            }, 200
            
        except Exception as e:
            logger.error("Platform requirements retrieval failed", 
                        platform=platform, error=str(e))
            return {'error': 'Failed to retrieve platform requirements'}, 500


class CostCalculatorResource(Resource):
    """Calculate workflow costs"""
    
    decorators = [jwt_required()]
    
    def post(self):
        """Calculate estimated costs for workflow implementation"""
        try:
            data = request.get_json() or {}
            
            required_fields = ['platform', 'workflow_type', 'video_specs']
            for field in required_fields:
                if field not in data:
                    return {'error': f'Missing required field: {field}'}, 400
            
            export_service = ExportService()
            cost_breakdown = export_service.calculate_workflow_costs(
                platform=data['platform'],
                workflow_type=data['workflow_type'],
                video_specs=data['video_specs'],
                additional_services=data.get('additional_services', [])
            )
            
            return {
                'cost_breakdown': cost_breakdown,
                'total_estimated_cost': cost_breakdown['total'],
                'currency': 'USD',
                'calculation_date': datetime.now(timezone.utc).isoformat()
            }, 200
            
        except Exception as e:
            logger.error("Cost calculation failed", error=str(e))
            return {'error': 'Cost calculation failed'}, 500


class WorkflowOptimizationResource(Resource):
    """Get workflow optimization suggestions"""
    
    decorators = [jwt_required()]
    
    def post(self):
        """Get optimization suggestions for workflow"""
        try:
            current_user_id = get_jwt_identity()
            
            data = request.get_json() or {}
            
            if 'video_id' not in data:
                return {'error': 'Missing required field: video_id'}, 400
            
            # Verify video generation
            video = VideoGeneration.query.filter_by(
                id=data['video_id'],
                user_id=current_user_id
            ).first()
            
            if not video:
                return {'error': 'Video generation not found'}, 404
            
            export_service = ExportService()
            suggestions = export_service.get_optimization_suggestions(
                video_generation=video,
                target_platforms=data.get('target_platforms', []),
                current_performance=data.get('current_performance', {})
            )
            
            return {
                'video_id': video.id,
                'optimization_suggestions': suggestions,
                'confidence_score': suggestions.get('confidence_score', 0.8),
                'generated_at': datetime.now(timezone.utc).isoformat()
            }, 200
            
        except Exception as e:
            logger.error("Workflow optimization failed", error=str(e))
            return {'error': 'Optimization suggestions failed'}, 500


class ExportHistoryResource(Resource):
    """Get user's export instruction history"""
    
    decorators = [jwt_required()]
    
    def get(self):
        """Get paginated history of export instructions"""
        try:
            current_user_id = get_jwt_identity()
            
            # Get pagination parameters
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 20, type=int), 100)
            
            # Query export instruction logs
            export_logs = UsageLog.query.filter_by(
                user_id=current_user_id,
                action_type=ActionType.EXPORT_INSTRUCTION
            ).order_by(UsageLog.created_at.desc()).paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            history = []
            for log in export_logs.items:
                # Get video generation details
                video = VideoGeneration.query.get(log.resource_id)
                
                history_item = {
                    'id': log.id,
                    'video_id': log.resource_id,
                    'platform': log.metadata.get('platform') if log.metadata else None,
                    'workflow_type': log.metadata.get('workflow_type') if log.metadata else None,
                    'created_at': log.created_at.isoformat(),
                    'success': log.success
                }
                
                if video:
                    history_item['video_info'] = {
                        'script_text': video.script_text[:50] + '...' if len(video.script_text) > 50 else video.script_text,
                        'quality': video.video_quality.value,
                        'aspect_ratio': video.aspect_ratio.value
                    }
                
                history.append(history_item)
            
            return {
                'history': history,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': export_logs.total,
                    'pages': export_logs.pages,
                    'has_prev': export_logs.has_prev,
                    'has_next': export_logs.has_next
                }
            }, 200
            
        except Exception as e:
            logger.error("Export history retrieval failed", error=str(e))
            return {'error': 'Failed to retrieve export history'}, 500


# Register API resources
export_api.add_resource(ExportInstructionsResource, '/instructions')
export_api.add_resource(WorkflowTemplatesResource, '/templates')
export_api.add_resource(PlatformRequirementsResource, '/requirements/<string:platform>')
export_api.add_resource(CostCalculatorResource, '/cost-calculator')
export_api.add_resource(WorkflowOptimizationResource, '/optimize')
export_api.add_resource(ExportHistoryResource, '/history')