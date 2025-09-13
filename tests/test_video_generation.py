"""
TalkingPhoto AI MVP - Video Generation Tests
Comprehensive test suite for Epic 3: AI Video Generation Engine
"""

import pytest
import json
import base64
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timezone
import numpy as np

from services.tts_service import (
    TTSService, TTSProvider, VoiceGender, VoiceEmotion, TTSVoice
)
from services.lipsync_service import (
    LipSyncAnimationEngine, VisemeType, Viseme, FacialExpression,
    FacialLandmarks, PhonemeMapper
)
from services.video_generation_service import (
    VideoGenerationPipeline, VideoGenerationProvider, VideoGenerationRequest,
    ProviderCapabilities
)
from services.cost_optimization_service import (
    CostOptimizationService, ProviderMetrics, CostEstimate
)
from services.websocket_service import WebSocketService
from models.video import VideoQuality, AspectRatio, AIProvider


class TestTTSService:
    """Test Text-to-Speech Service"""
    
    @pytest.fixture
    def tts_service(self):
        with patch('services.tts_service.current_app') as mock_app:
            mock_app.config.get.return_value = 'test_api_key'
            return TTSService()
    
    def test_get_available_voices(self, tts_service):
        """Test voice listing functionality"""
        # Test getting all voices
        voices = tts_service.get_available_voices()
        assert len(voices) > 0
        assert all('voice_id' in v for v in voices)
        
        # Test filtering by language
        english_voices = tts_service.get_available_voices(language='en')
        assert all('en' in v['language'] for v in english_voices)
        
        # Test filtering by gender
        female_voices = tts_service.get_available_voices(gender=VoiceGender.FEMALE)
        assert all(v['gender'] == 'female' for v in female_voices)
        
        # Test filtering by provider
        azure_voices = tts_service.get_available_voices(provider=TTSProvider.AZURE)
        assert all(v['provider'] == 'azure' for v in azure_voices)
    
    def test_generate_ssml(self, tts_service):
        """Test SSML generation"""
        text = "Hello, this is a test."
        options = {
            'language': 'en-US',
            'voice_name': 'TestVoice',
            'rate': 'fast',
            'pitch': 'high',
            'volume': 'loud',
            'style': 'cheerful',
            'style_degree': 1.5
        }
        
        ssml = tts_service.generate_ssml(text, options)
        
        assert '<speak' in ssml
        assert 'xml:lang="en-US"' in ssml
        assert '<voice name="TestVoice">' in ssml
        assert 'rate="fast"' in ssml
        assert 'pitch="high"' in ssml
        assert 'volume="loud"' in ssml
        assert '</speak>' in ssml
    
    @patch('services.tts_service.speechsdk')
    def test_synthesize_with_azure(self, mock_speechsdk, tts_service):
        """Test Azure TTS synthesis"""
        # Mock Azure Speech SDK
        mock_result = Mock()
        mock_result.reason = mock_speechsdk.ResultReason.SynthesizingAudioCompleted
        mock_result.audio_data = b'mock_audio_data'
        
        mock_synthesizer = Mock()
        mock_synthesizer.speak_text_async.return_value.get.return_value = mock_result
        mock_speechsdk.SpeechSynthesizer.return_value = mock_synthesizer
        
        # Test synthesis
        result = tts_service.synthesize_speech(
            "Test text",
            'en-US-JennyNeural',
            {'emotion': 'cheerful'}
        )
        
        assert result['success'] is True
        assert 'audio_data' in result
        assert result['provider'] == 'azure'
        assert result['cost'] > 0
    
    @patch('requests.post')
    def test_synthesize_with_elevenlabs(self, mock_post, tts_service):
        """Test ElevenLabs TTS synthesis"""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'mock_audio_mp3'
        mock_post.return_value = mock_response
        
        # Mock MP3 to WAV conversion
        with patch.object(tts_service, '_convert_mp3_to_wav', return_value=b'mock_audio_wav'):
            result = tts_service.synthesize_speech(
                "Test text",
                'EXAVITQu4vr4xnSDxMaL',  # Bella voice
                {'stability': 0.5}
            )
        
        assert result['success'] is True
        assert result['provider'] == 'elevenlabs'
        mock_post.assert_called_once()
    
    def test_estimate_speech_duration(self, tts_service):
        """Test speech duration estimation"""
        text = "This is a test sentence with ten words in it."
        duration = tts_service.estimate_speech_duration(text, words_per_minute=150)
        
        # 10 words at 150 wpm = 0.0667 minutes = 4 seconds
        assert 3 <= duration <= 5
    
    def test_optimize_text_for_speech(self, tts_service):
        """Test text optimization for TTS"""
        text = "Dr. Smith lives on St. Ave. in the U.S."
        optimized = tts_service.optimize_text_for_speech(text)
        
        assert "Doctor" in optimized
        assert "Street" in optimized
        assert "Avenue" in optimized
        assert "United States" in optimized
    
    def test_calculate_tts_cost(self, tts_service):
        """Test TTS cost calculation"""
        text_length = 1000
        
        # Test different provider costs
        azure_cost = tts_service._calculate_tts_cost(text_length, TTSProvider.AZURE)
        elevenlabs_cost = tts_service._calculate_tts_cost(text_length, TTSProvider.ELEVENLABS)
        google_cost = tts_service._calculate_tts_cost(text_length, TTSProvider.GOOGLE)
        
        assert azure_cost < elevenlabs_cost  # Azure should be cheaper than ElevenLabs
        assert google_cost == azure_cost  # Google and Azure have same pricing


class TestLipSyncAnimationEngine:
    """Test Lip-Sync Animation Engine"""
    
    @pytest.fixture
    def lipsync_engine(self):
        with patch('services.lipsync_service.current_app') as mock_app:
            mock_app.config.get.return_value = 'test_path'
            return LipSyncAnimationEngine()
    
    @pytest.fixture
    def mock_landmarks(self):
        return FacialLandmarks(
            points=np.random.rand(468, 3),
            confidence=0.95,
            face_rect=(100, 100, 200, 200),
            model_type='mediapipe'
        )
    
    def test_phoneme_to_viseme_mapping(self):
        """Test phoneme to viseme conversion"""
        assert PhonemeMapper.phoneme_to_viseme('AA') == VisemeType.AA
        assert PhonemeMapper.phoneme_to_viseme('EE') == VisemeType.EE
        assert PhonemeMapper.phoneme_to_viseme('MM') == VisemeType.MM
        assert PhonemeMapper.phoneme_to_viseme('SIL') == VisemeType.SILENCE
        assert PhonemeMapper.phoneme_to_viseme('UNKNOWN') == VisemeType.SILENCE
    
    @patch('cv2.imread')
    def test_extract_facial_landmarks(self, mock_imread, lipsync_engine):
        """Test facial landmark extraction"""
        # Mock image
        mock_imread.return_value = np.zeros((640, 480, 3), dtype=np.uint8)
        
        with patch.object(lipsync_engine.mp_face_mesh, 'FaceMesh') as mock_face_mesh:
            # Mock MediaPipe results
            mock_results = Mock()
            mock_landmark = Mock()
            mock_landmark.x = 0.5
            mock_landmark.y = 0.5
            mock_landmark.z = 0.0
            mock_results.multi_face_landmarks = [[mock_landmark] * 468]
            
            mock_face_mesh.return_value.__enter__.return_value.process.return_value = mock_results
            
            landmarks = lipsync_engine._extract_facial_landmarks('test_image.jpg')
            
            assert landmarks is not None
            assert landmarks.model_type == 'mediapipe'
            assert landmarks.confidence == 0.95
            assert len(landmarks.points) == 468
    
    def test_text_to_visemes(self, lipsync_engine):
        """Test text to viseme conversion"""
        text = "Hello world"
        duration = 2.0
        
        visemes = lipsync_engine._text_to_visemes(text, duration)
        
        assert len(visemes) > 0
        assert all(isinstance(v, Viseme) for v in visemes)
        assert any(v.type == VisemeType.SILENCE for v in visemes)  # Should have silence between words
        assert visemes[-1].end_time <= duration
    
    def test_audio_amplitude_to_visemes(self, lipsync_engine):
        """Test audio amplitude-based viseme generation"""
        # Create mock audio data
        sample_rate = 16000
        duration = 1.0
        samples = np.random.randint(-32768, 32767, int(sample_rate * duration), dtype=np.int16)
        
        # Create WAV format data
        import wave
        import io
        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            wav.writeframes(samples.tobytes())
        
        audio_data = wav_io.getvalue()
        
        visemes = lipsync_engine._audio_amplitude_to_visemes(audio_data, duration)
        
        assert len(visemes) > 0
        assert all(isinstance(v, Viseme) for v in visemes)
        assert all(0 <= v.intensity <= 1 for v in visemes)
    
    def test_generate_facial_expressions(self, lipsync_engine):
        """Test facial expression generation"""
        audio_data = b'mock_audio'
        n_frames = 30
        
        # Test different emotions
        for emotion in ['neutral', 'happy', 'sad', 'angry', 'excited']:
            expressions = lipsync_engine._generate_facial_expressions(
                audio_data, emotion, n_frames
            )
            
            assert len(expressions) == n_frames
            assert all(isinstance(e, FacialExpression) for e in expressions)
            
            # Check emotion-specific attributes
            if emotion == 'happy':
                assert any(e.smile > 0 for e in expressions)
            elif emotion == 'sad':
                assert any(e.smile < 0 for e in expressions)
    
    def test_calculate_mouth_deformation(self, lipsync_engine):
        """Test mouth deformation calculation"""
        # Test different visemes
        for viseme_type in VisemeType:
            deformation = lipsync_engine._calculate_mouth_deformation(viseme_type, 1.0)
            
            assert len(deformation) == 3
            assert all(isinstance(d, (int, float)) for d in deformation)
            
            # Check specific viseme characteristics
            if viseme_type == VisemeType.AA:
                assert deformation[2] > 0.5  # Should be open
            elif viseme_type == VisemeType.MM:
                assert deformation[2] == 0  # Should be closed
    
    @patch('cv2.imread')
    def test_create_animation_frames(self, mock_imread, lipsync_engine, mock_landmarks):
        """Test animation frame creation"""
        # Mock image
        mock_imread.return_value = np.zeros((640, 480, 3), dtype=np.uint8)
        
        # Create test visemes
        visemes = [
            Viseme(VisemeType.SILENCE, 0.0, 0.1, 0.0, 'SIL'),
            Viseme(VisemeType.AA, 0.1, 0.2, 0.8, 'AA'),
            Viseme(VisemeType.EE, 0.2, 0.3, 0.6, 'EE')
        ]
        
        # Create test expressions
        expressions = [FacialExpression() for _ in range(10)]
        
        # Test frame creation
        with patch.object(lipsync_engine, '_apply_animation_to_frame', 
                         return_value=np.zeros((640, 480, 3))):
            frames = lipsync_engine._create_animation_frames(
                'test_image.jpg',
                mock_landmarks,
                visemes,
                expressions,
                {'animation_intensity': 1.0, 'smooth_transitions': True}
            )
        
        assert len(frames) > 0
        assert all('frame_number' in f for f in frames)
        assert all('timestamp' in f for f in frames)
        assert all('viseme' in f for f in frames)
        assert all('data' in f for f in frames)
    
    def test_calculate_animation_metrics(self, lipsync_engine):
        """Test animation metrics calculation"""
        frames = [
            {'viseme_intensity': 0.5},
            {'viseme_intensity': 0.6},
            {'viseme_intensity': 0.7}
        ]
        
        visemes = [
            Viseme(VisemeType.AA, 0.0, 0.1, 0.8, 'AA'),
            Viseme(VisemeType.EE, 0.1, 0.2, 0.6, 'EE'),
            Viseme(VisemeType.SILENCE, 0.2, 0.3, 0.0, 'SIL')
        ]
        
        metrics = lipsync_engine._calculate_animation_metrics(frames, visemes)
        
        assert 'lip_sync_accuracy' in metrics
        assert 'animation_smoothness' in metrics
        assert 'viseme_coverage' in metrics
        assert 0 <= metrics['lip_sync_accuracy'] <= 100
        assert 0 <= metrics['animation_smoothness'] <= 100


class TestVideoGenerationPipeline:
    """Test Video Generation Pipeline"""
    
    @pytest.fixture
    def video_pipeline(self):
        with patch('services.video_generation_service.current_app') as mock_app:
            mock_app.config.get.return_value = 'test_value'
            with patch('services.video_generation_service.Redis'):
                return VideoGenerationPipeline()
    
    @pytest.fixture
    def video_request(self):
        return VideoGenerationRequest(
            source_image='test_image.jpg',
            audio_data=b'test_audio',
            script_text='Test script',
            quality=VideoQuality.STANDARD,
            aspect_ratio=AspectRatio.LANDSCAPE,
            duration=30.0
        )
    
    @pytest.mark.asyncio
    async def test_generate_audio(self, video_pipeline, video_request):
        """Test audio generation step"""
        with patch.object(video_pipeline.tts_service, 'synthesize_speech') as mock_tts:
            mock_tts.return_value = {
                'success': True,
                'audio_data': base64.b64encode(b'test_audio').decode('utf-8'),
                'duration_seconds': 30,
                'sample_rate': 16000
            }
            
            result = await video_pipeline._generate_audio(video_request, 'test_video_id')
            
            assert result['success'] is True
            assert 'audio_data' in result
            assert result['duration'] == 30
    
    @pytest.mark.asyncio
    async def test_select_optimal_provider(self, video_pipeline, video_request):
        """Test optimal provider selection"""
        with patch.object(video_pipeline, '_is_provider_available', return_value=True):
            provider = await video_pipeline._select_optimal_provider(
                video_request, 'test_video_id'
            )
            
            assert provider in VideoGenerationProvider
    
    @pytest.mark.asyncio
    async def test_generate_with_veo3(self, video_pipeline, video_request):
        """Test Veo3 video generation"""
        animation_data = {
            'frames': [{'data': 'frame1'}, {'data': 'frame2'}],
            'frame_rate': 30
        }
        
        with patch('requests.post') as mock_post:
            # Mock initial job submission
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {'job_id': 'test_job_123'}
            
            with patch.object(video_pipeline, '_poll_veo3_job') as mock_poll:
                mock_poll.return_value = {
                    'success': True,
                    'video_data': b'test_video_data',
                    'format': 'mp4',
                    'provider': 'veo3',
                    'cost': 4.5
                }
                
                result = await video_pipeline._generate_with_veo3(
                    video_request, animation_data, 'test_video_id'
                )
                
                assert result['success'] is True
                assert result['provider'] == 'veo3'
                assert result['cost'] == 4.5
    
    @pytest.mark.asyncio
    async def test_generate_with_runway(self, video_pipeline, video_request):
        """Test Runway video generation"""
        animation_data = {
            'frames': [{'data': 'frame1'}],
            'frame_rate': 30
        }
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 201
            mock_post.return_value.json.return_value = {'id': 'gen_456'}
            
            with patch.object(video_pipeline, '_poll_runway_generation') as mock_poll:
                mock_poll.return_value = {
                    'success': True,
                    'video_data': b'runway_video',
                    'format': 'mp4',
                    'provider': 'runway'
                }
                
                result = await video_pipeline._generate_with_runway(
                    video_request, animation_data, 'test_video_id'
                )
                
                assert result['success'] is True
                assert result['provider'] == 'runway'
    
    @pytest.mark.asyncio
    async def test_post_process_video(self, video_pipeline, video_request):
        """Test video post-processing"""
        video_result = {
            'success': True,
            'video_data': b'raw_video_data',
            'provider': 'veo3',
            'cost': 4.5,
            'processing_time': 60
        }
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            
            with patch('tempfile.NamedTemporaryFile'):
                with patch('builtins.open', create=True) as mock_open:
                    mock_open.return_value.__enter__.return_value.read.return_value = b'optimized_video'
                    
                    result = await video_pipeline._post_process_video(
                        video_result, video_request, 'test_video_id'
                    )
                    
                    assert result['success'] is True
                    assert 'optimization' in result
                    assert result['optimization']['original_size'] > 0
    
    @pytest.mark.asyncio
    async def test_get_fallback_provider(self, video_pipeline, video_request):
        """Test fallback provider selection"""
        with patch.object(video_pipeline, '_is_provider_available', return_value=True):
            fallback = await video_pipeline._get_fallback_provider(
                VideoGenerationProvider.VEO3, video_request
            )
            
            assert fallback == VideoGenerationProvider.RUNWAY
            
            fallback2 = await video_pipeline._get_fallback_provider(
                VideoGenerationProvider.RUNWAY, video_request
            )
            
            assert fallback2 in VideoGenerationProvider
    
    def test_calculate_estimated_cost(self, video_pipeline):
        """Test cost estimation"""
        costs = video_pipeline.calculate_estimated_cost(
            duration=30,
            quality=VideoQuality.STANDARD,
            provider=VideoGenerationProvider.VEO3
        )
        
        assert 'veo3' in costs
        assert costs['veo3'] == 4.5  # 30 seconds * 0.15 per second
        assert 'total' in costs
    
    def test_estimate_processing_time(self, video_pipeline):
        """Test processing time estimation"""
        time_estimate = video_pipeline.estimate_processing_time(
            duration=30,
            quality=VideoQuality.STANDARD,
            provider=VideoGenerationProvider.VEO3
        )
        
        assert time_estimate > 0
        assert time_estimate < 600  # Should be less than 10 minutes


class TestCostOptimizationService:
    """Test Cost Optimization Service"""
    
    @pytest.fixture
    def cost_service(self):
        with patch('services.cost_optimization_service.current_app') as mock_app:
            mock_app.config.get.return_value = 'test_value'
            with patch('services.cost_optimization_service.Redis') as mock_redis:
                mock_redis.return_value.hgetall.return_value = {
                    'success_rate': '0.95',
                    'average_processing_time': '60',
                    'average_cost': '0.15',
                    'current_load': '5',
                    'error_count': '0',
                    'availability_score': '0.95',
                    'quality_score': '0.85'
                }
                return CostOptimizationService()
    
    def test_select_optimal_provider(self, cost_service):
        """Test optimal provider selection with cost optimization"""
        provider, estimate = cost_service.select_optimal_provider(
            duration=30,
            quality=VideoQuality.STANDARD,
            aspect_ratio=AspectRatio.LANDSCAPE,
            user_preferences={'cost_priority': 0.6}
        )
        
        assert provider in VideoGenerationProvider
        assert isinstance(estimate, CostEstimate)
        assert estimate.estimated_cost > 0
        assert 0 <= estimate.confidence <= 1
    
    def test_get_provider_metrics(self, cost_service):
        """Test provider metrics retrieval"""
        metrics = cost_service._get_provider_metrics(VideoGenerationProvider.VEO3)
        
        assert isinstance(metrics, ProviderMetrics)
        assert metrics.provider == VideoGenerationProvider.VEO3
        assert 0 <= metrics.success_rate <= 1
        assert metrics.average_processing_time > 0
    
    def test_calculate_cost_estimate(self, cost_service):
        """Test cost estimation with all factors"""
        metrics = ProviderMetrics(
            provider=VideoGenerationProvider.VEO3,
            success_rate=0.95,
            average_processing_time=60,
            average_cost=0.15,
            current_load=10,
            error_count=0,
            availability_score=0.95,
            quality_score=0.85
        )
        
        estimate = cost_service._calculate_cost_estimate(
            VideoGenerationProvider.VEO3,
            30,  # 30 seconds
            VideoQuality.STANDARD,
            metrics
        )
        
        assert estimate.estimated_cost > 0
        assert estimate.processing_time > 0
        assert estimate.quality_score == 0.85
    
    def test_time_based_pricing(self, cost_service):
        """Test time-based pricing multipliers"""
        # Mock different times
        with patch('services.cost_optimization_service.datetime') as mock_dt:
            # Peak hours
            mock_dt.now.return_value.hour = 14  # 2 PM
            mock_dt.now.return_value.weekday.return_value = 1  # Tuesday
            peak_mult = cost_service._get_time_multiplier()
            assert peak_mult == 1.3
            
            # Off-peak hours
            mock_dt.now.return_value.hour = 3  # 3 AM
            off_peak_mult = cost_service._get_time_multiplier()
            assert off_peak_mult == 0.8
            
            # Weekend
            mock_dt.now.return_value.weekday.return_value = 6  # Sunday
            weekend_mult = cost_service._get_time_multiplier()
            assert weekend_mult == 0.8
    
    def test_load_based_pricing(self, cost_service):
        """Test load-based pricing (surge pricing)"""
        assert cost_service._get_load_multiplier(5) == 1.0
        assert cost_service._get_load_multiplier(15) == 1.1
        assert cost_service._get_load_multiplier(25) == 1.2
        assert cost_service._get_load_multiplier(35) == 1.3
    
    def test_update_provider_metrics(self, cost_service):
        """Test provider metrics update after job completion"""
        with patch.object(cost_service.redis_client, 'hset') as mock_hset:
            cost_service.update_provider_metrics(
                provider=VideoGenerationProvider.VEO3,
                success=True,
                processing_time=45,
                actual_cost=4.0,
                quality_rating=4.5
            )
            
            mock_hset.assert_called()
            call_args = mock_hset.call_args[1]['mapping']
            assert 'success_rate' in call_args
            assert 'average_processing_time' in call_args
            assert 'quality_score' in call_args
    
    def test_get_cost_breakdown(self, cost_service):
        """Test detailed cost breakdown"""
        breakdown = cost_service.get_cost_breakdown(
            duration=30,
            quality=VideoQuality.PREMIUM,
            provider=VideoGenerationProvider.VEO3
        )
        
        assert 'base_cost' in breakdown
        assert 'quality_multiplier' in breakdown
        assert 'time_multiplier' in breakdown
        assert 'estimated_total' in breakdown
        assert breakdown['quality_multiplier'] == 1.5  # Premium multiplier
    
    def test_usage_analytics(self, cost_service):
        """Test user usage analytics"""
        with patch.object(cost_service.redis_client, 'hgetall') as mock_hgetall:
            mock_hgetall.return_value = {
                'total_videos': '50',
                'total_cost': '225.50',
                'total_duration': '1500',
                'provider_usage': json.dumps({'veo3': 30, 'runway': 20}),
                'quality_usage': json.dumps({'standard': 60, 'premium': 40}),
                'time_pattern': json.dumps({'14': 10, '15': 8, '3': 2})
            }
            
            analytics = cost_service.get_usage_analytics('test_user', 30)
            
            assert analytics['total_videos'] == 50
            assert analytics['total_cost'] == 225.50
            assert 'recommendations' in analytics
            assert len(analytics['recommendations']) > 0
            assert 'potential_savings' in analytics


class TestWebSocketService:
    """Test WebSocket Service"""
    
    @pytest.fixture
    def websocket_service(self):
        with patch('services.websocket_service.current_app') as mock_app:
            mock_app.config.get.return_value = 'test_value'
            with patch('services.websocket_service.Redis'):
                mock_socketio = Mock()
                return WebSocketService(mock_socketio)
    
    def test_authenticate_connection(self, websocket_service):
        """Test WebSocket authentication"""
        with patch('services.websocket_service.jwt.decode') as mock_decode:
            mock_decode.return_value = {'user_id': 'test_user_123'}
            
            user_id = websocket_service._authenticate_connection({'token': 'test_token'})
            assert user_id == 'test_user_123'
            
            # Test invalid auth
            user_id = websocket_service._authenticate_connection({})
            assert user_id is None
    
    def test_broadcast_progress(self, websocket_service):
        """Test progress broadcasting"""
        with patch.object(websocket_service.redis_client, 'setex') as mock_setex:
            with patch.object(websocket_service.socketio, 'emit') as mock_emit:
                websocket_service.broadcast_progress(
                    video_id='test_video',
                    percentage=50,
                    message='Processing',
                    status='processing'
                )
                
                mock_setex.assert_called_once()
                mock_emit.assert_called_once()
                
                emit_args = mock_emit.call_args[0]
                assert emit_args[0] == 'video_progress'
                assert emit_args[1]['video_id'] == 'test_video'
    
    def test_notify_video_completed(self, websocket_service):
        """Test video completion notification"""
        with patch.object(websocket_service, 'broadcast_progress') as mock_broadcast:
            with patch.object(websocket_service.socketio, 'emit') as mock_emit:
                websocket_service.notify_video_completed(
                    video_id='test_video',
                    user_id='test_user',
                    output_url='https://example.com/video.mp4',
                    metadata={'duration': 30}
                )
                
                mock_broadcast.assert_called_once()
                mock_emit.assert_called_once()
                
                broadcast_args = mock_broadcast.call_args[1]
                assert broadcast_args['percentage'] == 100
                assert broadcast_args['status'] == 'completed'
    
    def test_track_video_generation(self, websocket_service):
        """Test video generation tracking"""
        with patch.object(websocket_service.redis_client, 'setex') as mock_setex:
            with patch.object(websocket_service.redis_client, 'sadd') as mock_sadd:
                with patch.object(websocket_service, 'broadcast_progress') as mock_broadcast:
                    websocket_service.track_video_generation(
                        video_id='test_video',
                        user_id='test_user'
                    )
                    
                    mock_setex.assert_called_once()
                    mock_sadd.assert_called_once()
                    mock_broadcast.assert_called_once()
    
    def test_get_connection_stats(self, websocket_service):
        """Test connection statistics"""
        websocket_service.active_connections = {
            'user1': {'session1', 'session2'},
            'user2': {'session3'}
        }
        
        with patch.object(websocket_service.redis_client, 'scan_iter') as mock_scan:
            mock_scan.return_value = ['video_progress:1', 'video_progress:2']
            
            with patch.object(websocket_service.redis_client, 'get') as mock_get:
                mock_get.return_value = json.dumps({'status': 'processing'})
                
                stats = websocket_service.get_connection_stats()
                
                assert stats['connected_users'] == 2
                assert stats['active_sessions'] == 3
                assert stats['active_video_generations'] == 2


# Integration Tests
class TestIntegration:
    """Integration tests for the complete video generation pipeline"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_video_generation(self):
        """Test complete video generation flow"""
        with patch('services.video_generation_service.current_app'):
            with patch('services.video_generation_service.Redis'):
                pipeline = VideoGenerationPipeline()
                
                request = VideoGenerationRequest(
                    source_image='test_image.jpg',
                    audio_data=b'test_audio',
                    script_text='Hello, this is a test video.',
                    quality=VideoQuality.STANDARD,
                    aspect_ratio=AspectRatio.LANDSCAPE,
                    duration=10.0
                )
                
                # Mock all external services
                with patch.multiple(pipeline,
                    _generate_audio=AsyncMock(return_value={'success': True, 'audio_data': b'audio', 'duration': 10}),
                    _analyze_facial_landmarks=AsyncMock(return_value={'success': True, 'landmarks': Mock()}),
                    _generate_lipsync_animation=AsyncMock(return_value={'success': True, 'frames': []}),
                    _select_optimal_provider=AsyncMock(return_value=VideoGenerationProvider.VEO3),
                    _generate_with_provider=AsyncMock(return_value={'success': True, 'video_data': b'video'}),
                    _post_process_video=AsyncMock(return_value={'success': True, 'video_data': b'final_video'}),
                    _update_progress=AsyncMock()
                ):
                    result = await pipeline.generate_video_async(request, 'test_video_id')
                    
                    assert result['success'] is True
                    assert result['video_data'] == b'final_video'
    
    def test_cost_optimization_with_real_metrics(self):
        """Test cost optimization with realistic metrics"""
        with patch('services.cost_optimization_service.current_app'):
            with patch('services.cost_optimization_service.Redis') as mock_redis:
                # Setup realistic metrics
                mock_redis.return_value.hgetall.side_effect = [
                    # VEO3 metrics - good all-around
                    {
                        'success_rate': '0.95',
                        'average_processing_time': '60',
                        'average_cost': '0.15',
                        'current_load': '5',
                        'error_count': '0',
                        'availability_score': '0.95',
                        'quality_score': '0.85'
                    },
                    # Runway metrics - high quality but expensive
                    {
                        'success_rate': '0.98',
                        'average_processing_time': '90',
                        'average_cost': '0.20',
                        'current_load': '2',
                        'error_count': '0',
                        'availability_score': '0.98',
                        'quality_score': '0.92'
                    }
                ]
                
                service = CostOptimizationService()
                
                # Test with cost priority
                provider, estimate = service.select_optimal_provider(
                    duration=30,
                    quality=VideoQuality.STANDARD,
                    aspect_ratio=AspectRatio.LANDSCAPE,
                    user_preferences={'cost_priority': 0.8, 'quality_priority': 0.2}
                )
                
                # Should prefer VEO3 for cost optimization
                assert provider == VideoGenerationProvider.VEO3
                assert estimate.estimated_cost < 10  # Reasonable cost for 30 seconds