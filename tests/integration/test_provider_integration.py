"""
TalkingPhoto AI MVP - Integration Tests for Provider Switching
Test provider switching, failover, and integration between services
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timedelta
import numpy as np

from services.video_generation_service import (
    VideoGenerationPipeline, VideoGenerationProvider,
    VideoGenerationRequest, ProviderCapabilities
)
from services.cost_optimization_service import (
    CostOptimizationService, ProviderMetrics, CostEstimate
)
from services.ai_service import AIServiceRouter
from models.video import VideoQuality, AspectRatio, AIProvider, VideoStatus
from tests.mocks.ai_providers import create_ai_service_mocks


class TestProviderIntegration:
    """Test integration between different AI providers"""
    
    @pytest.fixture
    def mock_app_context(self):
        """Create mock Flask app context"""
        with patch('services.ai_service.current_app') as mock_app:
            mock_app.config.get.side_effect = lambda key, default=None: {
                'NANO_BANANA_API_KEY': 'test_nano_key',
                'VEO3_API_KEY': 'test_veo3_key',
                'RUNWAY_API_KEY': 'test_runway_key',
                'OPENAI_API_KEY': 'test_openai_key',
                'REDIS_HOST': 'localhost',
                'REDIS_PORT': 6379
            }.get(key, default)
            yield mock_app
    
    @pytest.fixture
    def ai_router(self, mock_app_context):
        """Create AI service router"""
        return AIServiceRouter()
    
    @pytest.fixture
    def cost_optimizer(self, mock_app_context):
        """Create cost optimization service"""
        with patch('services.cost_optimization_service.Redis'):
            return CostOptimizationService()
    
    def test_optimal_service_selection(self, ai_router):
        """Test selecting optimal service based on preferences"""
        # Test economy preference
        economy_service = ai_router.select_optimal_service(
            'video_generation',
            'economy'
        )
        assert economy_service['name'] == 'nano_banana_video'
        assert economy_service['cost'] == 0.08
        
        # Test quality preference
        quality_service = ai_router.select_optimal_service(
            'video_generation',
            'quality'
        )
        assert quality_service['name'] == 'runway'
        assert quality_service['quality'] == 8.8
        
        # Test balanced preference
        balanced_service = ai_router.select_optimal_service(
            'video_generation',
            'balanced'
        )
        assert balanced_service is not None
        assert balanced_service['cost'] <= 0.20
    
    @patch('services.video_generation_service.requests')
    def test_provider_failover_cascade(self, mock_requests, mock_app_context):
        """Test cascading failover through multiple providers"""
        pipeline = VideoGenerationPipeline()
        
        # Configure mock responses
        mock_requests.post.side_effect = [
            Mock(status_code=500, json=lambda: {'error': 'Service unavailable'}),  # Veo3 fails
            Mock(status_code=503, json=lambda: {'error': 'Rate limited'}),  # Runway fails
            Mock(status_code=200, json=lambda: {'job_id': 'heygen_123', 'status': 'processing'})  # HeyGen succeeds
        ]
        
        # Create request
        request = VideoGenerationRequest(
            source_image='base64_image',
            audio_data=b'audio_data',
            script_text='Test script',
            quality=VideoQuality.STANDARD,
            aspect_ratio=AspectRatio.LANDSCAPE,
            duration=10
        )
        
        # Try generation - should failover to HeyGen
        with patch.object(pipeline, '_generate_with_veo3', side_effect=Exception("Veo3 failed")):
            with patch.object(pipeline, '_generate_with_runway', side_effect=Exception("Runway failed")):
                with patch.object(pipeline, '_generate_with_heygen') as mock_heygen:
                    mock_heygen.return_value = {'job_id': 'heygen_123', 'status': 'processing'}
                    
                    result = pipeline.generate_video(request)
                    
                    # Should have tried HeyGen after failures
                    mock_heygen.assert_called_once()
                    assert result['job_id'] == 'heygen_123'
    
    def test_cost_optimization_routing(self, cost_optimizer):
        """Test intelligent routing based on cost optimization"""
        # Set up mock metrics
        with patch.object(cost_optimizer, 'get_provider_metrics') as mock_metrics:
            mock_metrics.side_effect = lambda provider: ProviderMetrics(
                provider=provider,
                success_rate=0.95 if provider == VideoGenerationProvider.VEO3 else 0.90,
                average_processing_time=60 if provider == VideoGenerationProvider.VEO3 else 80,
                average_cost=0.15 if provider == VideoGenerationProvider.VEO3 else 0.20,
                current_load=10 if provider == VideoGenerationProvider.VEO3 else 5,
                error_count=1 if provider == VideoGenerationProvider.VEO3 else 3,
                availability_score=0.95,
                quality_score=0.85
            )
            
            # Get recommendations for different scenarios
            
            # Scenario 1: Optimize for cost
            cost_estimate = cost_optimizer.estimate_cost(
                duration=30,
                quality=VideoQuality.ECONOMY,
                providers=[VideoGenerationProvider.VEO3, VideoGenerationProvider.RUNWAY]
            )
            assert cost_estimate[0].provider == VideoGenerationProvider.VEO3  # Cheaper
            
            # Scenario 2: Optimize for quality
            quality_providers = cost_optimizer.rank_providers_by_quality(
                [VideoGenerationProvider.VEO3, VideoGenerationProvider.RUNWAY]
            )
            assert len(quality_providers) > 0
    
    def test_parallel_provider_requests(self, mock_app_context):
        """Test making parallel requests to multiple providers"""
        mocks = create_ai_service_mocks()
        
        async def make_parallel_requests():
            """Make parallel requests to different providers"""
            tasks = []
            
            # TTS requests
            tasks.append(asyncio.create_task(
                asyncio.to_thread(
                    mocks['elevenlabs'].text_to_speech,
                    'EXAVITQu4vr4xnSDxMaL',
                    'Test text for ElevenLabs'
                )
            ))
            
            tasks.append(asyncio.create_task(
                asyncio.to_thread(
                    mocks['azure_speech'].synthesize_speech,
                    '<speak>Test text for Azure</speak>'
                )
            ))
            
            # Video generation requests
            tasks.append(asyncio.create_task(
                asyncio.to_thread(
                    mocks['veo3'].submit_generation_job,
                    {'image': 'test', 'audio': 'test'}
                )
            ))
            
            tasks.append(asyncio.create_task(
                asyncio.to_thread(
                    mocks['runway'].create_generation,
                    {'prompt': 'test'}
                )
            ))
            
            # Wait for all to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            return results
        
        # Run async tasks
        results = asyncio.run(make_parallel_requests())
        
        # Verify all completed
        assert len(results) == 4
        assert all(not isinstance(r, Exception) for r in results)
        
        # Verify responses
        assert results[0]['status_code'] == 200  # ElevenLabs
        assert results[1]['status_code'] == 200  # Azure
        assert results[2]['status_code'] == 200  # Veo3
        assert results[3]['status_code'] == 201  # Runway


class TestProviderSwitching:
    """Test dynamic provider switching"""
    
    def test_switch_on_error(self):
        """Test switching providers on error"""
        providers = [
            VideoGenerationProvider.VEO3,
            VideoGenerationProvider.RUNWAY,
            VideoGenerationProvider.SYNTHESIA
        ]
        
        current_index = 0
        max_retries = len(providers)
        
        def try_provider():
            nonlocal current_index
            if current_index < len(providers) - 1:
                # Simulate failure
                current_index += 1
                raise Exception(f"Provider {providers[current_index-1]} failed")
            else:
                # Last provider succeeds
                return {'success': True, 'provider': providers[current_index]}
        
        # Try providers until success
        result = None
        for _ in range(max_retries):
            try:
                result = try_provider()
                break
            except Exception:
                continue
        
        assert result is not None
        assert result['provider'] == VideoGenerationProvider.SYNTHESIA
    
    def test_switch_on_capability_mismatch(self):
        """Test switching when provider doesn't support requirements"""
        request = {
            'duration': 180,  # 3 minutes
            'quality': VideoQuality.PREMIUM,
            'aspect_ratio': AspectRatio.PORTRAIT
        }
        
        providers = {
            VideoGenerationProvider.VEO3: {
                'max_duration': 60,
                'qualities': [VideoQuality.STANDARD, VideoQuality.PREMIUM]
            },
            VideoGenerationProvider.RUNWAY: {
                'max_duration': 120,
                'qualities': [VideoQuality.PREMIUM]
            },
            VideoGenerationProvider.SYNTHESIA: {
                'max_duration': 240,
                'qualities': [VideoQuality.STANDARD, VideoQuality.PREMIUM]
            }
        }
        
        # Find capable provider
        capable_provider = None
        for provider, capabilities in providers.items():
            if (capabilities['max_duration'] >= request['duration'] and
                request['quality'] in capabilities['qualities']):
                capable_provider = provider
                break
        
        assert capable_provider == VideoGenerationProvider.SYNTHESIA
    
    def test_load_balancing(self):
        """Test load balancing across providers"""
        provider_loads = {
            VideoGenerationProvider.VEO3: 0,
            VideoGenerationProvider.RUNWAY: 0,
            VideoGenerationProvider.D_ID: 0
        }
        
        # Simulate 100 requests
        for i in range(100):
            # Simple round-robin load balancing
            providers = list(provider_loads.keys())
            selected = providers[i % len(providers)]
            provider_loads[selected] += 1
        
        # Check distribution is balanced
        loads = list(provider_loads.values())
        assert max(loads) - min(loads) <= 1  # Difference should be at most 1
        
        # Check all providers got requests
        assert all(load > 0 for load in loads)


class TestEndToEndPipeline:
    """Test complete end-to-end pipeline with all components"""
    
    @patch('services.video_generation_service.TTSService')
    @patch('services.video_generation_service.LipSyncAnimationEngine')
    def test_complete_video_generation_pipeline(self, mock_lipsync, mock_tts):
        """Test complete pipeline from text to video"""
        # Configure mocks
        mock_tts_instance = Mock()
        mock_tts_instance.synthesize_speech.return_value = {
            'audio_data': b'mock_audio_data',
            'duration': 5.0,
            'voice_id': 'test_voice'
        }
        mock_tts.return_value = mock_tts_instance
        
        mock_lipsync_instance = Mock()
        mock_lipsync_instance.generate_animation.return_value = {
            'keyframes': [{'time': 0, 'viseme': 'A'}],
            'duration': 5.0
        }
        mock_lipsync.return_value = mock_lipsync_instance
        
        # Create pipeline
        with patch('services.video_generation_service.current_app'):
            pipeline = VideoGenerationPipeline()
        
        # Create request
        request = VideoGenerationRequest(
            source_image='base64_test_image',
            audio_data=None,  # Will be generated
            script_text='Hello, this is a test video.',
            quality=VideoQuality.STANDARD,
            aspect_ratio=AspectRatio.LANDSCAPE,
            duration=5.0
        )
        
        # Mock provider selection and generation
        with patch.object(pipeline, 'select_provider') as mock_select:
            mock_select.return_value = VideoGenerationProvider.VEO3
            
            with patch.object(pipeline, '_generate_with_veo3') as mock_generate:
                mock_generate.return_value = {
                    'job_id': 'test_job_123',
                    'status': 'processing',
                    'provider': 'veo3'
                }
                
                # Run pipeline
                result = pipeline.generate_video(request)
                
                # Verify TTS was called
                mock_tts_instance.synthesize_speech.assert_called()
                
                # Verify generation was called
                mock_generate.assert_called_once()
                
                # Verify result
                assert result['job_id'] == 'test_job_123'
                assert result['provider'] == 'veo3'
    
    def test_pipeline_error_recovery(self):
        """Test pipeline recovery from errors"""
        error_log = []
        
        def component_with_retry(name, max_retries=3):
            """Simulate component that might fail"""
            attempts = 0
            while attempts < max_retries:
                attempts += 1
                try:
                    if attempts < 2:
                        # Fail first attempt
                        error_log.append(f"{name} failed attempt {attempts}")
                        raise Exception(f"{name} temporary failure")
                    else:
                        # Succeed on retry
                        return f"{name} success"
                except Exception as e:
                    if attempts >= max_retries:
                        raise
                    time.sleep(0.1)  # Brief delay before retry
            
            return None
        
        # Test each component
        tts_result = component_with_retry("TTS")
        lipsync_result = component_with_retry("LipSync")
        video_result = component_with_retry("VideoGen")
        
        # All should eventually succeed
        assert tts_result == "TTS success"
        assert lipsync_result == "LipSync success"
        assert video_result == "VideoGen success"
        
        # Should have logged failures
        assert len(error_log) == 3  # One failure for each component
    
    def test_pipeline_monitoring(self):
        """Test pipeline monitoring and metrics collection"""
        metrics = {
            'requests': 0,
            'successes': 0,
            'failures': 0,
            'total_duration': 0,
            'provider_usage': {}
        }
        
        def track_request(provider, duration, success):
            """Track pipeline metrics"""
            metrics['requests'] += 1
            if success:
                metrics['successes'] += 1
            else:
                metrics['failures'] += 1
            
            metrics['total_duration'] += duration
            
            if provider not in metrics['provider_usage']:
                metrics['provider_usage'][provider] = 0
            metrics['provider_usage'][provider] += 1
        
        # Simulate requests
        track_request('veo3', 45, True)
        track_request('runway', 60, True)
        track_request('veo3', 30, False)
        track_request('d-id', 25, True)
        
        # Calculate stats
        success_rate = metrics['successes'] / metrics['requests']
        avg_duration = metrics['total_duration'] / metrics['requests']
        
        assert metrics['requests'] == 4
        assert metrics['successes'] == 3
        assert success_rate == 0.75
        assert avg_duration == 40  # (45+60+30+25)/4
        assert metrics['provider_usage']['veo3'] == 2


class TestConcurrentRequests:
    """Test handling concurrent requests"""
    
    def test_concurrent_provider_access(self):
        """Test concurrent access to same provider"""
        mocks = create_ai_service_mocks()
        veo3 = mocks['veo3']
        
        # Submit multiple jobs concurrently
        job_ids = []
        for i in range(5):
            response = veo3.submit_generation_job({'request': i})
            if response['status_code'] == 200:
                job_ids.append(response['job_id'])
        
        assert len(job_ids) == 5
        assert len(set(job_ids)) == 5  # All unique
        
        # Check all jobs are tracked
        for job_id in job_ids:
            status = veo3.get_job_status(job_id)
            assert status['status_code'] == 200
    
    def test_queue_management(self):
        """Test request queue management"""
        from collections import deque
        
        class RequestQueue:
            def __init__(self, max_size=10):
                self.queue = deque(maxlen=max_size)
                self.processing = set()
            
            def add(self, request_id):
                if len(self.queue) >= self.queue.maxlen:
                    return False
                self.queue.append(request_id)
                return True
            
            def get_next(self):
                if self.queue:
                    request_id = self.queue.popleft()
                    self.processing.add(request_id)
                    return request_id
                return None
            
            def complete(self, request_id):
                self.processing.discard(request_id)
        
        # Test queue
        queue = RequestQueue(max_size=3)
        
        # Add requests
        assert queue.add('req1') == True
        assert queue.add('req2') == True
        assert queue.add('req3') == True
        assert queue.add('req4') == False  # Queue full
        
        # Process requests
        req = queue.get_next()
        assert req == 'req1'
        assert 'req1' in queue.processing
        
        queue.complete('req1')
        assert 'req1' not in queue.processing
        
        # Now can add more
        assert queue.add('req4') == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])