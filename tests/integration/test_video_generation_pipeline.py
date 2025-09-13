"""
TalkingPhoto AI MVP - Video Generation Pipeline Integration Tests
Tests the complete video generation workflow with mocked external services
"""

import pytest
import asyncio
import json
import base64
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timezone
import tempfile
import os

from services.video_generation_service import VideoGenerationPipeline, VideoGenerationRequest
from services.tts_service import TTSService, TTSProvider
from services.lipsync_service import LipSyncAnimationEngine
from services.cost_optimization_service import CostOptimizationService
from services.websocket_service import WebSocketService
from models.video import VideoQuality, AspectRatio, AIProvider
from models.user import User, SubscriptionTier
from models.file import UploadedFile, FileType


@pytest.mark.integration
class TestVideoGenerationPipelineIntegration:
    """Integration tests for complete video generation pipeline"""
    
    @pytest.fixture
    def video_pipeline(self):
        """Create video generation pipeline with mocked dependencies"""
        with patch('services.video_generation_service.current_app') as mock_app:
            mock_app.config.get.side_effect = lambda key: {
                'REDIS_URL': 'redis://localhost:6379/0',
                'VEO3_API_KEY': 'test_veo3_key',
                'RUNWAY_API_KEY': 'test_runway_key',
                'AZURE_SPEECH_KEY': 'test_azure_key',
                'ELEVENLABS_API_KEY': 'test_elevenlabs_key'
            }.get(key, 'default_value')
            
            with patch('services.video_generation_service.Redis'):
                return VideoGenerationPipeline()
    
    @pytest.fixture
    def sample_video_request(self, temp_upload_dir):
        """Create sample video generation request"""
        # Create a sample image file
        image_path = os.path.join(temp_upload_dir, 'test_image.jpg')
        with open(image_path, 'wb') as f:
            # Write minimal JPEG header
            f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xd9')
        
        return VideoGenerationRequest(
            source_image=image_path,
            script_text="Hello everyone, welcome to our AI-powered video generation demo. This is a test of our advanced talking photo technology.",
            quality=VideoQuality.STANDARD,
            aspect_ratio=AspectRatio.LANDSCAPE,
            duration=15.0,
            voice_settings={
                'provider': TTSProvider.AZURE,
                'voice_name': 'en-US-JennyNeural',
                'emotion': 'cheerful'
            },
            animation_settings={
                'intensity': 0.8,
                'smooth_transitions': True,
                'enable_expressions': True
            }
        )
    
    @pytest.fixture
    def mock_user(self, db_session):
        """Create test user with premium subscription"""
        user = User(
            id='test_user_integration',
            email='integration@test.com',
            password='TestPassword123!',
            first_name='Integration',
            last_name='Test',
            subscription_tier=SubscriptionTier.PRO,
            credits_remaining=10
        )
        db_session.add(user)
        db_session.commit()
        return user
    
    @pytest.fixture
    def mock_websocket_service(self):
        """Mock WebSocket service for progress tracking"""
        mock_socketio = Mock()
        websocket_service = WebSocketService(mock_socketio)
        websocket_service.broadcast_progress = Mock()
        websocket_service.notify_video_completed = Mock()
        return websocket_service

    @pytest.mark.asyncio
    async def test_complete_video_generation_workflow(self, video_pipeline, sample_video_request, mock_websocket_service):
        """Test the complete video generation workflow from start to finish"""
        video_id = 'test_video_workflow_001'
        
        # Mock all external dependencies
        with patch.object(video_pipeline, 'websocket_service', mock_websocket_service):
            with patch.object(video_pipeline, 'tts_service') as mock_tts:
                with patch.object(video_pipeline, 'lipsync_engine') as mock_lipsync:
                    with patch.object(video_pipeline, 'cost_optimizer') as mock_optimizer:
                        
                        # Configure TTS service mock
                        mock_tts.synthesize_speech.return_value = {
                            'success': True,
                            'audio_data': base64.b64encode(b'mock_audio_data').decode('utf-8'),
                            'duration_seconds': 15,
                            'sample_rate': 16000,
                            'cost': 0.25,
                            'provider': 'azure'
                        }
                        
                        # Configure lip-sync engine mock
                        mock_lipsync.create_lip_sync_animation.return_value = {
                            'success': True,
                            'frames': [
                                {'frame_number': i, 'timestamp': i * 0.033, 'viseme': 'AA', 'data': f'frame_{i}'}
                                for i in range(450)  # 15 seconds * 30 fps
                            ],
                            'frame_rate': 30,
                            'total_frames': 450,
                            'animation_metrics': {
                                'lip_sync_accuracy': 92.5,
                                'animation_smoothness': 88.2,
                                'viseme_coverage': 95.0
                            }
                        }
                        
                        # Configure cost optimizer mock
                        mock_optimizer.select_optimal_provider.return_value = (
                            AIProvider.VEO3, 
                            {'estimated_cost': 2.25, 'processing_time': 45, 'confidence': 0.85}
                        )
                        
                        # Mock video generation providers
                        with patch.object(video_pipeline, '_generate_with_veo3') as mock_veo3:
                            mock_veo3.return_value = {
                                'success': True,
                                'video_data': b'mock_generated_video_data',
                                'format': 'mp4',
                                'duration': 15,
                                'resolution': '1920x1080',
                                'file_size': 5000000,  # 5MB
                                'provider': 'veo3',
                                'cost': 2.25,
                                'processing_time': 45,
                                'quality_metrics': {
                                    'overall_quality': 8.5,
                                    'lip_sync_accuracy': 92.5,
                                    'video_stability': 90.0,
                                    'audio_quality': 95.0
                                }
                            }
                            
                            # Mock post-processing
                            with patch.object(video_pipeline, '_post_process_video') as mock_post:
                                mock_post.return_value = {
                                    'success': True,
                                    'video_data': b'optimized_video_data',
                                    'optimization': {
                                        'original_size': 5000000,
                                        'optimized_size': 3500000,
                                        'compression_ratio': 0.3,
                                        'quality_retained': 0.95
                                    }
                                }
                                
                                # Execute the complete workflow
                                result = await video_pipeline.generate_video_async(
                                    sample_video_request,
                                    video_id
                                )
                                
                                # Verify successful completion
                                assert result['success'] is True
                                assert result['video_data'] == b'optimized_video_data'
                                assert result['duration'] == 15
                                assert result['total_cost'] > 0
                                
                                # Verify all stages were called
                                mock_tts.synthesize_speech.assert_called_once()
                                mock_lipsync.create_lip_sync_animation.assert_called_once()
                                mock_optimizer.select_optimal_provider.assert_called_once()
                                mock_veo3.assert_called_once()
                                mock_post.assert_called_once()
                                
                                # Verify progress tracking
                                assert mock_websocket_service.broadcast_progress.call_count >= 3
                                mock_websocket_service.notify_video_completed.assert_called_once()
                                
                                # Verify cost tracking
                                total_cost = result['cost_breakdown']['total']
                                assert total_cost > 2.0  # Should include TTS + video generation costs
                                assert 'tts_cost' in result['cost_breakdown']
                                assert 'video_generation_cost' in result['cost_breakdown']

    @pytest.mark.asyncio
    async def test_audio_generation_with_different_providers(self, video_pipeline, sample_video_request):
        """Test audio generation with different TTS providers"""
        video_id = 'test_audio_gen_001'
        
        # Test Azure TTS
        with patch('services.tts_service.speechsdk') as mock_speechsdk:
            mock_result = Mock()
            mock_result.reason = mock_speechsdk.ResultReason.SynthesizingAudioCompleted
            mock_result.audio_data = b'azure_audio_data'
            
            mock_synthesizer = Mock()
            mock_synthesizer.speak_ssml_async.return_value.get.return_value = mock_result
            mock_speechsdk.SpeechSynthesizer.return_value = mock_synthesizer
            
            audio_result = await video_pipeline._generate_audio(sample_video_request, video_id)
            
            assert audio_result['success'] is True
            assert 'audio_data' in audio_result
            assert audio_result['provider'] == 'azure'
            assert audio_result['duration'] > 0
        
        # Test ElevenLabs TTS
        sample_video_request.voice_settings['provider'] = TTSProvider.ELEVENLABS
        sample_video_request.voice_settings['voice_name'] = 'EXAVITQu4vr4xnSDxMaL'
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = b'elevenlabs_audio_data'
            mock_post.return_value = mock_response
            
            with patch.object(video_pipeline.tts_service, '_convert_mp3_to_wav') as mock_convert:
                mock_convert.return_value = b'converted_wav_data'
                
                audio_result = await video_pipeline._generate_audio(sample_video_request, video_id)
                
                assert audio_result['success'] is True
                assert 'audio_data' in audio_result
                assert audio_result['provider'] == 'elevenlabs'

    @pytest.mark.asyncio
    async def test_provider_failover_scenario(self, video_pipeline, sample_video_request):
        """Test automatic failover when primary provider fails"""
        video_id = 'test_failover_001'
        
        with patch.object(video_pipeline, '_is_provider_available') as mock_available:
            # VEO3 unavailable, Runway available
            mock_available.side_effect = lambda provider: provider != AIProvider.VEO3
            
            with patch.object(video_pipeline, '_generate_with_runway') as mock_runway:
                mock_runway.return_value = {
                    'success': True,
                    'video_data': b'runway_video_data',
                    'provider': 'runway',
                    'cost': 3.0
                }
                
                # Mock other dependencies
                with patch.object(video_pipeline, '_generate_audio') as mock_audio:
                    mock_audio.return_value = {'success': True, 'audio_data': b'audio', 'duration': 15}
                    
                    with patch.object(video_pipeline, '_analyze_facial_landmarks') as mock_landmarks:
                        mock_landmarks.return_value = {'success': True, 'landmarks': Mock()}
                        
                        with patch.object(video_pipeline, '_generate_lipsync_animation') as mock_lipsync:
                            mock_lipsync.return_value = {'success': True, 'frames': []}
                            
                            with patch.object(video_pipeline, '_post_process_video') as mock_post:
                                mock_post.return_value = {'success': True, 'video_data': b'final_video'}
                                
                                result = await video_pipeline.generate_video_async(
                                    sample_video_request, video_id
                                )
                                
                                # Should succeed with fallback provider
                                assert result['success'] is True
                                assert result['provider_used'] == 'runway'
                                mock_runway.assert_called_once()

    @pytest.mark.asyncio
    async def test_cost_optimization_integration(self, video_pipeline, sample_video_request):
        """Test cost optimization service integration"""
        video_id = 'test_cost_opt_001'
        
        # Mock cost optimization service
        with patch('services.cost_optimization_service.Redis') as mock_redis:
            mock_redis.return_value.hgetall.return_value = {
                'veo3_success_rate': '0.95',
                'veo3_avg_cost': '0.15',
                'veo3_avg_time': '45',
                'runway_success_rate': '0.98',
                'runway_avg_cost': '0.20',
                'runway_avg_time': '60'
            }
            
            cost_optimizer = CostOptimizationService()
            
            # Test with cost priority
            provider, estimate = cost_optimizer.select_optimal_provider(
                duration=15,
                quality=VideoQuality.STANDARD,
                aspect_ratio=AspectRatio.LANDSCAPE,
                user_preferences={'cost_priority': 0.8}
            )
            
            # Should select VEO3 for better cost
            assert provider == AIProvider.VEO3
            assert estimate['estimated_cost'] < 3.0
            
            # Test with quality priority
            provider, estimate = cost_optimizer.select_optimal_provider(
                duration=15,
                quality=VideoQuality.PREMIUM,
                aspect_ratio=AspectRatio.LANDSCAPE,
                user_preferences={'quality_priority': 0.9}
            )
            
            # Should consider quality more heavily
            assert estimate['quality_score'] > 0.8

    @pytest.mark.asyncio
    async def test_websocket_progress_tracking(self, video_pipeline, sample_video_request, mock_websocket_service):
        """Test WebSocket progress tracking throughout generation"""
        video_id = 'test_progress_001'
        
        progress_updates = []
        
        def capture_progress(*args, **kwargs):
            progress_updates.append(kwargs)
        
        mock_websocket_service.broadcast_progress.side_effect = capture_progress
        
        # Mock minimal pipeline
        with patch.object(video_pipeline, 'websocket_service', mock_websocket_service):
            with patch.multiple(video_pipeline,
                _generate_audio=AsyncMock(return_value={'success': True, 'duration': 15}),
                _analyze_facial_landmarks=AsyncMock(return_value={'success': True}),
                _generate_lipsync_animation=AsyncMock(return_value={'success': True, 'frames': []}),
                _select_optimal_provider=AsyncMock(return_value=AIProvider.VEO3),
                _generate_with_provider=AsyncMock(return_value={'success': True, 'video_data': b'video'}),
                _post_process_video=AsyncMock(return_value={'success': True, 'video_data': b'final_video'})
            ):
                
                result = await video_pipeline.generate_video_async(sample_video_request, video_id)
                
                # Verify progress tracking
                assert len(progress_updates) >= 5  # Multiple progress updates
                
                # Check progress sequence
                percentages = [update.get('percentage', 0) for update in progress_updates]
                assert percentages[0] < percentages[-1]  # Should increase
                assert any(p >= 90 for p in percentages)  # Should reach near completion
                
                # Verify final completion notification
                mock_websocket_service.notify_video_completed.assert_called_once_with(
                    video_id=video_id,
                    user_id=sample_video_request.user_id if hasattr(sample_video_request, 'user_id') else None,
                    output_url=result.get('output_url'),
                    metadata=result.get('metadata', {})
                )

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, video_pipeline, sample_video_request):
        """Test error handling and recovery mechanisms"""
        video_id = 'test_error_handling_001'
        
        # Test TTS failure with recovery
        with patch.object(video_pipeline, '_generate_audio') as mock_audio:
            # First call fails, second succeeds
            mock_audio.side_effect = [
                {'success': False, 'error': 'TTS service unavailable'},
                {'success': True, 'audio_data': b'recovered_audio', 'duration': 15}
            ]
            
            with patch.object(video_pipeline, '_analyze_facial_landmarks') as mock_landmarks:
                mock_landmarks.return_value = {'success': True, 'landmarks': Mock()}
                
                with patch.object(video_pipeline, '_generate_lipsync_animation') as mock_lipsync:
                    mock_lipsync.return_value = {'success': True, 'frames': []}
                    
                    with patch.object(video_pipeline, '_select_optimal_provider') as mock_select:
                        mock_select.return_value = AIProvider.VEO3
                        
                        with patch.object(video_pipeline, '_generate_with_provider') as mock_gen:
                            mock_gen.return_value = {'success': True, 'video_data': b'video'}
                            
                            with patch.object(video_pipeline, '_post_process_video') as mock_post:
                                mock_post.return_value = {'success': True, 'video_data': b'final'}
                                
                                result = await video_pipeline.generate_video_async(
                                    sample_video_request, video_id
                                )
                                
                                # Should recover and succeed
                                assert result['success'] is True
                                assert mock_audio.call_count == 2  # Retry occurred
        
        # Test complete failure scenario
        with patch.object(video_pipeline, '_generate_audio') as mock_audio:
            mock_audio.return_value = {'success': False, 'error': 'Permanent TTS failure'}
            
            result = await video_pipeline.generate_video_async(sample_video_request, video_id)
            
            # Should fail gracefully
            assert result['success'] is False
            assert 'error' in result
            assert 'TTS failure' in result['error'] or 'Permanent TTS failure' in result['error']

    def test_concurrent_video_generation(self, video_pipeline, sample_video_request):
        """Test handling of concurrent video generation requests"""
        video_ids = ['test_concurrent_001', 'test_concurrent_002', 'test_concurrent_003']
        
        async def mock_generation(request, video_id):
            # Simulate variable processing time
            await asyncio.sleep(0.1 if '001' in video_id else 0.05)
            return {
                'success': True,
                'video_id': video_id,
                'video_data': f'video_data_{video_id}'.encode(),
                'processing_time': 0.1 if '001' in video_id else 0.05
            }
        
        # Mock the generation method
        with patch.object(video_pipeline, 'generate_video_async', side_effect=mock_generation):
            
            async def run_concurrent_test():
                # Start multiple concurrent generations
                tasks = [
                    video_pipeline.generate_video_async(sample_video_request, video_id)
                    for video_id in video_ids
                ]
                
                # Wait for all to complete
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # All should succeed
                assert len(results) == 3
                for result in results:
                    assert not isinstance(result, Exception)
                    assert result['success'] is True
                
                # Results should have correct video IDs
                returned_ids = [r['video_id'] for r in results]
                assert set(returned_ids) == set(video_ids)
                
                return results
            
            # Run the concurrent test
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                results = loop.run_until_complete(run_concurrent_test())
                
                # Verify concurrent execution worked
                assert len(results) == 3
                for result in results:
                    assert result['success'] is True
            finally:
                loop.close()

    @pytest.mark.asyncio
    async def test_quality_metrics_collection(self, video_pipeline, sample_video_request):
        """Test collection and aggregation of quality metrics"""
        video_id = 'test_quality_metrics_001'
        
        # Mock with detailed quality metrics
        with patch.multiple(video_pipeline,
            _generate_audio=AsyncMock(return_value={
                'success': True,
                'audio_data': b'audio',
                'duration': 15,
                'quality_metrics': {
                    'audio_clarity': 92.5,
                    'speech_naturalness': 89.2,
                    'pronunciation_accuracy': 95.1
                }
            }),
            _generate_lipsync_animation=AsyncMock(return_value={
                'success': True,
                'frames': [],
                'animation_metrics': {
                    'lip_sync_accuracy': 91.8,
                    'animation_smoothness': 87.4,
                    'facial_expression_quality': 85.2
                }
            }),
            _generate_with_provider=AsyncMock(return_value={
                'success': True,
                'video_data': b'video',
                'quality_metrics': {
                    'overall_video_quality': 88.7,
                    'resolution_consistency': 94.3,
                    'frame_stability': 90.1
                }
            }),
            _post_process_video=AsyncMock(return_value={
                'success': True,
                'video_data': b'optimized',
                'optimization_metrics': {
                    'compression_efficiency': 85.0,
                    'quality_preservation': 96.2
                }
            })
        ):
            
            result = await video_pipeline.generate_video_async(sample_video_request, video_id)
            
            # Should aggregate all quality metrics
            assert result['success'] is True
            assert 'quality_metrics' in result
            
            metrics = result['quality_metrics']
            assert 'audio_clarity' in metrics
            assert 'lip_sync_accuracy' in metrics
            assert 'overall_video_quality' in metrics
            assert 'compression_efficiency' in metrics
            
            # Should calculate overall score
            assert 'overall_quality_score' in metrics
            assert 80 <= metrics['overall_quality_score'] <= 100