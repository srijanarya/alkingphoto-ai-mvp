"""
TalkingPhoto AI MVP - Improved Streamlit Utilities
Enhanced with proper type hints, performance optimizations, and idiomatic Python patterns
"""

import streamlit as st
import asyncio
import functools
import io
import re
import hashlib
import mimetypes
from datetime import datetime, timedelta
from typing import (
    Dict, List, Optional, Tuple, Any, Union, Protocol, TypeVar, Generic,
    Callable, Iterator, AsyncIterator, NamedTuple, Final
)
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum, auto
from contextlib import contextmanager, asynccontextmanager
import logging
from concurrent.futures import ThreadPoolExecutor
import weakref
from collections import defaultdict, deque
import threading
from PIL import Image
import numpy as np
import pandas as pd

# Type definitions
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])

# Constants
MAX_CACHE_SIZE: Final[int] = 1000
DEFAULT_TIMEOUT: Final[int] = 30
SUPPORTED_IMAGE_FORMATS: Final[frozenset] = frozenset(['JPEG', 'PNG', 'WEBP', 'BMP'])

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation strictness levels."""
    STRICT = auto()
    MODERATE = auto()
    PERMISSIVE = auto()


class CachePolicy(Enum):
    """Cache policy options."""
    NO_CACHE = auto()
    MEMORY_ONLY = auto()
    PERSISTENT = auto()
    LRU = auto()


@dataclass(frozen=True)
class ValidationRule:
    """Immutable validation rule definition."""
    name: str
    validator: Callable[[Any], bool]
    error_message: str
    warning_threshold: Optional[float] = None


@dataclass(frozen=True)
class ImageMetrics:
    """Comprehensive image quality metrics."""
    width: int
    height: int
    aspect_ratio: float
    file_size: int
    format: str
    color_mode: str
    dpi: Optional[Tuple[int, int]]
    sharpness_score: float
    brightness_score: float
    contrast_score: float
    has_transparency: bool
    estimated_quality: float


@dataclass(frozen=True)
class TextMetrics:
    """Comprehensive text analysis metrics."""
    character_count: int
    word_count: int
    sentence_count: int
    paragraph_count: int
    reading_level: float
    sentiment_score: float
    estimated_duration: float
    language_confidence: float
    complexity_score: float


class ValidationResult(NamedTuple):
    """Type-safe validation result."""
    is_valid: bool
    confidence: float
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    metrics: Union[ImageMetrics, TextMetrics, Dict[str, Any]]


class CacheEntry(NamedTuple):
    """Cache entry with metadata."""
    value: Any
    timestamp: datetime
    access_count: int
    size_bytes: int


class ValidatorProtocol(Protocol):
    """Protocol for validation implementations."""
    
    def validate(self, data: Any, rules: List[ValidationRule]) -> ValidationResult:
        """Validate data against rules."""
        ...


class PerformantImageProcessor:
    """Memory-efficient image processing with streaming capabilities."""
    
    def __init__(self, max_memory_mb: int = 500):
        self._max_memory_bytes = max_memory_mb * 1024 * 1024
        self._current_memory = 0
        self._lock = threading.Lock()
    
    @contextmanager
    def memory_guard(self, estimated_size: int):
        """Context manager for memory usage tracking."""
        with self._lock:
            if self._current_memory + estimated_size > self._max_memory_bytes:
                raise MemoryError(f"Would exceed memory limit: {self._max_memory_bytes}")
            self._current_memory += estimated_size
        
        try:
            yield
        finally:
            with self._lock:
                self._current_memory = max(0, self._current_memory - estimated_size)
    
    def process_image_stream(self, image_data: bytes) -> Iterator[ImageMetrics]:
        """Process image in chunks to avoid memory issues."""
        estimated_size = len(image_data) * 3  # RGB expansion
        
        with self.memory_guard(estimated_size):
            try:
                image = Image.open(io.BytesIO(image_data))
                yield self._extract_metrics(image, len(image_data))
            finally:
                if 'image' in locals():
                    image.close()
    
    def _extract_metrics(self, image: Image.Image, file_size: int) -> ImageMetrics:
        """Extract comprehensive metrics from image."""
        width, height = image.size
        aspect_ratio = width / height
        
        # Convert to numpy for analysis (memory efficient)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Sample image for quality analysis (to save memory)
        sample_size = min(512, min(width, height))
        if width > sample_size or height > sample_size:
            sample = image.resize((sample_size, sample_size), Image.Resampling.LANCZOS)
        else:
            sample = image
        
        # Calculate quality metrics
        np_image = np.array(sample)
        sharpness = self._calculate_sharpness(np_image)
        brightness = np.mean(np_image) / 255.0
        contrast = np.std(np_image) / 255.0
        
        return ImageMetrics(
            width=width,
            height=height,
            aspect_ratio=aspect_ratio,
            file_size=file_size,
            format=image.format or 'Unknown',
            color_mode=image.mode,
            dpi=getattr(image, 'info', {}).get('dpi'),
            sharpness_score=sharpness,
            brightness_score=brightness,
            contrast_score=contrast,
            has_transparency='transparency' in getattr(image, 'info', {}),
            estimated_quality=self._estimate_overall_quality(sharpness, brightness, contrast)
        )
    
    def _calculate_sharpness(self, image_array: np.ndarray) -> float:
        """Calculate image sharpness using Laplacian variance."""
        if len(image_array.shape) == 3:
            gray = np.mean(image_array, axis=2)
        else:
            gray = image_array
        
        # Laplacian filter for edge detection
        laplacian = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]])
        
        # Apply convolution
        from scipy.ndimage import convolve
        edges = convolve(gray, laplacian)
        
        # Return variance of edges (higher = sharper)
        return min(np.var(edges) / 10000, 1.0)
    
    def _estimate_overall_quality(self, sharpness: float, brightness: float, contrast: float) -> float:
        """Estimate overall image quality score."""
        # Optimal ranges
        optimal_brightness = 0.4  # Slightly dark is often better
        optimal_contrast = 0.3
        
        # Calculate penalties for being outside optimal ranges
        brightness_penalty = abs(brightness - optimal_brightness) / optimal_brightness
        contrast_penalty = abs(contrast - optimal_contrast) / optimal_contrast
        
        # Weighted quality score
        quality = (
            sharpness * 0.4 +
            (1 - brightness_penalty) * 0.3 +
            (1 - contrast_penalty) * 0.3
        )
        
        return max(0.0, min(1.0, quality))


class LRUCache(Generic[T]):
    """Type-safe LRU cache implementation with size limits."""
    
    def __init__(self, max_size: int = 128, max_memory_mb: int = 100):
        self._max_size = max_size
        self._max_memory_bytes = max_memory_mb * 1024 * 1024
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: deque = deque()
        self._current_memory = 0
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[T]:
        """Get item from cache, updating access order."""
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            
            # Update access order
            try:
                self._access_order.remove(key)
            except ValueError:
                pass
            self._access_order.append(key)
            
            # Update access count
            updated_entry = CacheEntry(
                value=entry.value,
                timestamp=entry.timestamp,
                access_count=entry.access_count + 1,
                size_bytes=entry.size_bytes
            )
            self._cache[key] = updated_entry
            
            return entry.value
    
    def put(self, key: str, value: T, size_hint: Optional[int] = None) -> None:
        """Put item in cache with size management."""
        size_bytes = size_hint or self._estimate_size(value)
        
        with self._lock:
            # Remove if already exists
            if key in self._cache:
                self._remove_key(key)
            
            # Ensure we have space
            while (
                len(self._cache) >= self._max_size or
                self._current_memory + size_bytes > self._max_memory_bytes
            ):
                if not self._cache:
                    break
                self._evict_lru()
            
            # Add new entry
            entry = CacheEntry(
                value=value,
                timestamp=datetime.now(),
                access_count=1,
                size_bytes=size_bytes
            )
            
            self._cache[key] = entry
            self._access_order.append(key)
            self._current_memory += size_bytes
    
    def _evict_lru(self) -> None:
        """Evict least recently used item."""
        if not self._access_order:
            return
        
        lru_key = self._access_order.popleft()
        self._remove_key(lru_key)
    
    def _remove_key(self, key: str) -> None:
        """Remove key from cache and update memory tracking."""
        if key in self._cache:
            entry = self._cache.pop(key)
            self._current_memory -= entry.size_bytes
    
    def _estimate_size(self, value: Any) -> int:
        """Estimate memory size of object."""
        import sys
        return sys.getsizeof(value)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()
            self._current_memory = 0
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            return {
                'size': len(self._cache),
                'max_size': self._max_size,
                'memory_usage_mb': self._current_memory / (1024 * 1024),
                'max_memory_mb': self._max_memory_bytes / (1024 * 1024),
                'hit_rate': self._calculate_hit_rate()
            }
    
    def _calculate_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        if not self._cache:
            return 0.0
        
        total_accesses = sum(entry.access_count for entry in self._cache.values())
        return len(self._cache) / max(total_accesses, 1)


class AdvancedImageValidator:
    """Advanced image validation with machine learning-style quality assessment."""
    
    def __init__(self, level: ValidationLevel = ValidationLevel.MODERATE):
        self.level = level
        self.processor = PerformantImageProcessor()
        self._validation_rules = self._build_validation_rules()
    
    def _build_validation_rules(self) -> List[ValidationRule]:
        """Build validation rules based on strictness level."""
        base_rules = [
            ValidationRule(
                "min_resolution",
                lambda m: m.width >= 512 and m.height >= 512,
                "Image resolution too low. Minimum 512x512 pixels required."
            ),
            ValidationRule(
                "supported_format",
                lambda m: m.format in SUPPORTED_IMAGE_FORMATS,
                "Unsupported image format."
            ),
            ValidationRule(
                "aspect_ratio",
                lambda m: 0.5 <= m.aspect_ratio <= 2.0,
                "Extreme aspect ratio may cause processing issues."
            )
        ]
        
        if self.level == ValidationLevel.STRICT:
            base_rules.extend([
                ValidationRule(
                    "high_quality",
                    lambda m: m.estimated_quality >= 0.8,
                    "Image quality too low for optimal results."
                ),
                ValidationRule(
                    "adequate_sharpness",
                    lambda m: m.sharpness_score >= 0.3,
                    "Image appears blurry or out of focus."
                ),
                ValidationRule(
                    "proper_brightness",
                    lambda m: 0.2 <= m.brightness_score <= 0.8,
                    "Image brightness outside optimal range."
                )
            ])
        
        return base_rules
    
    def validate_image(self, image_data: bytes, filename: str) -> ValidationResult:
        """
        Comprehensive image validation with performance optimization.
        
        Args:
            image_data: Raw image bytes
            filename: Original filename for context
            
        Returns:
            Detailed validation result with metrics
        """
        errors = []
        warnings = []
        suggestions = []
        
        try:
            # Extract metrics efficiently
            metrics_generator = self.processor.process_image_stream(image_data)
            metrics = next(metrics_generator)
            
            # Apply validation rules
            for rule in self._validation_rules:
                try:
                    if not rule.validator(metrics):
                        if self.level == ValidationLevel.STRICT:
                            errors.append(rule.error_message)
                        else:
                            warnings.append(rule.error_message)
                    elif rule.warning_threshold and hasattr(metrics, 'estimated_quality'):
                        if metrics.estimated_quality < rule.warning_threshold:
                            warnings.append(f"Quality concern: {rule.error_message}")
                            
                except Exception as e:
                    logger.warning(f"Validation rule {rule.name} failed: {e}")
            
            # Generate suggestions
            suggestions.extend(self._generate_suggestions(metrics))
            
            is_valid = len(errors) == 0
            confidence = self._calculate_confidence(metrics, errors, warnings)
            
            return ValidationResult(
                is_valid=is_valid,
                confidence=confidence,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions,
                metrics=metrics
            )
            
        except Exception as e:
            logger.error(f"Image validation failed: {e}")
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                errors=[f"Validation error: {str(e)}"],
                warnings=[],
                suggestions=[],
                metrics=ImageMetrics(0, 0, 0.0, 0, "Unknown", "Unknown", None, 0.0, 0.0, 0.0, False, 0.0)
            )
    
    def _generate_suggestions(self, metrics: ImageMetrics) -> List[str]:
        """Generate helpful suggestions based on image analysis."""
        suggestions = []
        
        if metrics.sharpness_score < 0.2:
            suggestions.append("Consider using a sharper image or enabling image stabilization")
        
        if metrics.brightness_score < 0.2:
            suggestions.append("Image appears too dark - consider increasing brightness")
        elif metrics.brightness_score > 0.8:
            suggestions.append("Image appears too bright - consider reducing exposure")
        
        if metrics.contrast_score < 0.1:
            suggestions.append("Low contrast detected - consider adjusting contrast settings")
        
        if metrics.aspect_ratio > 1.5:
            suggestions.append("Consider cropping to a more square aspect ratio for better results")
        
        if metrics.file_size > 10 * 1024 * 1024:  # 10MB
            suggestions.append("Large file size - consider compressing image for faster processing")
        
        return suggestions
    
    def _calculate_confidence(
        self, 
        metrics: ImageMetrics, 
        errors: List[str], 
        warnings: List[str]
    ) -> float:
        """Calculate validation confidence score."""
        if errors:
            return 0.0
        
        base_confidence = metrics.estimated_quality
        warning_penalty = len(warnings) * 0.1
        
        return max(0.0, min(1.0, base_confidence - warning_penalty))


class AsyncTextAnalyzer:
    """Advanced text analysis with NLP capabilities."""
    
    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._cache = LRUCache[TextMetrics](max_size=1000)
    
    async def analyze_text_async(self, text: str) -> TextMetrics:
        """Analyze text asynchronously for performance."""
        # Check cache first
        cache_key = hashlib.md5(text.encode()).hexdigest()
        cached_result = self._cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        # Run analysis in thread pool
        loop = asyncio.get_event_loop()
        metrics = await loop.run_in_executor(
            self._executor, 
            self._analyze_text_sync, 
            text
        )
        
        # Cache result
        self._cache.put(cache_key, metrics)
        return metrics
    
    def _analyze_text_sync(self, text: str) -> TextMetrics:
        """Synchronous text analysis implementation."""
        # Basic metrics
        char_count = len(text)
        words = text.split()
        word_count = len(words)
        sentences = re.split(r'[.!?]+', text)
        sentence_count = len([s for s in sentences if s.strip()])
        paragraph_count = len([p for p in text.split('\n\n') if p.strip()])
        
        # Advanced metrics
        reading_level = self._calculate_reading_level(words, sentence_count)
        sentiment_score = self._analyze_sentiment(text)
        estimated_duration = self._estimate_reading_duration(word_count)
        language_confidence = self._detect_language_confidence(text)
        complexity_score = self._calculate_complexity(words, sentence_count)
        
        return TextMetrics(
            character_count=char_count,
            word_count=word_count,
            sentence_count=sentence_count,
            paragraph_count=paragraph_count,
            reading_level=reading_level,
            sentiment_score=sentiment_score,
            estimated_duration=estimated_duration,
            language_confidence=language_confidence,
            complexity_score=complexity_score
        )
    
    def _calculate_reading_level(self, words: List[str], sentence_count: int) -> float:
        """Calculate Flesch Reading Ease score."""
        if not words or sentence_count == 0:
            return 0.0
        
        total_syllables = sum(self._count_syllables(word) for word in words)
        avg_sentence_length = len(words) / sentence_count
        avg_syllables_per_word = total_syllables / len(words)
        
        # Flesch Reading Ease formula
        score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        return max(0.0, min(100.0, score))
    
    def _count_syllables(self, word: str) -> int:
        """Estimate syllable count for a word."""
        word = word.lower().strip()
        if not word:
            return 0
        
        vowels = "aeiouy"
        syllable_count = 0
        prev_char_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_char_was_vowel:
                syllable_count += 1
            prev_char_was_vowel = is_vowel
        
        # Handle silent 'e'
        if word.endswith('e') and syllable_count > 1:
            syllable_count -= 1
        
        return max(1, syllable_count)
    
    def _analyze_sentiment(self, text: str) -> float:
        """Simple sentiment analysis (placeholder for real implementation)."""
        # In real implementation, use a proper NLP library like spaCy or transformers
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'disappointing']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count + negative_count == 0:
            return 0.5  # Neutral
        
        return positive_count / (positive_count + negative_count)
    
    def _estimate_reading_duration(self, word_count: int) -> float:
        """Estimate reading duration in seconds."""
        # Average reading speed: 200-250 words per minute
        words_per_second = 3.5
        return word_count / words_per_second
    
    def _detect_language_confidence(self, text: str) -> float:
        """Detect if text is likely English (simplified)."""
        english_indicators = re.findall(r'[a-zA-Z]', text)
        total_chars = len([c for c in text if c.isalnum()])
        
        if total_chars == 0:
            return 0.0
        
        return len(english_indicators) / total_chars
    
    def _calculate_complexity(self, words: List[str], sentence_count: int) -> float:
        """Calculate text complexity score."""
        if not words or sentence_count == 0:
            return 0.0
        
        # Factors: average word length, sentence length, vocabulary diversity
        avg_word_length = sum(len(word) for word in words) / len(words)
        avg_sentence_length = len(words) / sentence_count
        vocab_diversity = len(set(word.lower() for word in words)) / len(words)
        
        # Normalize and combine factors
        word_complexity = min(avg_word_length / 10, 1.0)
        sentence_complexity = min(avg_sentence_length / 30, 1.0)
        vocab_complexity = 1.0 - vocab_diversity  # Lower diversity = higher complexity
        
        return (word_complexity + sentence_complexity + vocab_complexity) / 3


# Improved session management with type safety
class TypedSessionManager:
    """Type-safe session state management with cleanup and validation."""
    
    def __init__(self):
        self._session_schema: Dict[str, type] = {}
        self._cleanup_callbacks: List[Callable[[], None]] = []
        self._validators: Dict[str, Callable[[Any], bool]] = {}
    
    def register_key(
        self, 
        key: str, 
        value_type: type, 
        default: Any = None,
        validator: Optional[Callable[[Any], bool]] = None
    ) -> None:
        """Register a session key with type information."""
        self._session_schema[key] = value_type
        if validator:
            self._validators[key] = validator
        
        # Set default if key doesn't exist
        if key not in st.session_state and default is not None:
            st.session_state[key] = default
    
    def get_typed(self, key: str, default: Optional[T] = None) -> Optional[T]:
        """Get session value with type checking."""
        if key not in st.session_state:
            return default
        
        value = st.session_state[key]
        expected_type = self._session_schema.get(key)
        
        if expected_type and not isinstance(value, expected_type):
            logger.warning(f"Session key {key} has wrong type: {type(value)}, expected {expected_type}")
            return default
        
        # Run validator if available
        validator = self._validators.get(key)
        if validator and not validator(value):
            logger.warning(f"Session key {key} failed validation")
            return default
        
        return value
    
    def set_typed(self, key: str, value: Any) -> bool:
        """Set session value with type checking."""
        expected_type = self._session_schema.get(key)
        
        if expected_type and not isinstance(value, expected_type):
            logger.error(f"Cannot set {key}: wrong type {type(value)}, expected {expected_type}")
            return False
        
        # Run validator if available
        validator = self._validators.get(key)
        if validator and not validator(value):
            logger.error(f"Cannot set {key}: value failed validation")
            return False
        
        st.session_state[key] = value
        return True
    
    def cleanup_session(self) -> None:
        """Clean up session with registered callbacks."""
        for callback in self._cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Cleanup callback failed: {e}")
        
        # Clear session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
    
    def register_cleanup(self, callback: Callable[[], None]) -> None:
        """Register a cleanup callback."""
        self._cleanup_callbacks.append(callback)


# Example usage and integration
def create_optimized_components():
    """Factory function for creating optimized component instances."""
    return {
        'image_validator': AdvancedImageValidator(ValidationLevel.MODERATE),
        'text_analyzer': AsyncTextAnalyzer(),
        'session_manager': TypedSessionManager(),
        'cache': LRUCache[Any](max_size=1000, max_memory_mb=100)
    }


# Performance monitoring decorator
def monitor_performance(func: F) -> F:
    """Decorator to monitor function performance."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"{func.__name__} completed in {duration:.3f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"{func.__name__} failed after {duration:.3f}s: {e}")
            raise
    
    return wrapper


# Async monitoring decorator
def async_monitor_performance(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to monitor async function performance."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"{func.__name__} completed in {duration:.3f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"{func.__name__} failed after {duration:.3f}s: {e}")
            raise
    
    return wrapper