"""
TalkingPhoto AI MVP - Improved AI Service Implementation
Enhanced with proper type hints, async patterns, and error handling
"""

import asyncio
import aiohttp
import base64
import hashlib
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Protocol, Union, AsyncIterator
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import structlog
from contextlib import asynccontextmanager
import weakref

from models.video import VideoGeneration, AIProvider, VideoStatus
from models.file import UploadedFile
from services.file_service import FileService


logger = structlog.get_logger()


class ProcessingError(Exception):
    """Base exception for AI processing errors."""
    def __init__(self, message: str, provider: Optional[str] = None, error_code: Optional[str] = None):
        super().__init__(message)
        self.provider = provider
        self.error_code = error_code


class RateLimitError(ProcessingError):
    """Exception raised when API rate limits are exceeded."""
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class ServiceUnavailableError(ProcessingError):
    """Exception raised when AI service is unavailable."""
    pass


@dataclass(frozen=True)
class ServiceMetrics:
    """Immutable service performance metrics."""
    name: str
    cost: float
    quality: float
    speed: float
    success_rate: float = 0.95
    avg_response_time: float = 0.0


@dataclass
class ProcessingResult:
    """Result of AI processing operation."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metrics: Optional[ServiceMetrics] = None
    processing_time: float = 0.0
    cost: float = 0.0


class AIServiceProtocol(Protocol):
    """Protocol defining AI service interface."""
    
    async def process_image(
        self, 
        file_content: bytes, 
        options: Dict[str, Any]
    ) -> ProcessingResult:
        """Process image with AI service."""
        ...
    
    async def generate_video(
        self, 
        video_generation: VideoGeneration
    ) -> ProcessingResult:
        """Generate video with AI service."""
        ...
    
    async def check_status(
        self, 
        job_id: str
    ) -> ProcessingResult:
        """Check processing status."""
        ...


class OptimalServiceSelector:
    """Intelligent service selection based on multiple criteria."""
    
    def __init__(self, services: Dict[str, List[ServiceMetrics]]):
        self._services = services
        self._performance_cache: Dict[str, float] = {}
        self._failure_counts: Dict[str, int] = {}
        
    def select_service(
        self, 
        service_type: str, 
        quality_preference: str = 'balanced',
        budget_limit: Optional[float] = None
    ) -> Optional[ServiceMetrics]:
        """
        Select optimal service using multi-criteria decision analysis.
        
        Args:
            service_type: Type of service needed ('image_enhancement', 'video_generation')
            quality_preference: 'economy', 'balanced', or 'premium'
            budget_limit: Maximum cost per operation
            
        Returns:
            Selected service metrics or None if no suitable service found
        """
        available_services = self._services.get(service_type, [])
        
        if not available_services:
            return None
        
        # Filter by budget if specified
        if budget_limit:
            available_services = [s for s in available_services if s.cost <= budget_limit]
        
        if not available_services:
            return None
        
        # Score services based on preference
        scored_services = []
        for service in available_services:
            score = self._calculate_service_score(service, quality_preference)
            scored_services.append((score, service))
        
        # Sort by score (higher is better) and return best
        scored_services.sort(key=lambda x: x[0], reverse=True)
        return scored_services[0][1]
    
    def _calculate_service_score(self, service: ServiceMetrics, preference: str) -> float:
        """Calculate weighted score for service selection."""
        weights = self._get_preference_weights(preference)
        
        # Normalize metrics to 0-1 scale
        normalized_quality = service.quality / 10.0
        normalized_speed = 1.0 / (service.speed / 10.0)  # Lower time is better
        normalized_cost = 1.0 / (service.cost + 0.01)    # Lower cost is better
        
        # Apply failure penalty
        failure_penalty = self._failure_counts.get(service.name, 0) * 0.1
        
        score = (
            weights['quality'] * normalized_quality +
            weights['speed'] * normalized_speed +
            weights['cost'] * normalized_cost +
            weights['reliability'] * service.success_rate
        ) - failure_penalty
        
        return max(0.0, score)
    
    def _get_preference_weights(self, preference: str) -> Dict[str, float]:
        """Get scoring weights based on user preference."""
        weight_profiles = {
            'economy': {'cost': 0.5, 'quality': 0.2, 'speed': 0.2, 'reliability': 0.1},
            'balanced': {'cost': 0.25, 'quality': 0.35, 'speed': 0.25, 'reliability': 0.15},
            'premium': {'cost': 0.1, 'quality': 0.5, 'speed': 0.25, 'reliability': 0.15}
        }
        return weight_profiles.get(preference, weight_profiles['balanced'])
    
    def record_failure(self, service_name: str) -> None:
        """Record service failure for future selection."""
        self._failure_counts[service_name] = self._failure_counts.get(service_name, 0) + 1
        
    def record_success(self, service_name: str) -> None:
        """Record service success, reducing failure count."""
        if service_name in self._failure_counts:
            self._failure_counts[service_name] = max(0, self._failure_counts[service_name] - 1)


class AsyncAIService:
    """Improved async AI service with proper error handling and performance optimization."""
    
    def __init__(self, config: Dict[str, Any]):
        self._config = config
        self._session_pool: Optional[aiohttp.ClientSession] = None
        self._file_service = FileService()
        
        # Initialize service metrics
        self._service_metrics = {
            'image_enhancement': [
                ServiceMetrics('nano_banana', 0.039, 8.5, 2.1, 0.95),
                ServiceMetrics('openai_dall_e', 0.50, 9.2, 3.4, 0.98),
                ServiceMetrics('stability_ai', 0.35, 9.0, 2.8, 0.96)
            ],
            'video_generation': [
                ServiceMetrics('veo3', 0.15, 8.0, 12.5, 0.92),
                ServiceMetrics('runway', 0.20, 8.8, 15.2, 0.94),
                ServiceMetrics('nano_banana_video', 0.08, 7.2, 8.0, 0.89)
            ]
        }
        
        self._selector = OptimalServiceSelector(self._service_metrics)
        self._active_jobs: weakref.WeakSet = weakref.WeakSet()
        
    async def __aenter__(self) -> 'AsyncAIService':
        """Async context manager entry."""
        await self._initialize_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self._cleanup_session()
    
    async def _initialize_session(self) -> None:
        """Initialize HTTP session with optimized settings."""
        timeout = aiohttp.ClientTimeout(total=300, connect=30)
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=30,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        self._session_pool = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={'User-Agent': 'TalkingPhotoAI/1.0.0'}
        )
    
    async def _cleanup_session(self) -> None:
        """Cleanup HTTP session and resources."""
        if self._session_pool:
            await self._session_pool.close()
    
    async def enhance_image_async(
        self, 
        file_id: str, 
        options: Optional[Dict[str, Any]] = None
    ) -> ProcessingResult:
        """
        Enhance image using optimal AI service with async processing.
        
        Args:
            file_id: ID of the file to enhance
            options: Enhancement options (quality_preference, budget_limit, etc.)
            
        Returns:
            ProcessingResult with enhancement data
        """
        start_time = time.time()
        options = options or {}
        
        try:
            # Get source file
            source_file = await self._get_file_async(file_id)
            if not source_file:
                return ProcessingResult(
                    success=False, 
                    error="Source file not found"
                )
            
            # Select optimal service
            service = self._selector.select_service(
                'image_enhancement',
                options.get('quality_preference', 'balanced'),
                options.get('budget_limit')
            )
            
            if not service:
                return ProcessingResult(
                    success=False,
                    error="No suitable service available"
                )
            
            # Get file content efficiently
            file_content = await self._get_file_content_async(source_file.storage_path)
            if not file_content:
                return ProcessingResult(
                    success=False,
                    error="Unable to read source file"
                )
            
            # Process with selected service
            result = await self._process_with_service(
                service, 'enhance', file_content, source_file, options
            )
            
            processing_time = time.time() - start_time
            result.processing_time = processing_time
            
            # Record performance metrics
            if result.success:
                self._selector.record_success(service.name)
            else:
                self._selector.record_failure(service.name)
            
            return result
            
        except Exception as e:
            logger.error("Image enhancement failed", file_id=file_id, error=str(e))
            return ProcessingResult(
                success=False,
                error=f"Enhancement failed: {str(e)}",
                processing_time=time.time() - start_time
            )
    
    async def generate_video_async(
        self, 
        video_generation_id: str
    ) -> ProcessingResult:
        """
        Generate video asynchronously with comprehensive error handling.
        
        Args:
            video_generation_id: ID of the video generation request
            
        Returns:
            ProcessingResult with generation data
        """
        start_time = time.time()
        
        try:
            # Get video generation record
            video_gen = await self._get_video_generation_async(video_generation_id)
            if not video_gen:
                return ProcessingResult(
                    success=False,
                    error="Video generation not found"
                )
            
            # Mark as processing
            await self._update_video_status(video_gen, VideoStatus.PROCESSING)
            
            # Select service based on provider
            service = self._get_service_for_provider(video_gen.ai_provider)
            if not service:
                return ProcessingResult(
                    success=False,
                    error=f"Provider {video_gen.ai_provider.value} not available"
                )
            
            # Process video generation
            result = await self._generate_with_provider(video_gen, service)
            
            # Update status based on result
            if result.success:
                await self._update_video_status(video_gen, VideoStatus.COMPLETED)
            else:
                await self._update_video_status(video_gen, VideoStatus.FAILED)
            
            result.processing_time = time.time() - start_time
            return result
            
        except Exception as e:
            logger.error("Video generation failed", 
                        video_generation_id=video_generation_id, error=str(e))
            return ProcessingResult(
                success=False,
                error=f"Generation failed: {str(e)}",
                processing_time=time.time() - start_time
            )
    
    async def _process_with_service(
        self,
        service: ServiceMetrics,
        operation: str,
        file_content: bytes,
        source_file: UploadedFile,
        options: Dict[str, Any]
    ) -> ProcessingResult:
        """Process with specific AI service."""
        if service.name == 'nano_banana':
            return await self._enhance_with_nano_banana(file_content, source_file, options)
        elif service.name == 'openai_dall_e':
            return await self._enhance_with_openai(file_content, source_file, options)
        elif service.name == 'stability_ai':
            return await self._enhance_with_stability_ai(file_content, source_file, options)
        else:
            return ProcessingResult(
                success=False,
                error=f"Service {service.name} not implemented"
            )
    
    async def _enhance_with_nano_banana(
        self,
        file_content: bytes,
        source_file: UploadedFile,
        options: Dict[str, Any]
    ) -> ProcessingResult:
        """Enhance image using Google Nano Banana (Gemini 2.5 Flash) async."""
        try:
            api_key = self._config.get('NANO_BANANA_API_KEY')
            if not api_key:
                raise ServiceUnavailableError("Nano Banana API key not configured")
            
            # Convert image to base64 efficiently
            image_b64 = base64.b64encode(file_content).decode('utf-8')
            
            # Prepare enhancement prompt
            enhancement_prompt = options.get('prompt', 
                "Enhance this photo for professional video creation. "
                "Improve lighting, clarity, and overall composition while maintaining natural appearance.")
            
            # API request payload
            payload = {
                "contents": [{
                    "parts": [
                        {"text": enhancement_prompt},
                        {
                            "inline_data": {
                                "mime_type": source_file.mime_type,
                                "data": image_b64
                            }
                        }
                    ]
                }],
                "generationConfig": {
                    "temperature": 0.4,
                    "maxOutputTokens": 1024
                }
            }
            
            # Make async API call
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
            headers = {
                'Content-Type': 'application/json',
                'x-goog-api-key': api_key
            }
            
            async with self._session_pool.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error("Nano Banana API error", 
                               status_code=response.status, response=error_text)
                    
                    if response.status == 429:
                        raise RateLimitError("Rate limit exceeded", retry_after=60)
                    else:
                        raise ProcessingError(f"API error: {response.status}")
                
                response_data = await response.json()
            
            # Process response and store enhanced file
            enhanced_filename = f"enhanced_{source_file.filename}"
            enhanced_hash = hashlib.sha256(file_content).hexdigest()
            
            # Store enhanced file (in real implementation, use actual enhanced content)
            storage_result = await self._store_file_async(
                file_content=file_content,  # Would be actual enhanced content
                filename=enhanced_filename,
                content_type=source_file.mime_type
            )
            
            if not storage_result['success']:
                raise ProcessingError("Failed to store enhanced file")
            
            return ProcessingResult(
                success=True,
                data={
                    'filename': enhanced_filename,
                    'file_hash': enhanced_hash,
                    'file_size': len(file_content),
                    'storage_path': storage_result['path'],
                    'storage_url': storage_result.get('url'),
                    'cdn_url': storage_result.get('cdn_url'),
                    'prompt': enhancement_prompt,
                    'width': source_file.width,
                    'height': source_file.height
                },
                cost=0.039,
                metrics=ServiceMetrics('nano_banana', 0.039, 8.5, 2.1)
            )
            
        except (RateLimitError, ServiceUnavailableError, ProcessingError):
            raise
        except Exception as e:
            logger.error("Nano Banana enhancement failed", error=str(e))
            raise ProcessingError(f"Enhancement failed: {str(e)}", provider="nano_banana")
    
    async def _enhance_with_openai(
        self,
        file_content: bytes,
        source_file: UploadedFile,
        options: Dict[str, Any]
    ) -> ProcessingResult:
        """Enhanced OpenAI DALL-E integration (placeholder)."""
        # Implementation would go here
        raise ProcessingError("OpenAI enhancement not yet implemented", provider="openai")
    
    async def _enhance_with_stability_ai(
        self,
        file_content: bytes,
        source_file: UploadedFile,
        options: Dict[str, Any]
    ) -> ProcessingResult:
        """Enhanced Stability AI integration (placeholder)."""
        # Implementation would go here
        raise ProcessingError("Stability AI enhancement not yet implemented", provider="stability_ai")
    
    # Helper methods with proper async patterns
    async def _get_file_async(self, file_id: str) -> Optional[UploadedFile]:
        """Get file record asynchronously."""
        # In real implementation, this would be an async database query
        return UploadedFile.query.get(file_id)
    
    async def _get_file_content_async(self, storage_path: str) -> Optional[bytes]:
        """Get file content efficiently with async I/O."""
        try:
            path = Path(storage_path)
            if not path.exists():
                return None
            
            # Use async file reading for large files
            import aiofiles
            async with aiofiles.open(path, 'rb') as f:
                return await f.read()
                
        except Exception as e:
            logger.error("Failed to read file", storage_path=storage_path, error=str(e))
            return None
    
    async def _store_file_async(
        self,
        file_content: bytes,
        filename: str,
        content_type: str
    ) -> Dict[str, Any]:
        """Store file asynchronously."""
        # Placeholder for async file storage
        return {
            'success': True,
            'path': f"uploads/{filename}",
            'url': f"https://storage.example.com/{filename}"
        }
    
    async def _get_video_generation_async(self, video_id: str) -> Optional[VideoGeneration]:
        """Get video generation record asynchronously."""
        # In real implementation, this would be an async database query
        return VideoGeneration.query.get(video_id)
    
    async def _update_video_status(
        self, 
        video_gen: VideoGeneration, 
        status: VideoStatus
    ) -> None:
        """Update video generation status asynchronously."""
        video_gen.status = status
        # In real implementation, this would be an async database update
    
    def _get_service_for_provider(self, provider: AIProvider) -> Optional[ServiceMetrics]:
        """Get service metrics for AI provider."""
        provider_mapping = {
            AIProvider.VEO3: 'veo3',
            AIProvider.RUNWAY: 'runway',
            AIProvider.NANO_BANANA: 'nano_banana_video'
        }
        
        service_name = provider_mapping.get(provider)
        if not service_name:
            return None
        
        # Find service in video generation services
        for service in self._service_metrics['video_generation']:
            if service.name == service_name:
                return service
        
        return None
    
    async def _generate_with_provider(
        self,
        video_gen: VideoGeneration,
        service: ServiceMetrics
    ) -> ProcessingResult:
        """Generate video with specific provider."""
        # This would contain the actual provider-specific implementation
        # For now, return a mock success result
        return ProcessingResult(
            success=True,
            data={'video_url': f"https://storage.example.com/video_{video_gen.id}.mp4"},
            cost=service.cost * video_gen.duration_seconds
        )


# Usage example with proper async context management
async def example_usage():
    """Example of how to use the improved AI service."""
    config = {
        'NANO_BANANA_API_KEY': 'your-api-key',
        'OPENAI_API_KEY': 'your-openai-key'
    }
    
    async with AsyncAIService(config) as ai_service:
        # Enhance image
        result = await ai_service.enhance_image_async(
            file_id="photo_123",
            options={
                'quality_preference': 'premium',
                'budget_limit': 1.0,
                'prompt': 'Enhance for professional headshot'
            }
        )
        
        if result.success:
            print(f"Enhancement completed in {result.processing_time:.2f}s")
            print(f"Cost: ${result.cost:.3f}")
        else:
            print(f"Enhancement failed: {result.error}")
        
        # Generate video
        video_result = await ai_service.generate_video_async("video_gen_456")
        if video_result.success:
            print(f"Video generated successfully")