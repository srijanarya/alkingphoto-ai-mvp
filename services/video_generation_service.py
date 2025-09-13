"""
TalkingPhoto AI MVP - Video Generation Pipeline
Comprehensive video generation with Veo3, Runway, and smart routing
"""

import requests
import base64
import json
import time
import asyncio
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import cv2
import numpy as np
import io
import tempfile
import subprocess
import structlog
from flask import current_app
from celery import Celery, Task
from redis import Redis
import websocket

from models.video import VideoGeneration, VideoStatus, VideoQuality, AspectRatio, AIProvider
from models.file import UploadedFile
from services.file_service import FileService
from services.tts_service import TTSService
from services.lipsync_service import LipSyncAnimationEngine

logger = structlog.get_logger()


class VideoGenerationProvider(Enum):
    """Video generation AI providers"""
    VEO3 = 'veo3'
    RUNWAY = 'runway'
    SYNTHESIA = 'synthesia'
    D_ID = 'd-id'
    HEYGEN = 'heygen'


@dataclass
class VideoGenerationRequest:
    """Video generation request parameters"""
    source_image: str  # Path or base64
    audio_data: bytes
    script_text: str
    quality: VideoQuality
    aspect_ratio: AspectRatio
    duration: float
    background: Optional[str] = None
    animation_style: str = 'natural'
    expression_intensity: float = 1.0
    provider_preference: Optional[VideoGenerationProvider] = None


@dataclass
class ProviderCapabilities:
    """Provider capabilities and limits"""
    provider: VideoGenerationProvider
    max_duration: int  # seconds
    supported_qualities: List[VideoQuality]
    supported_aspects: List[AspectRatio]
    cost_per_second: float
    processing_speed: float  # relative speed (1.0 = baseline)
    accuracy_score: float  # lip-sync accuracy (0-100)
    availability: float  # uptime percentage


class VideoGenerationPipeline:
    """
    Advanced video generation pipeline with multi-provider support
    """
    
    # Provider capabilities database
    PROVIDER_CAPABILITIES = {
        VideoGenerationProvider.VEO3: ProviderCapabilities(
            provider=VideoGenerationProvider.VEO3,
            max_duration=60,
            supported_qualities=[VideoQuality.STANDARD, VideoQuality.PREMIUM],
            supported_aspects=[AspectRatio.LANDSCAPE, AspectRatio.PORTRAIT, AspectRatio.SQUARE],
            cost_per_second=0.15,
            processing_speed=1.0,
            accuracy_score=85.0,
            availability=0.95
        ),
        VideoGenerationProvider.RUNWAY: ProviderCapabilities(
            provider=VideoGenerationProvider.RUNWAY,
            max_duration=120,
            supported_qualities=[VideoQuality.PREMIUM],
            supported_aspects=[AspectRatio.LANDSCAPE, AspectRatio.PORTRAIT, AspectRatio.SQUARE],
            cost_per_second=0.20,
            processing_speed=0.8,
            accuracy_score=92.0,
            availability=0.98
        ),
        VideoGenerationProvider.SYNTHESIA: ProviderCapabilities(
            provider=VideoGenerationProvider.SYNTHESIA,
            max_duration=180,
            supported_qualities=[VideoQuality.STANDARD, VideoQuality.PREMIUM],
            supported_aspects=[AspectRatio.LANDSCAPE, AspectRatio.PORTRAIT],
            cost_per_second=0.25,
            processing_speed=0.6,
            accuracy_score=95.0,
            availability=0.99
        ),
        VideoGenerationProvider.D_ID: ProviderCapabilities(
            provider=VideoGenerationProvider.D_ID,
            max_duration=300,
            supported_qualities=[VideoQuality.ECONOMY, VideoQuality.STANDARD],
            supported_aspects=[AspectRatio.LANDSCAPE, AspectRatio.PORTRAIT, AspectRatio.SQUARE],
            cost_per_second=0.10,
            processing_speed=1.2,
            accuracy_score=80.0,
            availability=0.93
        ),
        VideoGenerationProvider.HEYGEN: ProviderCapabilities(
            provider=VideoGenerationProvider.HEYGEN,
            max_duration=240,
            supported_qualities=[VideoQuality.STANDARD, VideoQuality.PREMIUM],
            supported_aspects=[AspectRatio.LANDSCAPE, AspectRatio.PORTRAIT],
            cost_per_second=0.18,
            processing_speed=0.9,
            accuracy_score=88.0,
            availability=0.96
        )
    }
    
    def __init__(self):
        self.file_service = FileService()
        self.tts_service = TTSService()
        self.lipsync_engine = LipSyncAnimationEngine()
        
        # Redis for job queuing and progress tracking
        self.redis_client = Redis(
            host=current_app.config.get('REDIS_HOST', 'localhost'),
            port=current_app.config.get('REDIS_PORT', 6379),
            decode_responses=True
        )
        
        # API credentials
        self.api_credentials = {
            'veo3': {
                'api_key': current_app.config.get('VEO3_API_KEY'),
                'api_url': current_app.config.get('VEO3_API_URL', 'https://api.veo3.ai/v1')
            },
            'runway': {
                'api_key': current_app.config.get('RUNWAY_API_KEY'),
                'api_url': current_app.config.get('RUNWAY_API_URL', 'https://api.runwayml.com/v1')
            },
            'synthesia': {
                'api_key': current_app.config.get('SYNTHESIA_API_KEY'),
                'api_url': current_app.config.get('SYNTHESIA_API_URL', 'https://api.synthesia.io/v2')
            },
            'd-id': {
                'api_key': current_app.config.get('D_ID_API_KEY'),
                'api_url': current_app.config.get('D_ID_API_URL', 'https://api.d-id.com')
            },
            'heygen': {
                'api_key': current_app.config.get('HEYGEN_API_KEY'),
                'api_url': current_app.config.get('HEYGEN_API_URL', 'https://api.heygen.com/v1')
            }
        }
    
    async def generate_video_async(self, request: VideoGenerationRequest,
                                  video_generation_id: str) -> Dict[str, Any]:
        """
        Asynchronous video generation with progress tracking
        """
        try:
            # Update initial progress
            await self._update_progress(video_generation_id, 0, "Initializing video generation")
            
            # Step 1: Generate audio from text (10% progress)
            audio_result = await self._generate_audio(request, video_generation_id)
            if not audio_result['success']:
                return audio_result
            
            # Step 2: Analyze facial landmarks (20% progress)
            landmarks_result = await self._analyze_facial_landmarks(request, video_generation_id)
            if not landmarks_result['success']:
                return landmarks_result
            
            # Step 3: Generate lip-sync animation (40% progress)
            animation_result = await self._generate_lipsync_animation(
                request, audio_result['audio_data'], landmarks_result['landmarks'], video_generation_id
            )
            if not animation_result['success']:
                return animation_result
            
            # Step 4: Select optimal provider (45% progress)
            provider = await self._select_optimal_provider(request, video_generation_id)
            
            # Step 5: Generate video with selected provider (50-90% progress)
            video_result = await self._generate_with_provider(
                provider, request, animation_result, video_generation_id
            )
            
            if not video_result['success']:
                # Try fallback provider
                fallback_provider = await self._get_fallback_provider(provider, request)
                if fallback_provider:
                    await self._update_progress(video_generation_id, 60, 
                                              f"Retrying with {fallback_provider.value}")
                    video_result = await self._generate_with_provider(
                        fallback_provider, request, animation_result, video_generation_id
                    )
            
            # Step 6: Post-process and optimize (90-95% progress)
            if video_result['success']:
                final_result = await self._post_process_video(video_result, request, video_generation_id)
            else:
                final_result = video_result
            
            # Step 7: Complete (100% progress)
            await self._update_progress(video_generation_id, 100, "Video generation completed")
            
            return final_result
            
        except Exception as e:
            logger.error("Video generation failed", error=str(e), video_id=video_generation_id)
            await self._update_progress(video_generation_id, -1, f"Error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _generate_audio(self, request: VideoGenerationRequest,
                            video_generation_id: str) -> Dict[str, Any]:
        """
        Generate audio from text using TTS service
        """
        try:
            await self._update_progress(video_generation_id, 5, "Generating speech audio")
            
            # Select voice based on quality preference
            voice_id = self._select_voice_for_quality(request.quality)
            
            # Generate speech
            tts_options = {
                'speed': 1.0,
                'pitch': 0.0,
                'emotion': 'neutral',
                'quality_preference': request.quality.value
            }
            
            audio_result = self.tts_service.synthesize_speech(
                request.script_text,
                voice_id,
                tts_options
            )
            
            if audio_result['success']:
                await self._update_progress(video_generation_id, 10, "Audio generation completed")
                return {
                    'success': True,
                    'audio_data': base64.b64decode(audio_result['audio_data']),
                    'duration': audio_result['duration_seconds'],
                    'sample_rate': audio_result['sample_rate']
                }
            else:
                return {'success': False, 'error': audio_result['error']}
                
        except Exception as e:
            logger.error("Audio generation failed", error=str(e))
            return {'success': False, 'error': str(e)}
    
    async def _analyze_facial_landmarks(self, request: VideoGenerationRequest,
                                       video_generation_id: str) -> Dict[str, Any]:
        """
        Analyze facial landmarks from source image
        """
        try:
            await self._update_progress(video_generation_id, 15, "Analyzing facial features")
            
            # Extract landmarks using lipsync engine
            landmarks = self.lipsync_engine._extract_facial_landmarks(request.source_image)
            
            if landmarks:
                await self._update_progress(video_generation_id, 20, "Facial analysis completed")
                return {
                    'success': True,
                    'landmarks': landmarks,
                    'face_count': 1,
                    'confidence': landmarks.confidence
                }
            else:
                return {'success': False, 'error': 'No face detected in image'}
                
        except Exception as e:
            logger.error("Facial landmark analysis failed", error=str(e))
            return {'success': False, 'error': str(e)}
    
    async def _generate_lipsync_animation(self, request: VideoGenerationRequest,
                                         audio_data: bytes, landmarks: Any,
                                         video_generation_id: str) -> Dict[str, Any]:
        """
        Generate lip-sync animation frames
        """
        try:
            await self._update_progress(video_generation_id, 25, "Creating lip-sync animation")
            
            # Animation options
            animation_options = {
                'animation_style': request.animation_style,
                'animation_intensity': request.expression_intensity,
                'smooth_transitions': True,
                'emotion': 'neutral'
            }
            
            # Generate animation
            animation_result = self.lipsync_engine.generate_lip_sync_animation(
                request.source_image,
                audio_data,
                request.script_text,
                animation_options
            )
            
            if animation_result['success']:
                await self._update_progress(video_generation_id, 40, "Animation frames generated")
                return animation_result
            else:
                return {'success': False, 'error': animation_result['error']}
                
        except Exception as e:
            logger.error("Lip-sync animation failed", error=str(e))
            return {'success': False, 'error': str(e)}
    
    async def _select_optimal_provider(self, request: VideoGenerationRequest,
                                      video_generation_id: str) -> VideoGenerationProvider:
        """
        Select optimal provider based on requirements and availability
        """
        await self._update_progress(video_generation_id, 45, "Selecting optimal AI provider")
        
        # Filter providers by capabilities
        suitable_providers = []
        
        for provider, capabilities in self.PROVIDER_CAPABILITIES.items():
            # Check duration support
            if request.duration > capabilities.max_duration:
                continue
            
            # Check quality support
            if request.quality not in capabilities.supported_qualities:
                continue
            
            # Check aspect ratio support
            if request.aspect_ratio not in capabilities.supported_aspects:
                continue
            
            # Check API availability
            if not self._is_provider_available(provider):
                continue
            
            suitable_providers.append((provider, capabilities))
        
        if not suitable_providers:
            # Fallback to most capable provider
            return VideoGenerationProvider.VEO3
        
        # Score providers based on cost, speed, and accuracy
        if request.provider_preference:
            # Check if preferred provider is suitable
            for provider, _ in suitable_providers:
                if provider == request.provider_preference:
                    return provider
        
        # Calculate scores
        scored_providers = []
        for provider, capabilities in suitable_providers:
            # Weighted scoring
            cost_score = (1.0 - (capabilities.cost_per_second / 0.30)) * 0.3  # 30% weight
            speed_score = capabilities.processing_speed * 0.2  # 20% weight
            accuracy_score = (capabilities.accuracy_score / 100) * 0.4  # 40% weight
            availability_score = capabilities.availability * 0.1  # 10% weight
            
            total_score = cost_score + speed_score + accuracy_score + availability_score
            scored_providers.append((provider, total_score))
        
        # Sort by score and return best
        scored_providers.sort(key=lambda x: x[1], reverse=True)
        return scored_providers[0][0]
    
    async def _generate_with_provider(self, provider: VideoGenerationProvider,
                                     request: VideoGenerationRequest,
                                     animation_data: Dict[str, Any],
                                     video_generation_id: str) -> Dict[str, Any]:
        """
        Generate video with specific provider
        """
        try:
            await self._update_progress(video_generation_id, 50, 
                                      f"Generating video with {provider.value}")
            
            if provider == VideoGenerationProvider.VEO3:
                return await self._generate_with_veo3(request, animation_data, video_generation_id)
            elif provider == VideoGenerationProvider.RUNWAY:
                return await self._generate_with_runway(request, animation_data, video_generation_id)
            elif provider == VideoGenerationProvider.SYNTHESIA:
                return await self._generate_with_synthesia(request, animation_data, video_generation_id)
            elif provider == VideoGenerationProvider.D_ID:
                return await self._generate_with_d_id(request, animation_data, video_generation_id)
            elif provider == VideoGenerationProvider.HEYGEN:
                return await self._generate_with_heygen(request, animation_data, video_generation_id)
            else:
                return {'success': False, 'error': f'Provider {provider.value} not implemented'}
                
        except Exception as e:
            logger.error(f"{provider.value} generation failed", error=str(e))
            return {'success': False, 'error': str(e)}
    
    async def _generate_with_veo3(self, request: VideoGenerationRequest,
                                 animation_data: Dict[str, Any],
                                 video_generation_id: str) -> Dict[str, Any]:
        """
        Generate video using Veo3 API
        """
        try:
            credentials = self.api_credentials['veo3']
            if not credentials['api_key']:
                return {'success': False, 'error': 'Veo3 API key not configured'}
            
            # Prepare request payload
            frames_data = [frame['data'] for frame in animation_data['frames']]
            
            payload = {
                'frames': frames_data[:300],  # Limit frames for API
                'fps': animation_data['frame_rate'],
                'audio': base64.b64encode(request.audio_data).decode('utf-8'),
                'resolution': self._get_resolution_for_quality(request.quality),
                'aspect_ratio': request.aspect_ratio.value,
                'background': request.background,
                'enhancement': {
                    'stabilization': True,
                    'color_correction': True,
                    'noise_reduction': request.quality == VideoQuality.PREMIUM
                }
            }
            
            headers = {
                'Authorization': f'Bearer {credentials["api_key"]}',
                'Content-Type': 'application/json'
            }
            
            # Submit job
            await self._update_progress(video_generation_id, 55, "Submitting to Veo3")
            
            response = requests.post(
                f"{credentials['api_url']}/video/generate",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code != 200:
                return {'success': False, 'error': f'Veo3 API error: {response.status_code}'}
            
            job_data = response.json()
            job_id = job_data['job_id']
            
            # Poll for completion
            return await self._poll_veo3_job(job_id, credentials, video_generation_id)
            
        except Exception as e:
            logger.error("Veo3 generation failed", error=str(e))
            return {'success': False, 'error': str(e)}
    
    async def _generate_with_runway(self, request: VideoGenerationRequest,
                                   animation_data: Dict[str, Any],
                                   video_generation_id: str) -> Dict[str, Any]:
        """
        Generate video using Runway API
        """
        try:
            credentials = self.api_credentials['runway']
            if not credentials['api_key']:
                return {'success': False, 'error': 'Runway API key not configured'}
            
            # Runway Gen-3 API format
            payload = {
                'model': 'gen3_turbo',  # or 'gen3_alpha' for higher quality
                'input': {
                    'image': request.source_image if request.source_image.startswith('data:') 
                            else self._image_to_base64(request.source_image),
                    'audio': base64.b64encode(request.audio_data).decode('utf-8'),
                    'animation_frames': animation_data['frames'][:500]  # Runway supports more frames
                },
                'parameters': {
                    'duration': request.duration,
                    'aspect_ratio': request.aspect_ratio.value,
                    'quality': 'HD' if request.quality == VideoQuality.PREMIUM else 'SD',
                    'motion_amount': request.expression_intensity,
                    'camera_motion': 'static',
                    'style': request.animation_style
                }
            }
            
            headers = {
                'Authorization': f'Bearer {credentials["api_key"]}',
                'Content-Type': 'application/json'
            }
            
            await self._update_progress(video_generation_id, 55, "Submitting to Runway")
            
            response = requests.post(
                f"{credentials['api_url']}/generations",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code != 201:
                return {'success': False, 'error': f'Runway API error: {response.text}'}
            
            generation_data = response.json()
            generation_id = generation_data['id']
            
            # Poll for completion
            return await self._poll_runway_generation(generation_id, credentials, video_generation_id)
            
        except Exception as e:
            logger.error("Runway generation failed", error=str(e))
            return {'success': False, 'error': str(e)}
    
    async def _poll_veo3_job(self, job_id: str, credentials: Dict,
                            video_generation_id: str) -> Dict[str, Any]:
        """
        Poll Veo3 job status until completion
        """
        max_attempts = 120  # 10 minutes at 5 second intervals
        attempt = 0
        
        while attempt < max_attempts:
            await asyncio.sleep(5)
            attempt += 1
            
            # Update progress
            progress = min(55 + (attempt / max_attempts) * 35, 90)
            await self._update_progress(video_generation_id, progress, "Processing video")
            
            # Check status
            response = requests.get(
                f"{credentials['api_url']}/video/status/{job_id}",
                headers={'Authorization': f'Bearer {credentials["api_key"]}'},
                timeout=10
            )
            
            if response.status_code == 200:
                status_data = response.json()
                
                if status_data['status'] == 'completed':
                    # Download video
                    video_url = status_data['output_url']
                    video_response = requests.get(video_url, timeout=60)
                    
                    if video_response.status_code == 200:
                        return {
                            'success': True,
                            'video_data': video_response.content,
                            'format': 'mp4',
                            'provider': 'veo3',
                            'cost': status_data.get('cost', 0),
                            'processing_time': status_data.get('processing_time', 0),
                            'quality_metrics': status_data.get('quality_metrics', {})
                        }
                
                elif status_data['status'] == 'failed':
                    return {'success': False, 'error': status_data.get('error', 'Processing failed')}
        
        return {'success': False, 'error': 'Processing timeout'}
    
    async def _poll_runway_generation(self, generation_id: str, credentials: Dict,
                                     video_generation_id: str) -> Dict[str, Any]:
        """
        Poll Runway generation status
        """
        max_attempts = 180  # 15 minutes at 5 second intervals
        attempt = 0
        
        while attempt < max_attempts:
            await asyncio.sleep(5)
            attempt += 1
            
            progress = min(55 + (attempt / max_attempts) * 35, 90)
            await self._update_progress(video_generation_id, progress, "Runway processing")
            
            response = requests.get(
                f"{credentials['api_url']}/generations/{generation_id}",
                headers={'Authorization': f'Bearer {credentials["api_key"]}'},
                timeout=10
            )
            
            if response.status_code == 200:
                generation_data = response.json()
                
                if generation_data['status'] == 'succeeded':
                    # Get video URL
                    video_url = generation_data['output']['video_url']
                    video_response = requests.get(video_url, timeout=60)
                    
                    if video_response.status_code == 200:
                        return {
                            'success': True,
                            'video_data': video_response.content,
                            'format': 'mp4',
                            'provider': 'runway',
                            'cost': generation_data.get('estimated_cost', 0),
                            'processing_time': generation_data.get('processing_time_seconds', 0),
                            'quality_metrics': {
                                'resolution': generation_data.get('output', {}).get('resolution'),
                                'fps': generation_data.get('output', {}).get('fps'),
                                'duration': generation_data.get('output', {}).get('duration')
                            }
                        }
                
                elif generation_data['status'] == 'failed':
                    return {'success': False, 'error': generation_data.get('failure_reason', 'Unknown error')}
        
        return {'success': False, 'error': 'Generation timeout'}
    
    async def _generate_with_synthesia(self, request: VideoGenerationRequest,
                                      animation_data: Dict[str, Any],
                                      video_generation_id: str) -> Dict[str, Any]:
        """
        Generate video using Synthesia API
        """
        # Implementation for Synthesia
        return {'success': False, 'error': 'Synthesia integration pending'}
    
    async def _generate_with_d_id(self, request: VideoGenerationRequest,
                                 animation_data: Dict[str, Any],
                                 video_generation_id: str) -> Dict[str, Any]:
        """
        Generate video using D-ID API
        """
        # Implementation for D-ID
        return {'success': False, 'error': 'D-ID integration pending'}
    
    async def _generate_with_heygen(self, request: VideoGenerationRequest,
                                   animation_data: Dict[str, Any],
                                   video_generation_id: str) -> Dict[str, Any]:
        """
        Generate video using HeyGen API
        """
        # Implementation for HeyGen
        return {'success': False, 'error': 'HeyGen integration pending'}
    
    async def _post_process_video(self, video_result: Dict[str, Any],
                                 request: VideoGenerationRequest,
                                 video_generation_id: str) -> Dict[str, Any]:
        """
        Post-process and optimize video
        """
        try:
            await self._update_progress(video_generation_id, 92, "Optimizing video")
            
            video_data = video_result['video_data']
            
            # Save to temporary file for processing
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_input:
                temp_input.write(video_data)
                temp_input_path = temp_input.name
            
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_output:
                temp_output_path = temp_output.name
            
            # FFmpeg optimization command
            ffmpeg_cmd = [
                'ffmpeg', '-i', temp_input_path,
                '-c:v', 'libx264',  # H.264 codec
                '-preset', 'medium',  # Balance between speed and compression
                '-crf', '23' if request.quality == VideoQuality.PREMIUM else '28',  # Quality
                '-c:a', 'aac',  # Audio codec
                '-b:a', '192k' if request.quality == VideoQuality.PREMIUM else '128k',
                '-movflags', '+faststart',  # Web optimization
                '-y', temp_output_path
            ]
            
            # Run FFmpeg
            process = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            
            if process.returncode == 0:
                # Read optimized video
                with open(temp_output_path, 'rb') as f:
                    optimized_video = f.read()
                
                # Calculate metrics
                original_size = len(video_data)
                optimized_size = len(optimized_video)
                compression_ratio = (1 - optimized_size / original_size) * 100
                
                await self._update_progress(video_generation_id, 95, "Finalization")
                
                return {
                    'success': True,
                    'video_data': optimized_video,
                    'format': 'mp4',
                    'provider': video_result['provider'],
                    'cost': video_result['cost'],
                    'processing_time': video_result['processing_time'],
                    'quality_metrics': video_result.get('quality_metrics', {}),
                    'optimization': {
                        'original_size': original_size,
                        'optimized_size': optimized_size,
                        'compression_ratio': compression_ratio
                    }
                }
            else:
                # Return original if optimization fails
                logger.warning("Video optimization failed, returning original",
                             error=process.stderr)
                return video_result
                
        except Exception as e:
            logger.error("Video post-processing failed", error=str(e))
            return video_result
        finally:
            # Cleanup temp files
            try:
                import os
                if 'temp_input_path' in locals():
                    os.unlink(temp_input_path)
                if 'temp_output_path' in locals():
                    os.unlink(temp_output_path)
            except:
                pass
    
    async def _get_fallback_provider(self, failed_provider: VideoGenerationProvider,
                                    request: VideoGenerationRequest) -> Optional[VideoGenerationProvider]:
        """
        Get fallback provider when primary fails
        """
        # Fallback chain
        fallback_chain = {
            VideoGenerationProvider.VEO3: VideoGenerationProvider.RUNWAY,
            VideoGenerationProvider.RUNWAY: VideoGenerationProvider.HEYGEN,
            VideoGenerationProvider.HEYGEN: VideoGenerationProvider.D_ID,
            VideoGenerationProvider.D_ID: VideoGenerationProvider.VEO3,
            VideoGenerationProvider.SYNTHESIA: VideoGenerationProvider.VEO3
        }
        
        fallback = fallback_chain.get(failed_provider)
        
        # Check if fallback supports requirements
        if fallback and fallback in self.PROVIDER_CAPABILITIES:
            capabilities = self.PROVIDER_CAPABILITIES[fallback]
            
            if (request.duration <= capabilities.max_duration and
                request.quality in capabilities.supported_qualities and
                request.aspect_ratio in capabilities.supported_aspects and
                self._is_provider_available(fallback)):
                return fallback
        
        return None
    
    def _is_provider_available(self, provider: VideoGenerationProvider) -> bool:
        """
        Check if provider API is available
        """
        provider_key = provider.value.lower().replace('_', '-')
        if provider_key in self.api_credentials:
            return bool(self.api_credentials[provider_key].get('api_key'))
        return False
    
    def _select_voice_for_quality(self, quality: VideoQuality) -> str:
        """
        Select appropriate voice based on quality tier
        """
        if quality == VideoQuality.PREMIUM:
            return 'en-US-JennyNeural'  # Azure premium voice
        elif quality == VideoQuality.STANDARD:
            return 'en-US-GuyNeural'  # Azure standard voice
        else:
            return 'en-US-Wavenet-D'  # Google economy voice
    
    def _get_resolution_for_quality(self, quality: VideoQuality) -> str:
        """
        Get video resolution for quality tier
        """
        resolutions = {
            VideoQuality.ECONOMY: '720p',
            VideoQuality.STANDARD: '1080p',
            VideoQuality.PREMIUM: '4K'
        }
        return resolutions.get(quality, '1080p')
    
    def _image_to_base64(self, image_path: str) -> str:
        """
        Convert image file to base64
        """
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            return f"data:image/jpeg;base64,{base64.b64encode(image_data).decode('utf-8')}"
        except:
            return image_path
    
    async def _update_progress(self, video_generation_id: str, percentage: int, message: str):
        """
        Update video generation progress in Redis and notify via WebSocket
        """
        try:
            # Update Redis
            progress_key = f"video_progress:{video_generation_id}"
            progress_data = {
                'percentage': percentage,
                'message': message,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            self.redis_client.setex(
                progress_key,
                3600,  # 1 hour TTL
                json.dumps(progress_data)
            )
            
            # Notify via WebSocket (if connected)
            await self._notify_websocket(video_generation_id, progress_data)
            
        except Exception as e:
            logger.error("Progress update failed", error=str(e))
    
    async def _notify_websocket(self, video_generation_id: str, progress_data: Dict[str, Any]):
        """
        Send progress update via WebSocket
        """
        try:
            # WebSocket notification implementation
            # This would connect to your WebSocket server
            pass
        except:
            pass
    
    def get_progress(self, video_generation_id: str) -> Dict[str, Any]:
        """
        Get current progress for video generation
        """
        try:
            progress_key = f"video_progress:{video_generation_id}"
            progress_data = self.redis_client.get(progress_key)
            
            if progress_data:
                return json.loads(progress_data)
            else:
                return {'percentage': 0, 'message': 'Not started', 'timestamp': None}
                
        except Exception as e:
            logger.error("Failed to get progress", error=str(e))
            return {'percentage': 0, 'message': 'Error', 'timestamp': None}
    
    def calculate_estimated_cost(self, duration: float, quality: VideoQuality,
                                provider: VideoGenerationProvider = None) -> Dict[str, float]:
        """
        Calculate estimated cost for video generation
        """
        costs = {}
        
        if provider:
            # Calculate for specific provider
            if provider in self.PROVIDER_CAPABILITIES:
                capabilities = self.PROVIDER_CAPABILITIES[provider]
                base_cost = capabilities.cost_per_second * duration
                
                # Quality multiplier
                quality_multipliers = {
                    VideoQuality.ECONOMY: 0.8,
                    VideoQuality.STANDARD: 1.0,
                    VideoQuality.PREMIUM: 1.5
                }
                
                total_cost = base_cost * quality_multipliers.get(quality, 1.0)
                costs[provider.value] = round(total_cost, 2)
        else:
            # Calculate for all providers
            for provider, capabilities in self.PROVIDER_CAPABILITIES.items():
                if quality in capabilities.supported_qualities:
                    base_cost = capabilities.cost_per_second * duration
                    
                    quality_multipliers = {
                        VideoQuality.ECONOMY: 0.8,
                        VideoQuality.STANDARD: 1.0,
                        VideoQuality.PREMIUM: 1.5
                    }
                    
                    total_cost = base_cost * quality_multipliers.get(quality, 1.0)
                    costs[provider.value] = round(total_cost, 2)
        
        # Add TTS cost (approximately)
        tts_cost = len(str(duration * 150)) * 0.000016  # Rough estimate
        costs['tts'] = round(tts_cost, 4)
        
        # Total
        costs['total'] = round(sum(costs.values()) / len(costs) if costs else 0, 2)
        
        return costs
    
    def estimate_processing_time(self, duration: float, quality: VideoQuality,
                                provider: VideoGenerationProvider = None) -> int:
        """
        Estimate processing time in seconds
        """
        if provider and provider in self.PROVIDER_CAPABILITIES:
            capabilities = self.PROVIDER_CAPABILITIES[provider]
            base_time = duration * 10  # Base: 10 seconds processing per second of video
            
            # Adjust for provider speed
            adjusted_time = base_time / capabilities.processing_speed
            
            # Quality adjustment
            if quality == VideoQuality.PREMIUM:
                adjusted_time *= 1.5
            elif quality == VideoQuality.ECONOMY:
                adjusted_time *= 0.8
            
            return int(adjusted_time)
        else:
            # Average estimate
            return int(duration * 12)