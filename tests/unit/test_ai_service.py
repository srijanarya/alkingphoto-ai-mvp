"""
TalkingPhoto AI MVP - AI Service Unit Tests
Comprehensive tests for AI service routing, provider selection, and video generation
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
import requests
from datetime import datetime, timezone

from services.ai_service import AIService, AIServiceRouter
from models.video import VideoGeneration, AIProvider, VideoStatus, VideoQuality, AspectRatio
from models.file import UploadedFile, FileType, FileStatus
from models.user import User, SubscriptionTier


class TestAIServiceRouter:
    """Test AI service routing and provider selection logic"""
    
    @pytest.fixture
    def router(self):
        with patch('services.ai_service.current_app') as mock_app:
            mock_app.config.get.return_value = 'test_api_key'
            return AIServiceRouter()
    
    def test_service_configuration(self, router):
        """Test that services are properly configured"""
        assert 'image_enhancement' in router.services
        assert 'video_generation' in router.services
        
        # Check image enhancement services
        img_services = router.services['image_enhancement']
        assert len(img_services) == 3
        service_names = [s['name'] for s in img_services]
        assert 'nano_banana' in service_names
        assert 'openai_dall_e' in service_names
        assert 'stability_ai' in service_names
        
        # Check video generation services
        video_services = router.services['video_generation']
        assert len(video_services) == 3
        video_names = [s['name'] for s in video_services]
        assert 'veo3' in video_names
        assert 'runway' in video_names
        assert 'nano_banana_video' in video_names
    
    def test_select_optimal_service_economy_preference(self, router):
        """Test service selection with economy preference"""
        with patch.object(router, '_is_service_available', return_value=True):
            result = router.select_optimal_service('image_enhancement', 'economy')
            
            assert result['success'] is True
            assert result['service']['name'] == 'nano_banana'  # Cheapest option
            assert result['service']['cost'] == 0.039
    
    def test_select_optimal_service_premium_preference(self, router):
        """Test service selection with premium preference"""
        with patch.object(router, '_is_service_available', return_value=True):
            result = router.select_optimal_service('image_enhancement', 'premium')
            
            assert result['success'] is True
            assert result['service']['name'] == 'openai_dall_e'  # Highest quality
            assert result['service']['quality'] == 9.2
    
    def test_select_optimal_service_balanced_preference(self, router):
        """Test service selection with balanced preference"""
        with patch.object(router, '_is_service_available', return_value=True):
            result = router.select_optimal_service('image_enhancement', 'balanced')
            
            assert result['success'] is True
            # Should select based on cost/quality ratio
            service = result['service']
            assert service['name'] in ['nano_banana', 'stability_ai']
    
    def test_select_optimal_service_no_services_available(self, router):
        """Test service selection when no services are available"""
        with patch.object(router, '_is_service_available', return_value=False):
            result = router.select_optimal_service('image_enhancement', 'balanced')
            
            assert 'error' in result
            assert 'No services currently available' in result['error']
    
    def test_select_optimal_service_invalid_type(self, router):
        """Test service selection with invalid service type"""
        result = router.select_optimal_service('invalid_service_type', 'balanced')
        
        assert 'error' in result
        assert 'No services available for invalid_service_type' in result['error']
    
    def test_is_service_available_with_api_key(self, router):
        """Test service availability check with API key"""
        router.api_keys['test_service'] = 'test_key'
        assert router._is_service_available('test_service') is True
    
    def test_is_service_available_without_api_key(self, router):
        """Test service availability check without API key"""
        router.api_keys['test_service'] = None
        assert router._is_service_available('test_service') is False


class TestAIService:
    """Test main AI service functionality"""
    
    @pytest.fixture
    def ai_service(self):
        with patch('services.ai_service.current_app') as mock_app:
            mock_app.config.get.return_value = 'test_api_key'
            return AIService()
    
    @pytest.fixture
    def mock_file(self, db_session):
        """Create a mock uploaded file"""
        file = UploadedFile(
            id='test_file_123',
            user_id='test_user',
            original_filename='test_image.jpg',
            filename='test_image_unique.jpg',
            file_type=FileType.IMAGE,
            mime_type='image/jpeg',
            file_size=1024000,
            file_hash='abc123def456',
            width=1920,
            height=1080,
            storage_path='uploads/test_image_unique.jpg'
        )
        db_session.add(file)
        db_session.commit()
        return file
    
    @pytest.fixture
    def mock_video_generation(self, db_session, mock_file):
        """Create a mock video generation"""
        video_gen = VideoGeneration(
            id='test_video_123',
            user_id='test_user',
            source_file_id=mock_file.id,
            script_text='Hello, this is a test video script.',
            ai_provider=AIProvider.VEO3,
            video_quality=VideoQuality.STANDARD,
            aspect_ratio=AspectRatio.LANDSCAPE,
            duration_seconds=30
        )
        db_session.add(video_gen)
        db_session.commit()
        return video_gen

    # Image Enhancement Tests
    def test_enhance_image_success_nano_banana(self, ai_service, mock_file):
        """Test successful image enhancement with Nano Banana"""
        with patch.object(ai_service.router, 'select_optimal_service') as mock_select:
            mock_select.return_value = {
                'success': True,
                'service': {'name': 'nano_banana', 'cost': 0.039}
            }
            
            with patch.object(ai_service.file_service, 'get_file_content') as mock_get_file:
                mock_get_file.return_value = b'mock_image_data'
                
                with patch.object(ai_service, '_enhance_with_nano_banana') as mock_enhance:
                    mock_enhance.return_value = {
                        'success': True,
                        'filename': 'enhanced_test_image.jpg',
                        'cost': 0.039
                    }
                    
                    result = ai_service.enhance_image('test_file_123')
                    
                    assert result['success'] is True
                    assert result['filename'] == 'enhanced_test_image.jpg'
                    assert result['cost'] == 0.039
                    mock_enhance.assert_called_once()
    
    def test_enhance_image_file_not_found(self, ai_service):
        """Test image enhancement with non-existent file"""
        result = ai_service.enhance_image('non_existent_file')
        
        assert result['success'] is False
        assert 'Source file not found' in result['error']
    
    def test_enhance_image_no_services_available(self, ai_service, mock_file):
        """Test image enhancement when no services are available"""
        with patch.object(ai_service.router, 'select_optimal_service') as mock_select:
            mock_select.return_value = {'error': 'No services available'}
            
            result = ai_service.enhance_image('test_file_123')
            
            assert result['success'] is False
            assert 'No services available' in result['error']
    
    @patch('requests.post')
    def test_enhance_with_nano_banana_success(self, mock_post, ai_service, mock_file):
        """Test Nano Banana image enhancement success"""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'candidates': [{'content': {'parts': [{'text': 'Enhanced image description'}]}}]
        }
        mock_post.return_value = mock_response
        
        with patch.object(ai_service.file_service, 'store_file') as mock_store:
            mock_store.return_value = {
                'success': True,
                'path': 'enhanced/test_image.jpg',
                'url': 'https://example.com/enhanced.jpg'
            }
            
            result = ai_service._enhance_with_nano_banana(
                b'mock_image_data', 
                mock_file, 
                {'prompt': 'Enhance this image'}
            )
            
            assert result['success'] is True
            assert result['cost'] == 0.039
            assert 'storage_path' in result
            mock_post.assert_called_once()
    
    @patch('requests.post')
    def test_enhance_with_nano_banana_api_error(self, mock_post, ai_service, mock_file):
        """Test Nano Banana API error handling"""
        # Mock API error
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = 'Bad Request'
        mock_post.return_value = mock_response
        
        result = ai_service._enhance_with_nano_banana(
            b'mock_image_data', 
            mock_file, 
            {}
        )
        
        assert result['success'] is False
        assert 'API error: 400' in result['error']

    # Video Generation Tests
    def test_generate_video_veo3_success(self, ai_service, mock_video_generation):
        """Test successful video generation with VEO3"""
        with patch.object(ai_service, '_generate_with_veo3') as mock_generate:
            mock_generate.return_value = {
                'success': True,
                'output_file_path': 'videos/test_video.mp4',
                'duration': 30,
                'cost': 4.5
            }
            
            result = ai_service.generate_video('test_video_123')
            
            assert result['success'] is True
            assert result['duration'] == 30
            assert result['cost'] == 4.5
            mock_generate.assert_called_once()
    
    def test_generate_video_runway_success(self, ai_service, mock_video_generation, db_session):
        """Test successful video generation with Runway"""
        # Change AI provider to Runway
        mock_video_generation.ai_provider = AIProvider.RUNWAY
        db_session.commit()
        
        with patch.object(ai_service, '_generate_with_runway') as mock_generate:
            mock_generate.return_value = {
                'success': True,
                'output_file_path': 'videos/test_video.mp4',
                'duration': 30,
                'cost': 6.0
            }
            
            result = ai_service.generate_video('test_video_123')
            
            assert result['success'] is True
            assert result['cost'] == 6.0
            mock_generate.assert_called_once()
    
    def test_generate_video_mock_provider(self, ai_service, mock_video_generation, db_session):
        """Test video generation with mock provider"""
        # Change AI provider to Mock
        mock_video_generation.ai_provider = AIProvider.MOCK
        db_session.commit()
        
        with patch.object(ai_service, '_generate_mock_video') as mock_generate:
            mock_generate.return_value = {
                'success': True,
                'output_file_path': 'videos/mock_test_video.mp4',
                'duration': 30,
                'cost': 0.0
            }
            
            result = ai_service.generate_video('test_video_123')
            
            assert result['success'] is True
            assert result['cost'] == 0.0  # Mock has no cost
            mock_generate.assert_called_once()
    
    def test_generate_video_not_found(self, ai_service):
        """Test video generation with non-existent video generation"""
        result = ai_service.generate_video('non_existent_video')
        
        assert result['success'] is False
        assert 'Video generation not found' in result['error']
    
    def test_generate_video_unsupported_provider(self, ai_service, mock_video_generation, db_session):
        """Test video generation with unsupported AI provider"""
        # Set an invalid provider (this would normally be prevented by enum)
        with patch.object(mock_video_generation, 'ai_provider', 'INVALID_PROVIDER'):
            result = ai_service.generate_video('test_video_123')
            
            assert result['success'] is False
            assert 'not supported' in result['error']
    
    def test_generate_with_veo3_mock_implementation(self, ai_service, mock_video_generation):
        """Test VEO3 mock implementation"""
        with patch.object(ai_service.file_service, 'store_file') as mock_store:
            mock_store.return_value = {
                'success': True,
                'path': 'videos/test_video.mp4',
                'url': 'https://example.com/test_video.mp4'
            }
            
            with patch.object(ai_service, '_create_mock_video_content') as mock_content:
                mock_content.return_value = b'mock_video_data'
                
                result = ai_service._generate_with_veo3(
                    mock_video_generation, 
                    mock_video_generation.source_file
                )
                
                assert result['success'] is True
                assert result['cost'] == 4.5  # 30 seconds * 0.15
                assert result['quality_metrics']['lip_sync_accuracy'] == 85.5
    
    def test_generate_with_runway_mock_implementation(self, ai_service, mock_video_generation):
        """Test Runway mock implementation"""
        with patch.object(ai_service.file_service, 'store_file') as mock_store:
            mock_store.return_value = {
                'success': True,
                'path': 'videos/test_video.mp4',
                'url': 'https://example.com/test_video.mp4'
            }
            
            with patch.object(ai_service, '_create_mock_video_content') as mock_content:
                mock_content.return_value = b'mock_video_data'
                
                result = ai_service._generate_with_runway(
                    mock_video_generation, 
                    mock_video_generation.source_file
                )
                
                assert result['success'] is True
                assert result['cost'] == 6.0  # 30 seconds * 0.20
                assert result['quality_metrics']['lip_sync_accuracy'] == 92.3
    
    def test_generate_with_nano_banana_video(self, ai_service, mock_video_generation):
        """Test Nano Banana video generation"""
        with patch.object(ai_service.file_service, 'store_file') as mock_store:
            mock_store.return_value = {
                'success': True,
                'path': 'videos/test_video.mp4',
                'url': 'https://example.com/test_video.mp4'
            }
            
            with patch.object(ai_service, '_create_mock_video_content') as mock_content:
                mock_content.return_value = b'mock_video_data'
                
                result = ai_service._generate_with_nano_banana_video(
                    mock_video_generation, 
                    mock_video_generation.source_file
                )
                
                assert result['success'] is True
                assert result['cost'] == 2.4  # 30 seconds * 0.08
                assert result['quality_metrics']['lip_sync_accuracy'] == 78.2
                assert result['quality_metrics']['video_resolution'] == '1280x720'
    
    def test_create_mock_video_content(self, ai_service):
        """Test mock video content creation"""
        content = ai_service._create_mock_video_content()
        
        assert isinstance(content, bytes)
        assert len(content) > 0
        assert content.startswith(b'\x00\x00\x00\x20ftypmp41')  # MP4 header

    # Status Check Tests
    def test_get_generation_status_no_job_id(self, ai_service, mock_video_generation):
        """Test status check when no provider job ID exists"""
        mock_video_generation.provider_job_id = None
        
        result = ai_service.get_generation_status(mock_video_generation)
        
        assert result['status_changed'] is False
    
    def test_get_generation_status_veo3(self, ai_service, mock_video_generation):
        """Test status check for VEO3 provider"""
        mock_video_generation.provider_job_id = 'veo3_job_123'
        mock_video_generation.ai_provider = AIProvider.VEO3
        
        with patch.object(ai_service, '_get_veo3_status') as mock_status:
            mock_status.return_value = {'status_changed': True, 'status': 'completed'}
            
            result = ai_service.get_generation_status(mock_video_generation)
            
            assert result['status_changed'] is True
            assert result['status'] == 'completed'
            mock_status.assert_called_once()
    
    def test_get_generation_status_runway(self, ai_service, mock_video_generation, db_session):
        """Test status check for Runway provider"""
        mock_video_generation.provider_job_id = 'runway_job_456'
        mock_video_generation.ai_provider = AIProvider.RUNWAY
        db_session.commit()
        
        with patch.object(ai_service, '_get_runway_status') as mock_status:
            mock_status.return_value = {'status_changed': True, 'status': 'processing'}
            
            result = ai_service.get_generation_status(mock_video_generation)
            
            assert result['status_changed'] is True
            assert result['status'] == 'processing'
            mock_status.assert_called_once()
    
    def test_get_generation_status_error_handling(self, ai_service, mock_video_generation):
        """Test status check error handling"""
        mock_video_generation.provider_job_id = 'test_job'
        
        with patch.object(ai_service, '_get_veo3_status') as mock_status:
            mock_status.side_effect = Exception('API error')
            
            result = ai_service.get_generation_status(mock_video_generation)
            
            assert result['status_changed'] is False
            assert 'error' in result


@pytest.mark.integration
class TestAIServiceIntegration:
    """Integration tests for AI service with external dependencies"""
    
    @pytest.fixture
    def ai_service_integration(self):
        """AI service with real configuration (but mocked externals)"""
        with patch('services.ai_service.current_app') as mock_app:
            mock_app.config.get.side_effect = lambda key: {
                'NANO_BANANA_API_KEY': 'real_test_key',
                'VEO3_API_KEY': 'real_veo3_key',
                'RUNWAY_API_KEY': 'real_runway_key'
            }.get(key)
            return AIService()
    
    def test_end_to_end_image_enhancement_flow(self, ai_service_integration, mock_file):
        """Test complete image enhancement workflow"""
        # Mock file content retrieval
        with patch.object(ai_service_integration.file_service, 'get_file_content') as mock_get:
            mock_get.return_value = b'real_image_data'
            
            # Mock external API call
            with patch('requests.post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {'status': 'success'}
                mock_post.return_value = mock_response
                
                # Mock file storage
                with patch.object(ai_service_integration.file_service, 'store_file') as mock_store:
                    mock_store.return_value = {
                        'success': True,
                        'path': 'enhanced/image.jpg',
                        'url': 'https://example.com/enhanced.jpg'
                    }
                    
                    # Test the full flow
                    result = ai_service_integration.enhance_image(
                        'test_file_123',
                        {'quality_preference': 'economy', 'prompt': 'Enhance for video'}
                    )
                    
                    # Verify all steps were called
                    mock_get.assert_called_once()
                    mock_post.assert_called_once()
                    mock_store.assert_called_once()
                    
                    # Verify result
                    assert result['success'] is True
                    assert 'storage_path' in result
                    assert result['cost'] > 0
    
    def test_provider_failover_scenario(self, ai_service_integration):
        """Test AI provider failover when primary service fails"""
        with patch.object(ai_service_integration.router, '_is_service_available') as mock_available:
            # First service fails, second succeeds
            mock_available.side_effect = [False, True, True]
            
            result = ai_service_integration.router.select_optimal_service(
                'image_enhancement', 'balanced'
            )
            
            assert result['success'] is True
            # Should have tried multiple services
            assert mock_available.call_count >= 2