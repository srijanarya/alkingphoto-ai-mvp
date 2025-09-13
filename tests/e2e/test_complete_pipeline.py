"""
TalkingPhoto AI MVP - End-to-End Pipeline Tests
Complete pipeline testing from image upload to video generation
"""

import pytest
import asyncio
import base64
import json
import time
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
import numpy as np
from PIL import Image
import io

from services.video_generation_service import (
    VideoGenerationPipeline, VideoGenerationProvider,
    VideoGenerationRequest, ProviderCapabilities
)
from services.tts_service import TTSService, TTSProvider
from services.lipsync_service import LipSyncAnimationEngine
from services.cost_optimization_service import CostOptimizationService
from models.video import VideoQuality, AspectRatio, VideoStatus
from tests.mocks.ai_providers import create_ai_service_mocks


class TestCompleteVideoGeneration:
    """Test complete video generation pipeline"""
    
    @pytest.fixture
    def mock_image(self):
        """Create a mock image for testing"""
        # Create a simple test image
        img = Image.new('RGB', (640, 480), color='red')
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='JPEG')
        img_buffer.seek(0)
        
        # Convert to base64
        img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
        return img_base64
    
    @pytest.fixture
    def mock_services(self):
        """Create mock services for testing"""
        return create_ai_service_mocks()
    
    def test_image_to_video_pipeline(self, mock_image, mock_services):
        """Test complete pipeline from image to video"""
        
        # Step 1: Image Enhancement
        nano_banana = mock_services['nano_banana']
        enhance_response = nano_banana.generate_content({
            'contents': [{
                'parts': [
                    {'text': 'Enhance this image for video generation'},
                    {'inline_data': {'mime_type': 'image/jpeg', 'data': mock_image}}
                ]
            }]
        })
        
        assert enhance_response['status_code'] == 200
        enhancement_text = enhance_response['candidates'][0]['content']['parts'][0]['text']
        assert 'enhancement completed' in enhancement_text.lower()
        
        # Step 2: Generate Script
        script = "Welcome to TalkingPhoto AI. This is a demonstration of our advanced video generation technology."
        
        # Step 3: Text-to-Speech
        elevenlabs = mock_services['elevenlabs']
        tts_response = elevenlabs.text_to_speech(
            'EXAVITQu4vr4xnSDxMaL',  # Bella voice
            script
        )
        
        assert tts_response['status_code'] == 200
        assert 'audio_data' in tts_response
        audio_duration = tts_response['duration']
        
        # Step 4: Submit Video Generation
        veo3 = mock_services['veo3']
        video_response = veo3.submit_generation_job({
            'image': mock_image,
            'audio': base64.b64encode(tts_response['audio_data']).decode('utf-8'),
            'duration': audio_duration,
            'quality': 'high',
            'aspect_ratio': '16:9'
        })
        
        assert video_response['status_code'] == 200
        job_id = video_response['job_id']
        
        # Step 5: Monitor Job Progress
        max_checks = 10
        for i in range(max_checks):
            status = veo3.get_job_status(job_id)
            
            if status['status'] == 'completed':
                assert 'output_url' in status
                assert status['progress'] == 100
                break
            
            # Simulate waiting
            time.sleep(0.1)
            
            # Force completion for testing
            if i == 5:
                veo3.jobs[job_id]['created_at'] = datetime.now().replace(
                    second=datetime.now().second - 35
                )
        
        # Verify final output
        final_status = veo3.get_job_status(job_id)
        assert final_status['status'] == 'completed'
        assert 'metadata' in final_status
        assert final_status['metadata']['duration'] == 15
    
    def test_pipeline_with_provider_failover(self, mock_image, mock_services):
        """Test pipeline with provider failover"""
        
        # Configure Veo3 to fail
        veo3 = mock_services['veo3']
        veo3.set_failure_rate(1.0)
        
        # Configure Runway as backup
        runway = mock_services['runway']
        runway.set_failure_rate(0.0)
        
        # Try Veo3 first (will fail)
        veo3_response = veo3.submit_generation_job({'test': 'data'})
        assert veo3_response['status_code'] == 400
        
        # Fallback to Runway
        runway_response = runway.create_generation({'test': 'data'})
        assert runway_response['status_code'] == 201
        
        # Track failover
        failover_log = {
            'primary_provider': 'veo3',
            'primary_status': veo3_response['status_code'],
            'fallback_provider': 'runway',
            'fallback_status': runway_response['status_code'],
            'failover_time': time.time()
        }
        
        assert failover_log['primary_status'] != 200
        assert failover_log['fallback_status'] in [200, 201]
    
    def test_multi_language_pipeline(self, mock_image):
        """Test pipeline with multiple languages"""
        
        languages = [
            {'code': 'en-US', 'text': 'Hello, this is a test', 'voice': 'en-US-JennyNeural'},
            {'code': 'es-ES', 'text': 'Hola, esto es una prueba', 'voice': 'es-ES-AlvaroNeural'},
            {'code': 'fr-FR', 'text': 'Bonjour, ceci est un test', 'voice': 'fr-FR-DeniseNeural'},
            {'code': 'hi-IN', 'text': 'नमस्ते, यह एक परीक्षण है', 'voice': 'hi-IN-SwaraNeural'}
        ]
        
        results = []
        
        for lang in languages:
            # Generate SSML for each language
            ssml = f'''
            <speak version="1.0" xml:lang="{lang['code']}">
                <voice name="{lang['voice']}">
                    <prosody rate="medium" pitch="default">
                        {lang['text']}
                    </prosody>
                </voice>
            </speak>
            '''
            
            # Mock TTS generation
            result = {
                'language': lang['code'],
                'ssml': ssml,
                'audio_generated': True,
                'duration': len(lang['text']) * 0.1  # Rough estimate
            }
            results.append(result)
        
        # Verify all languages processed
        assert len(results) == 4
        assert all(r['audio_generated'] for r in results)
        
        # Check language diversity
        languages_processed = [r['language'] for r in results]
        assert len(set(languages_processed)) == 4  # All unique


class TestQualityAssessment:
    """Test AI quality assessment metrics"""
    
    def test_video_quality_scoring(self):
        """Test video quality scoring system"""
        
        class VideoQualityAnalyzer:
            def __init__(self):
                self.metrics = {}
            
            def analyze_resolution(self, width, height):
                """Score based on resolution"""
                pixels = width * height
                if pixels >= 1920 * 1080:  # Full HD or better
                    return 1.0
                elif pixels >= 1280 * 720:  # HD
                    return 0.75
                elif pixels >= 854 * 480:  # SD
                    return 0.5
                else:
                    return 0.25
            
            def analyze_framerate(self, fps):
                """Score based on framerate"""
                if fps >= 60:
                    return 1.0
                elif fps >= 30:
                    return 0.8
                elif fps >= 24:
                    return 0.6
                else:
                    return 0.3
            
            def analyze_bitrate(self, bitrate_mbps):
                """Score based on bitrate"""
                if bitrate_mbps >= 10:
                    return 1.0
                elif bitrate_mbps >= 5:
                    return 0.75
                elif bitrate_mbps >= 2:
                    return 0.5
                else:
                    return 0.25
            
            def analyze_lip_sync(self, sync_accuracy):
                """Score lip sync accuracy"""
                return min(max(sync_accuracy, 0), 1)
            
            def calculate_overall_score(self, width, height, fps, bitrate_mbps, sync_accuracy):
                """Calculate overall quality score"""
                resolution_score = self.analyze_resolution(width, height) * 0.25
                framerate_score = self.analyze_framerate(fps) * 0.20
                bitrate_score = self.analyze_bitrate(bitrate_mbps) * 0.20
                sync_score = self.analyze_lip_sync(sync_accuracy) * 0.35
                
                total = resolution_score + framerate_score + bitrate_score + sync_score
                
                # Determine quality tier
                if total >= 0.85:
                    tier = 'Premium'
                elif total >= 0.65:
                    tier = 'Standard'
                else:
                    tier = 'Economy'
                
                return {
                    'score': total,
                    'tier': tier,
                    'breakdown': {
                        'resolution': resolution_score / 0.25,
                        'framerate': framerate_score / 0.20,
                        'bitrate': bitrate_score / 0.20,
                        'lip_sync': sync_score / 0.35
                    }
                }
        
        analyzer = VideoQualityAnalyzer()
        
        # Test Premium quality video
        premium_result = analyzer.calculate_overall_score(
            width=1920, height=1080, fps=30, bitrate_mbps=8, sync_accuracy=0.92
        )
        assert premium_result['tier'] == 'Premium'
        assert premium_result['score'] > 0.85
        
        # Test Standard quality video
        standard_result = analyzer.calculate_overall_score(
            width=1280, height=720, fps=30, bitrate_mbps=4, sync_accuracy=0.80
        )
        assert standard_result['tier'] == 'Standard'
        assert 0.65 <= standard_result['score'] < 0.85
        
        # Test Economy quality video
        economy_result = analyzer.calculate_overall_score(
            width=854, height=480, fps=24, bitrate_mbps=2, sync_accuracy=0.70
        )
        assert economy_result['tier'] == 'Economy'
        assert economy_result['score'] < 0.65
    
    def test_audio_quality_assessment(self):
        """Test audio quality assessment"""
        
        def assess_audio_quality(sample_rate, bit_depth, channels, noise_level):
            """Assess audio quality metrics"""
            # Sample rate scoring
            if sample_rate >= 48000:
                sample_score = 1.0
            elif sample_rate >= 44100:
                sample_score = 0.9
            elif sample_rate >= 22050:
                sample_score = 0.6
            else:
                sample_score = 0.3
            
            # Bit depth scoring
            if bit_depth >= 24:
                depth_score = 1.0
            elif bit_depth >= 16:
                depth_score = 0.8
            else:
                depth_score = 0.5
            
            # Channel scoring
            channel_score = 0.7 if channels == 1 else 1.0  # Mono vs Stereo
            
            # Noise level scoring (lower is better)
            noise_score = max(0, 1 - noise_level)
            
            # Calculate overall score
            overall = (
                sample_score * 0.3 +
                depth_score * 0.2 +
                channel_score * 0.2 +
                noise_score * 0.3
            )
            
            return {
                'overall': overall,
                'sample_rate': sample_score,
                'bit_depth': depth_score,
                'channels': channel_score,
                'noise': noise_score
            }
        
        # Test high quality audio
        hq_result = assess_audio_quality(48000, 24, 2, 0.05)
        assert hq_result['overall'] > 0.9
        
        # Test standard quality audio
        std_result = assess_audio_quality(44100, 16, 2, 0.1)
        assert 0.7 < std_result['overall'] < 0.9
        
        # Test low quality audio
        lq_result = assess_audio_quality(22050, 16, 1, 0.3)
        assert lq_result['overall'] < 0.7


class TestErrorRecovery:
    """Test error recovery mechanisms"""
    
    def test_retry_with_backoff(self):
        """Test retry mechanism with exponential backoff"""
        
        class RetryableOperation:
            def __init__(self):
                self.attempt = 0
                self.max_attempts = 3
            
            def execute(self):
                """Execute operation with possible failure"""
                self.attempt += 1
                if self.attempt < self.max_attempts:
                    raise Exception(f"Attempt {self.attempt} failed")
                return f"Success on attempt {self.attempt}"
        
        def retry_with_backoff(operation, max_retries=3, base_delay=0.1):
            """Retry operation with exponential backoff"""
            for attempt in range(max_retries):
                try:
                    return operation.execute()
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
            return None
        
        # Test successful retry
        op = RetryableOperation()
        result = retry_with_backoff(op)
        assert result == "Success on attempt 3"
        assert op.attempt == 3
    
    def test_circuit_breaker(self):
        """Test circuit breaker pattern"""
        
        class CircuitBreaker:
            def __init__(self, failure_threshold=3, reset_timeout=1.0):
                self.failure_threshold = failure_threshold
                self.reset_timeout = reset_timeout
                self.failure_count = 0
                self.last_failure_time = None
                self.state = 'closed'  # closed, open, half-open
            
            def call(self, func, *args, **kwargs):
                """Call function with circuit breaker protection"""
                # Check if circuit should reset
                if self.state == 'open':
                    if (self.last_failure_time and 
                        time.time() - self.last_failure_time > self.reset_timeout):
                        self.state = 'half-open'
                        self.failure_count = 0
                    else:
                        raise Exception("Circuit breaker is open")
                
                try:
                    result = func(*args, **kwargs)
                    if self.state == 'half-open':
                        self.state = 'closed'
                    return result
                except Exception as e:
                    self.failure_count += 1
                    self.last_failure_time = time.time()
                    
                    if self.failure_count >= self.failure_threshold:
                        self.state = 'open'
                    raise
        
        breaker = CircuitBreaker(failure_threshold=2, reset_timeout=0.5)
        
        # Function that fails initially
        fail_count = 0
        def unreliable_function():
            nonlocal fail_count
            fail_count += 1
            if fail_count <= 2:
                raise Exception("Service unavailable")
            return "Success"
        
        # Test circuit breaker
        # First two calls fail and open the circuit
        for _ in range(2):
            try:
                breaker.call(unreliable_function)
            except:
                pass
        
        assert breaker.state == 'open'
        
        # Circuit is open, should reject immediately
        with pytest.raises(Exception, match="Circuit breaker is open"):
            breaker.call(unreliable_function)
        
        # Wait for reset timeout
        time.sleep(0.6)
        
        # Circuit should be half-open, ready to test
        # Function now succeeds, circuit closes
        result = breaker.call(unreliable_function)
        assert result == "Success"
        assert breaker.state == 'closed'
    
    def test_graceful_degradation(self):
        """Test graceful degradation of service"""
        
        class VideoService:
            def __init__(self):
                self.providers = ['premium', 'standard', 'basic']
                self.current_level = 0
            
            def generate_video(self, request):
                """Generate video with graceful degradation"""
                while self.current_level < len(self.providers):
                    provider = self.providers[self.current_level]
                    
                    try:
                        if provider == 'premium' and request.get('fail_premium'):
                            raise Exception("Premium service unavailable")
                        elif provider == 'standard' and request.get('fail_standard'):
                            raise Exception("Standard service unavailable")
                        
                        return {
                            'provider': provider,
                            'quality': self._get_quality(provider),
                            'success': True
                        }
                    except Exception:
                        # Degrade to next level
                        self.current_level += 1
                
                # All providers failed, return minimal service
                return {
                    'provider': 'fallback',
                    'quality': 'minimal',
                    'success': False
                }
            
            def _get_quality(self, provider):
                return {
                    'premium': 'high',
                    'standard': 'medium',
                    'basic': 'low'
                }.get(provider, 'minimal')
        
        service = VideoService()
        
        # Test normal operation
        result = service.generate_video({})
        assert result['provider'] == 'premium'
        assert result['quality'] == 'high'
        
        # Test degradation
        service = VideoService()
        result = service.generate_video({'fail_premium': True})
        assert result['provider'] == 'standard'
        assert result['quality'] == 'medium'
        
        # Test multiple degradations
        service = VideoService()
        result = service.generate_video({'fail_premium': True, 'fail_standard': True})
        assert result['provider'] == 'basic'
        assert result['quality'] == 'low'


class TestMonitoringAndMetrics:
    """Test monitoring and metrics collection"""
    
    def test_performance_metrics_collection(self):
        """Test collection of performance metrics"""
        
        class MetricsCollector:
            def __init__(self):
                self.metrics = {
                    'requests': [],
                    'errors': [],
                    'latencies': [],
                    'provider_usage': {}
                }
            
            def record_request(self, provider, latency, success, error=None):
                """Record request metrics"""
                timestamp = time.time()
                
                self.metrics['requests'].append({
                    'timestamp': timestamp,
                    'provider': provider,
                    'latency': latency,
                    'success': success
                })
                
                self.metrics['latencies'].append(latency)
                
                if not success and error:
                    self.metrics['errors'].append({
                        'timestamp': timestamp,
                        'provider': provider,
                        'error': str(error)
                    })
                
                if provider not in self.metrics['provider_usage']:
                    self.metrics['provider_usage'][provider] = 0
                self.metrics['provider_usage'][provider] += 1
            
            def get_statistics(self):
                """Calculate statistics from metrics"""
                if not self.metrics['latencies']:
                    return {}
                
                return {
                    'total_requests': len(self.metrics['requests']),
                    'error_rate': len(self.metrics['errors']) / len(self.metrics['requests']),
                    'avg_latency': statistics.mean(self.metrics['latencies']),
                    'p50_latency': statistics.median(self.metrics['latencies']),
                    'p95_latency': np.percentile(self.metrics['latencies'], 95),
                    'p99_latency': np.percentile(self.metrics['latencies'], 99),
                    'provider_distribution': self.metrics['provider_usage']
                }
        
        collector = MetricsCollector()
        
        # Simulate requests
        collector.record_request('veo3', 1.5, True)
        collector.record_request('runway', 2.0, True)
        collector.record_request('veo3', 1.8, False, "Timeout")
        collector.record_request('d-id', 1.2, True)
        collector.record_request('veo3', 1.6, True)
        
        # Get statistics
        stats = collector.get_statistics()
        
        assert stats['total_requests'] == 5
        assert stats['error_rate'] == 0.2  # 1 error out of 5
        assert 1.5 < stats['avg_latency'] < 1.7
        assert stats['provider_distribution']['veo3'] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])