"""
TalkingPhoto AI MVP - Improved Streamlit Components
Enhanced with proper type hints, SOLID principles, and performance optimizations
"""

import streamlit as st
import asyncio
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Protocol, TypeVar, Generic, Union
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging
from contextlib import contextmanager
import functools

from streamlit_utils_improved import (
    ValidationResult, AdvancedImageValidator, AsyncTextAnalyzer,
    TypedSessionManager, monitor_performance, LRUCache
)
from streamlit_config import config

logger = logging.getLogger(__name__)

# Type definitions
T = TypeVar('T')
ComponentResult = TypeVar('ComponentResult')


class ComponentState(Enum):
    """Component lifecycle states."""
    INITIALIZING = "initializing"
    READY = "ready"
    LOADING = "loading"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class ComponentConfig:
    """Configuration for component behavior."""
    cache_enabled: bool = True
    auto_refresh: bool = False
    validation_enabled: bool = True
    performance_monitoring: bool = True
    error_recovery: bool = True


class ComponentProtocol(Protocol):
    """Protocol defining the component interface."""
    
    def render(self) -> Any:
        """Render the component and return result."""
        ...
    
    def validate_state(self) -> bool:
        """Validate component state."""
        ...
    
    def cleanup(self) -> None:
        """Cleanup component resources."""
        ...


class BaseComponent(ABC):
    """
    Abstract base component with common functionality.
    
    Implements the Template Method pattern for consistent component lifecycle.
    """
    
    def __init__(self, component_id: str, config: Optional[ComponentConfig] = None):
        self.component_id = component_id
        self.config = config or ComponentConfig()
        self.state = ComponentState.INITIALIZING
        self._cache = LRUCache[Any](max_size=100) if config and config.cache_enabled else None
        self._session_manager = TypedSessionManager()
        self._last_render_time: Optional[datetime] = None
        self._error_count = 0
        self._setup_component()
    
    def _setup_component(self) -> None:
        """Setup component-specific session keys and validation."""
        self._register_session_keys()
        self.state = ComponentState.READY
    
    @abstractmethod
    def _register_session_keys(self) -> None:
        """Register component-specific session keys with types."""
        pass
    
    @monitor_performance
    def render(self) -> Any:
        """
        Template method for component rendering.
        
        Implements the common rendering pipeline with error handling.
        """
        try:
            if not self.validate_state():
                return self._render_error_state()
            
            self.state = ComponentState.LOADING
            
            # Check cache if enabled
            if self._cache and self.config.cache_enabled:
                cache_key = self._get_cache_key()
                cached_result = self._cache.get(cache_key)
                if cached_result and not self._should_refresh():
                    return cached_result
            
            # Pre-render hook
            self._pre_render()
            
            # Main rendering
            result = self._do_render()
            
            # Post-render hook
            self._post_render(result)
            
            # Cache result if successful
            if self._cache and result is not None:
                cache_key = self._get_cache_key()
                self._cache.put(cache_key, result)
            
            self.state = ComponentState.READY
            self._last_render_time = datetime.now()
            self._error_count = 0
            
            return result
            
        except Exception as e:
            self._handle_render_error(e)
            return self._render_error_state()
    
    @abstractmethod
    def _do_render(self) -> Any:
        """Component-specific rendering logic."""
        pass
    
    def _pre_render(self) -> None:
        """Hook called before rendering."""
        pass
    
    def _post_render(self, result: Any) -> None:
        """Hook called after successful rendering."""
        pass
    
    def _handle_render_error(self, error: Exception) -> None:
        """Handle rendering errors with recovery options."""
        self._error_count += 1
        self.state = ComponentState.ERROR
        
        logger.error(f"Component {self.component_id} render error: {error}")
        
        # Show error in UI
        st.error(f"Component error: {str(error)}")
        
        # Attempt recovery if enabled and under threshold
        if self.config.error_recovery and self._error_count < 3:
            st.warning("Attempting to recover...")
            self._attempt_recovery()
    
    def _attempt_recovery(self) -> None:
        """Attempt to recover from error state."""
        try:
            self.state = ComponentState.READY
            # Clear any problematic cached data
            if self._cache:
                self._cache.clear()
        except Exception as e:
            logger.error(f"Recovery failed for {self.component_id}: {e}")
    
    def _render_error_state(self) -> Any:
        """Render component in error state."""
        st.error(f"Component {self.component_id} is not available")
        if st.button(f"Retry {self.component_id}", key=f"retry_{self.component_id}"):
            self._attempt_recovery()
            st.rerun()
        return None
    
    def validate_state(self) -> bool:
        """Validate component can render safely."""
        return self.state in [ComponentState.READY, ComponentState.LOADING]
    
    def _get_cache_key(self) -> str:
        """Generate cache key for current component state."""
        # Default implementation - override for component-specific caching
        return f"{self.component_id}_{hash(str(st.session_state))}"
    
    def _should_refresh(self) -> bool:
        """Determine if component should refresh despite cache."""
        if not self._last_render_time:
            return True
        
        if self.config.auto_refresh:
            return datetime.now() - self._last_render_time > timedelta(seconds=30)
        
        return False
    
    def cleanup(self) -> None:
        """Cleanup component resources."""
        if self._cache:
            self._cache.clear()


class OptimizedPhotoUploadComponent(BaseComponent):
    """
    Optimized photo upload component with streaming and progressive validation.
    """
    
    def __init__(self, config: Optional[ComponentConfig] = None):
        super().__init__("photo_upload", config)
        self._validator = AdvancedImageValidator()
        self._upload_progress = {}
    
    def _register_session_keys(self) -> None:
        """Register session keys for photo upload."""
        self._session_manager.register_key('uploaded_photos', list, [])
        self._session_manager.register_key('current_upload', dict, {})
        self._session_manager.register_key('upload_errors', list, [])
    
    def _do_render(self) -> Optional[Dict[str, Any]]:
        """Render the optimized photo upload interface."""
        st.subheader("📤 Upload Your Photo")
        
        # Upload guidelines with progressive disclosure
        self._render_upload_guidelines()
        
        # Main upload interface
        uploaded_file = self._render_upload_interface()
        
        if uploaded_file:
            return self._process_upload_progressive(uploaded_file)
        
        # Show recent uploads with improved UX
        self._render_recent_uploads_optimized()
        return None
    
    def _render_upload_guidelines(self) -> None:
        """Render upload guidelines with smart expansion."""
        uploaded_photos = self._session_manager.get_typed('uploaded_photos', [])
        default_expanded = len(uploaded_photos) == 0
        
        with st.expander("📋 Upload Guidelines", expanded=default_expanded):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                **✅ Optimal Photos:**
                - Clear, well-lit face (front-facing)
                - High resolution (1024x1024+)
                - Neutral expression works best
                - Minimal background distractions
                - Good contrast and sharpness
                """)
            
            with col2:
                st.markdown("""
                **❌ Avoid:**
                - Blurry or dark images
                - Multiple faces in frame
                - Sunglasses or face coverings
                - Extreme angles or lighting
                - Very small face relative to frame
                """)
    
    def _render_upload_interface(self) -> Optional[Any]:
        """Render optimized upload interface with drag-and-drop."""
        # File uploader with enhanced UX
        uploaded_file = st.file_uploader(
            "Choose a photo file",
            type=config.ALLOWED_EXTENSIONS,
            help=f"Supported formats: {', '.join(config.ALLOWED_EXTENSIONS)} • Max size: {config.MAX_FILE_SIZE // (1024*1024)}MB",
            key="photo_uploader",
            label_visibility="collapsed"
        )
        
        # Real-time file info if file selected
        if uploaded_file:
            self._show_upload_preview(uploaded_file)
        
        return uploaded_file
    
    def _show_upload_preview(self, uploaded_file) -> None:
        """Show immediate preview with basic info."""
        col1, col2 = st.columns([3, 1])
        
        with col2:
            # Quick file stats
            st.metric("File Size", f"{uploaded_file.size / (1024*1024):.1f}MB")
            st.metric("Format", uploaded_file.type.split('/')[-1].upper())
    
    @st.fragment
    def _process_upload_progressive(self, uploaded_file) -> Optional[Dict[str, Any]]:
        """Process upload with progressive feedback and streaming validation."""
        
        # Step 1: Basic validation (immediate)
        if uploaded_file.size > config.MAX_FILE_SIZE:
            st.error(f"File too large! Maximum size is {config.MAX_FILE_SIZE // (1024*1024)}MB")
            return None
        
        # Step 2: Image loading and preview
        try:
            from PIL import Image
            image = Image.open(uploaded_file)
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.image(image, caption=f"Preview: {uploaded_file.name}", use_column_width=True)
            
            with col2:
                # Enhanced file details
                self._render_image_details(image, uploaded_file)
            
            # Step 3: Progressive validation with live feedback
            validation_container = st.container()
            with validation_container:
                with st.spinner("Analyzing image quality..."):
                    validation_result = self._validate_image_progressive(uploaded_file.getvalue(), uploaded_file.name)
                
                self._display_validation_results_enhanced(validation_result)
            
            # Step 4: Upload action if valid
            if validation_result.is_valid:
                return self._handle_upload_action(uploaded_file, image, validation_result)
            
        except Exception as e:
            st.error(f"Error processing image: {str(e)}")
            logger.error(f"Image processing error: {e}")
        
        return None
    
    def _render_image_details(self, image: Image.Image, uploaded_file) -> None:
        """Render enhanced image details panel."""
        st.write("**Image Details:**")
        
        # File info
        st.write(f"📁 **File:** {uploaded_file.name}")
        st.write(f"📏 **Dimensions:** {image.size[0]}×{image.size[1]}")
        st.write(f"🎨 **Mode:** {image.mode}")
        st.write(f"⚖️ **Size:** {uploaded_file.size / (1024*1024):.1f}MB")
        
        # Calculated properties
        aspect_ratio = image.size[0] / image.size[1]
        st.write(f"📐 **Aspect Ratio:** {aspect_ratio:.2f}:1")
        
        # Quick quality indicator
        if hasattr(image, 'info') and 'quality' in image.info:
            st.write(f"✨ **JPEG Quality:** {image.info['quality']}")
    
    def _validate_image_progressive(self, image_data: bytes, filename: str) -> ValidationResult:
        """Perform progressive image validation with caching."""
        # Use caching for expensive validation
        import hashlib
        cache_key = hashlib.md5(image_data).hexdigest()
        
        if self._cache:
            cached_result = self._cache.get(f"validation_{cache_key}")
            if cached_result:
                return cached_result
        
        # Perform validation
        result = self._validator.validate_image(image_data, filename)
        
        # Cache result
        if self._cache:
            self._cache.put(f"validation_{cache_key}", result)
        
        return result
    
    def _display_validation_results_enhanced(self, result: ValidationResult) -> None:
        """Display enhanced validation results with actionable feedback."""
        # Quality score with visual indicator
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Confidence score with color coding
            confidence_color = "green" if result.confidence > 0.8 else "orange" if result.confidence > 0.6 else "red"
            st.markdown(
                f'**Quality Score:** <span style="color: {confidence_color}; font-weight: bold; font-size: 1.2em;">'
                f'{result.confidence:.1%}</span>',
                unsafe_allow_html=True
            )
        
        with col2:
            # Quality indicator emoji
            if result.confidence > 0.8:
                st.success("🌟 Excellent")
            elif result.confidence > 0.6:
                st.warning("⚠️ Good")
            else:
                st.error("❌ Poor")
        
        # Detailed feedback sections
        if result.errors:
            st.error("**Issues Found:**")
            for error in result.errors:
                st.write(f"• {error}")
        
        if result.warnings:
            st.warning("**Recommendations:**")
            for warning in result.warnings:
                st.write(f"• {warning}")
        
        if result.suggestions:
            with st.expander("💡 Optimization Tips"):
                for suggestion in result.suggestions:
                    st.info(f"💡 {suggestion}")
    
    def _handle_upload_action(self, uploaded_file, image, validation_result) -> Dict[str, Any]:
        """Handle the actual upload with progress tracking."""
        if st.button("🚀 Upload Photo", type="primary", key="upload_button"):
            return self._execute_upload_with_progress(uploaded_file, image, validation_result)
        return None
    
    def _execute_upload_with_progress(self, uploaded_file, image, validation_result) -> Dict[str, Any]:
        """Execute upload with real-time progress feedback."""
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Simulate progressive upload steps
            steps = [
                ("Preparing upload...", 20),
                ("Uploading file...", 60),
                ("Processing image...", 80),
                ("Finalizing...", 100)
            ]
            
            for step_name, progress in steps:
                status_text.text(step_name)
                progress_bar.progress(progress)
                time.sleep(0.5)  # Simulate processing time
            
            # Create photo record with enhanced metadata
            photo_data = {
                'id': f"photo_{int(time.time())}",
                'name': uploaded_file.name,
                'uploaded_at': datetime.now(),
                'size': uploaded_file.size,
                'dimensions': image.size,
                'format': image.format,
                'validation': validation_result,
                'file_path': f"uploads/{uploaded_file.name}",
                'metadata': {
                    'confidence_score': validation_result.confidence,
                    'has_warnings': len(validation_result.warnings) > 0,
                    'processing_time': time.time()  # Would store actual processing time
                }
            }
            
            # Update session state
            uploaded_photos = self._session_manager.get_typed('uploaded_photos', [])
            uploaded_photos.append(photo_data)
            self._session_manager.set_typed('uploaded_photos', uploaded_photos)
            
            # Clear progress UI
            progress_bar.empty()
            status_text.empty()
            
            # Success feedback with next steps
            st.success("✅ Photo uploaded successfully!")
            st.balloons()
            
            # Action buttons
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🎬 Generate Video", type="primary", key="proceed_to_generate"):
                    st.session_state.current_page = 'generate'
                    st.session_state.selected_photo_id = photo_data['id']
                    st.rerun()
            
            return photo_data
            
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"Upload failed: {str(e)}")
            logger.error(f"Upload error: {e}")
            return None
    
    def _render_recent_uploads_optimized(self) -> None:
        """Render optimized recent uploads with better UX."""
        uploaded_photos = self._session_manager.get_typed('uploaded_photos', [])
        
        if not uploaded_photos:
            return
        
        st.subheader("📋 Recent Uploads")
        
        # Show uploads in a more compact, scannable format
        for photo in reversed(uploaded_photos[-5:]):  # Show last 5
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                
                with col1:
                    # Truncate long filenames nicely
                    display_name = photo['name']
                    if len(display_name) > 25:
                        display_name = display_name[:22] + "..."
                    st.write(f"**{display_name}**")
                
                with col2:
                    upload_time = photo['uploaded_at']
                    time_str = upload_time.strftime('%m/%d %H:%M')
                    st.write(f"📅 {time_str}")
                
                with col3:
                    quality_score = photo['validation'].confidence
                    if quality_score > 0.8:
                        st.success(f"Quality: {quality_score:.1%}")
                    elif quality_score > 0.6:
                        st.warning(f"Quality: {quality_score:.1%}")
                    else:
                        st.error(f"Quality: {quality_score:.1%}")
                
                with col4:
                    if st.button("Use", key=f"use_{photo['id']}", help="Use this photo for video generation"):
                        st.session_state.selected_photo_id = photo['id']
                        st.session_state.current_page = 'generate'
                        st.rerun()
                
                # Add subtle separator
                st.divider()


class AsyncTextInputComponent(BaseComponent):
    """
    Async text input component with real-time analysis and smart templates.
    """
    
    def __init__(self, config: Optional[ComponentConfig] = None):
        super().__init__("text_input", config)
        self._text_analyzer = AsyncTextAnalyzer()
        self._analysis_cache = LRUCache[Any](max_size=500)
    
    def _register_session_keys(self) -> None:
        """Register session keys for text input."""
        self._session_manager.register_key('current_text', str, "")
        self._session_manager.register_key('text_analysis', dict, {})
        self._session_manager.register_key('saved_templates', list, [])
        self._session_manager.register_key('template_categories', dict, {})
    
    def _do_render(self) -> tuple[str, Dict[str, Any]]:
        """Render async text input with real-time analysis."""
        st.subheader("✍️ Enter Your Text")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            text_input = self._render_smart_text_editor()
        
        with col2:
            self._render_template_manager()
        
        # Async text analysis
        if text_input:
            analysis_result = self._analyze_text_realtime(text_input)
            self._display_text_analysis(analysis_result)
            return text_input, analysis_result
        
        return "", {}
    
    def _render_smart_text_editor(self) -> str:
        """Render smart text editor with real-time feedback."""
        # Text area with enhanced features
        text = st.text_area(
            "Your message",
            height=150,
            max_chars=config.CHARACTER_LIMIT,
            placeholder="Enter the text you want your photo to speak...\n\nTip: Use natural speech patterns and punctuation for better results.",
            help=f"Maximum {config.CHARACTER_LIMIT} characters • Use punctuation for natural pauses",
            key="text_input_main"
        )
        
        # Real-time character counter with smart coloring
        char_count = len(text) if text else 0
        char_percentage = (char_count / config.CHARACTER_LIMIT) * 100
        
        # Dynamic color based on usage
        if char_percentage < 50:
            color, status = "green", "Good length"
        elif char_percentage < 75:
            color, status = "orange", "Getting longer"
        elif char_percentage < 90:
            color, status = "orange", "Consider shortening"
        else:
            color, status = "red", "Too long!"
        
        # Enhanced character counter with recommendations
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown(
                f'<p style="color: {color}; font-weight: bold;">Characters: {char_count}/{config.CHARACTER_LIMIT}</p>',
                unsafe_allow_html=True
            )
        with col2:
            st.caption(status)
        with col3:
            if text:
                words = len(text.split())
                st.caption(f"{words} words")
        
        # Text enhancement tools
        if text:
            self._render_text_tools(text)
        
        return text
    
    def _render_text_tools(self, text: str) -> None:
        """Render text enhancement tools."""
        st.write("**Text Tools:**")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("✨ Enhance", help="AI-powered text enhancement"):
                enhanced_text = self._enhance_text_ai(text)
                if enhanced_text != text:
                    st.session_state.text_input_main = enhanced_text
                    st.rerun()
        
        with col2:
            if st.button("⏸️ Add Pauses", help="Add natural speech pauses"):
                text_with_pauses = self._add_natural_pauses(text)
                st.session_state.text_input_main = text_with_pauses
                st.rerun()
        
        with col3:
            if st.button("🎭 Add Emotion", help="Add emotional markers"):
                self._show_emotion_selector(text)
        
        with col4:
            if st.button("🔤 Clear", help="Clear all text"):
                st.session_state.text_input_main = ""
                st.rerun()
    
    def _enhance_text_ai(self, text: str) -> str:
        """AI-powered text enhancement (placeholder)."""
        # In real implementation, use AI to enhance text for speech
        enhanced = text.strip()
        
        # Basic enhancements
        if not enhanced.endswith('.'):
            enhanced += '.'
        
        # Fix common issues
        enhanced = re.sub(r'\s+', ' ', enhanced)  # Multiple spaces
        enhanced = re.sub(r'([.!?])\s*([a-z])', r'\1 \2', enhanced)  # Spacing after punctuation
        
        return enhanced
    
    def _add_natural_pauses(self, text: str) -> str:
        """Add natural speech pauses to text."""
        # Add pauses after sentences and commas
        text = re.sub(r'([.!?])\s*', r'\1... ', text)
        text = re.sub(r',\s*', r', ... ', text)
        return text.strip()
    
    def _show_emotion_selector(self, text: str) -> None:
        """Show emotion selector for text enhancement."""
        with st.container():
            st.write("**Select emotion to add:**")
            emotions = ["excitement", "joy", "calm", "confident", "friendly", "professional"]
            
            selected_emotion = st.selectbox("Emotion", emotions, key="emotion_selector")
            
            if st.button("Apply Emotion", key="apply_emotion"):
                emotional_text = f"[{selected_emotion}] {text}"
                st.session_state.text_input_main = emotional_text
                st.rerun()
    
    def _analyze_text_realtime(self, text: str) -> Dict[str, Any]:
        """Perform real-time text analysis with caching."""
        # Use a simple cache key
        import hashlib
        cache_key = hashlib.md5(text.encode()).hexdigest()
        
        # Check cache first
        cached_analysis = self._analysis_cache.get(cache_key)
        if cached_analysis:
            return cached_analysis
        
        # For demo, use synchronous analysis
        # In real implementation, this would be async
        try:
            # Basic analysis for now
            words = text.split()
            sentences = re.split(r'[.!?]+', text)
            
            analysis = {
                'character_count': len(text),
                'word_count': len(words),
                'sentence_count': len([s for s in sentences if s.strip()]),
                'estimated_duration': len(words) / 3.5,  # words per second
                'readability_score': self._calculate_simple_readability(text),
                'emotion_detected': self._detect_simple_emotion(text),
                'suggestions': self._generate_text_suggestions(text)
            }
            
            # Cache the result
            self._analysis_cache.put(cache_key, analysis)
            return analysis
            
        except Exception as e:
            logger.error(f"Text analysis error: {e}")
            return {'error': str(e)}
    
    def _calculate_simple_readability(self, text: str) -> float:
        """Calculate simple readability score."""
        words = text.split()
        sentences = len(re.split(r'[.!?]+', text))
        
        if not words or sentences == 0:
            return 0.0
        
        avg_words_per_sentence = len(words) / sentences
        
        # Simple scoring: shorter sentences = higher readability
        if avg_words_per_sentence < 10:
            return 0.9
        elif avg_words_per_sentence < 15:
            return 0.7
        elif avg_words_per_sentence < 20:
            return 0.5
        else:
            return 0.3
    
    def _detect_simple_emotion(self, text: str) -> str:
        """Simple emotion detection."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['!', 'amazing', 'great', 'excited']):
            return 'excited'
        elif any(word in text_lower for word in ['thank', 'please', 'welcome']):
            return 'friendly'
        elif any(word in text_lower for word in ['professional', 'business', 'company']):
            return 'professional'
        else:
            return 'neutral'
    
    def _generate_text_suggestions(self, text: str) -> List[str]:
        """Generate suggestions for text improvement."""
        suggestions = []
        
        if len(text) < 20:
            suggestions.append("Consider adding more content for a more engaging video")
        
        if not re.search(r'[.!?]', text):
            suggestions.append("Add punctuation to improve speech pacing")
        
        if len(text.split()) > 100:
            suggestions.append("Consider shortening for better viewer engagement")
        
        if re.search(r'[A-Z]{3,}', text):
            suggestions.append("Avoid all-caps text for more natural speech")
        
        return suggestions
    
    def _display_text_analysis(self, analysis: Dict[str, Any]) -> None:
        """Display text analysis results."""
        if 'error' in analysis:
            st.error(f"Analysis error: {analysis['error']}")
            return
        
        # Quick stats
        with st.expander("📊 Text Analysis", expanded=False):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Characters", analysis.get('character_count', 0))
            
            with col2:
                st.metric("Words", analysis.get('word_count', 0))
            
            with col3:
                st.metric("Sentences", analysis.get('sentence_count', 0))
            
            with col4:
                duration = analysis.get('estimated_duration', 0)
                st.metric("Est. Duration", f"{duration:.1f}s")
            
            # Additional insights
            readability = analysis.get('readability_score', 0)
            emotion = analysis.get('emotion_detected', 'neutral')
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Readability:** {readability:.1%}")
            with col2:
                st.write(f"**Detected Tone:** {emotion.title()}")
            
            # Suggestions
            suggestions = analysis.get('suggestions', [])
            if suggestions:
                st.write("**Suggestions:**")
                for suggestion in suggestions:
                    st.info(f"💡 {suggestion}")
    
    def _render_template_manager(self) -> None:
        """Render smart template management."""
        st.write("**📝 Smart Templates**")
        
        # Template categories
        categories = {
            "Professional": [
                "Welcome to our presentation.",
                "Thank you for your attention.",
                "I'm excited to share this with you."
            ],
            "Personal": [
                "Hi there! Hope you're doing well.",
                "Thanks for watching!",
                "Don't forget to like and subscribe!"
            ],
            "Educational": [
                "Let's dive into today's lesson.",
                "This is an important concept to understand.",
                "I hope this explanation helps clarify things."
            ]
        }
        
        # Category selector
        selected_category = st.selectbox("Template Category", list(categories.keys()))
        
        # Show templates for selected category
        for i, template in enumerate(categories[selected_category]):
            if st.button(
                f"📝 {template[:30]}...", 
                key=f"template_{selected_category}_{i}",
                help=template
            ):
                st.session_state.text_input_main = template
                st.rerun()
        
        st.divider()
        
        # Custom template management
        self._render_custom_templates()
    
    def _render_custom_templates(self) -> None:
        """Render custom template management."""
        st.write("**💾 Your Templates**")
        
        # Save current text
        current_text = st.session_state.get('text_input_main', '')
        if current_text and len(current_text.strip()) > 10:
            if st.button("💾 Save Current", key="save_template"):
                saved_templates = self._session_manager.get_typed('saved_templates', [])
                
                # Add template with metadata
                template_entry = {
                    'text': current_text,
                    'saved_at': datetime.now(),
                    'usage_count': 0
                }
                saved_templates.append(template_entry)
                
                # Keep only last 10 templates
                if len(saved_templates) > 10:
                    saved_templates = saved_templates[-10:]
                
                self._session_manager.set_typed('saved_templates', saved_templates)
                st.success("Template saved!")
        
        # Load saved templates
        saved_templates = self._session_manager.get_typed('saved_templates', [])
        if saved_templates:
            for i, template in enumerate(reversed(saved_templates[-5:])):  # Show last 5
                preview_text = template['text'][:40] + "..." if len(template['text']) > 40 else template['text']
                
                if st.button(
                    f"📖 {preview_text}",
                    key=f"load_template_{i}",
                    help=f"Saved: {template['saved_at'].strftime('%m/%d %H:%M')}"
                ):
                    st.session_state.text_input_main = template['text']
                    # Update usage count
                    template['usage_count'] += 1
                    st.rerun()


# Factory function for creating optimized components
def create_optimized_components(config: Optional[ComponentConfig] = None) -> Dict[str, BaseComponent]:
    """Create optimized component instances."""
    component_config = config or ComponentConfig(
        cache_enabled=True,
        auto_refresh=False,
        validation_enabled=True,
        performance_monitoring=True,
        error_recovery=True
    )
    
    return {
        'photo_upload': OptimizedPhotoUploadComponent(component_config),
        'text_input': AsyncTextInputComponent(component_config),
        # Add other components here as they're implemented
    }


# Performance monitoring for components
class ComponentPerformanceMonitor:
    """Monitor component performance and health."""
    
    def __init__(self):
        self._metrics: Dict[str, List[float]] = defaultdict(list)
        self._error_counts: Dict[str, int] = defaultdict(int)
    
    def record_render_time(self, component_id: str, render_time: float) -> None:
        """Record component render time."""
        self._metrics[component_id].append(render_time)
        
        # Keep only last 100 measurements
        if len(self._metrics[component_id]) > 100:
            self._metrics[component_id] = self._metrics[component_id][-100:]
    
    def record_error(self, component_id: str) -> None:
        """Record component error."""
        self._error_counts[component_id] += 1
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance report for all components."""
        report = {}
        
        for component_id, times in self._metrics.items():
            if times:
                report[component_id] = {
                    'avg_render_time': sum(times) / len(times),
                    'max_render_time': max(times),
                    'min_render_time': min(times),
                    'total_renders': len(times),
                    'error_count': self._error_counts.get(component_id, 0),
                    'error_rate': self._error_counts.get(component_id, 0) / len(times)
                }
        
        return report