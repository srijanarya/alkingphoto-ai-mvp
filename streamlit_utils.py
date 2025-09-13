"""
TalkingPhoto AI MVP - Streamlit Utilities
Epic 4: User Experience & Interface Utilities
"""

import streamlit as st
import requests
import json
import time
import base64
import io
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from PIL import Image
import pandas as pd
from pathlib import Path
import hashlib
import mimetypes
import re
from dataclasses import dataclass, asdict
import logging
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of photo or text validation"""
    is_valid: bool
    confidence: float
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    metadata: Dict[str, Any]

@dataclass
class UploadProgress:
    """Track upload progress"""
    filename: str
    size: int
    uploaded: int
    progress: float
    status: str
    estimated_completion: Optional[datetime] = None

class StreamlitUtils:
    """Utility functions for Streamlit UI components"""
    
    @staticmethod
    def apply_custom_css():
        """Apply custom CSS for professional design"""
        css = """
        <style>
        /* Main app styling */
        .main {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        /* Button styling */
        .stButton > button {
            width: 100%;
            border-radius: 8px;
            border: none;
            padding: 0.5rem 1rem;
            font-weight: 500;
            transition: all 0.3s ease;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        
        /* Upload area styling */
        .upload-section {
            border: 2px dashed #cccccc;
            border-radius: 12px;
            padding: 2rem;
            text-align: center;
            background: linear-gradient(135deg, #fafafa 0%, #f0f2f6 100%);
            margin: 1rem 0;
            transition: all 0.3s ease;
        }
        
        .upload-section:hover {
            border-color: #667eea;
            background: linear-gradient(135deg, #f8f9ff 0%, #f0f2f6 100%);
        }
        
        /* Voice preview card */
        .voice-preview {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            margin: 0.5rem 0;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }
        
        /* Progress container */
        .progress-container {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin: 1rem 0;
            border: 1px solid #e0e6ed;
        }
        
        /* Status badges */
        .status-badge {
            padding: 0.4rem 0.8rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
            text-transform: uppercase;
            display: inline-block;
            margin: 0.2rem;
        }
        
        .status-processing {
            background: linear-gradient(45deg, #ffc107, #ffb300);
            color: #212529;
        }
        
        .status-completed {
            background: linear-gradient(45deg, #28a745, #20c997);
            color: white;
        }
        
        .status-error {
            background: linear-gradient(45deg, #dc3545, #e74c3c);
            color: white;
        }
        
        .status-queued {
            background: linear-gradient(45deg, #6c757d, #adb5bd);
            color: white;
        }
        
        /* Metric cards */
        .metric-card {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
            border: 1px solid #e0e6ed;
            transition: all 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.15);
        }
        
        /* Generation card */
        .generation-card {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            margin: 0.5rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        /* Alert styling */
        .custom-alert {
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            border-left: 4px solid;
        }
        
        .alert-success {
            background-color: #d4edda;
            border-color: #28a745;
            color: #155724;
        }
        
        .alert-warning {
            background-color: #fff3cd;
            border-color: #ffc107;
            color: #856404;
        }
        
        .alert-error {
            background-color: #f8d7da;
            border-color: #dc3545;
            color: #721c24;
        }
        
        .alert-info {
            background-color: #cce7ff;
            border-color: #667eea;
            color: #004085;
        }
        
        /* Sidebar styling */
        .css-1d391kg {
            background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
        }
        
        /* Hide Streamlit menu and footer */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Custom loader */
        .custom-loader {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .main {
                padding-top: 1rem;
                padding-bottom: 1rem;
            }
            
            .metric-card, .progress-container {
                padding: 1rem;
            }
            
            .upload-section {
                padding: 1.5rem;
            }
        }
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)
    
    @staticmethod
    def show_loading_spinner(message: str = "Loading..."):
        """Show a custom loading spinner"""
        return st.markdown(f"""
        <div style="text-align: center; padding: 2rem;">
            <div class="custom-loader"></div>
            <p style="margin-top: 1rem; color: #666;">{message}</p>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def create_status_badge(status: str, text: str = None) -> str:
        """Create a status badge HTML"""
        if text is None:
            text = status.replace('_', ' ').title()
        
        return f'<span class="status-badge status-{status}">{text}</span>'
    
    @staticmethod
    def create_metric_card(title: str, value: str, delta: Optional[str] = None, 
                          delta_color: str = "normal") -> str:
        """Create a custom metric card"""
        delta_html = ""
        if delta:
            delta_color_map = {"normal": "#666", "inverse": "#dc3545", "positive": "#28a745"}
            color = delta_color_map.get(delta_color, "#666")
            delta_html = f'<p style="color: {color}; font-size: 0.8rem; margin: 0.5rem 0 0 0;">{delta}</p>'
        
        return f"""
        <div class="metric-card">
            <h3 style="margin: 0; color: #333; font-size: 1.2rem;">{value}</h3>
            <p style="margin: 0.5rem 0 0 0; color: #666; font-size: 0.9rem;">{title}</p>
            {delta_html}
        </div>
        """
    
    @staticmethod
    def create_progress_bar(progress: float, status: str = "", height: int = 20) -> str:
        """Create a custom progress bar"""
        progress_percent = min(max(progress, 0), 100)
        
        color_map = {
            "processing": "#667eea",
            "completed": "#28a745",
            "error": "#dc3545",
            "queued": "#6c757d"
        }
        
        color = color_map.get(status, "#667eea")
        
        return f"""
        <div style="background-color: #f0f2f6; border-radius: {height//2}px; height: {height}px; margin: 0.5rem 0;">
            <div style="
                width: {progress_percent}%; 
                height: 100%; 
                background: linear-gradient(90deg, {color}, {color}aa);
                border-radius: {height//2}px;
                transition: width 0.3s ease;
                display: flex;
                align-items: center;
                justify-content: flex-end;
                padding-right: 8px;
                color: white;
                font-size: 0.8rem;
                font-weight: bold;
            ">
                {progress_percent:.1f}%
            </div>
        </div>
        """
    
    @staticmethod
    def show_alert(message: str, alert_type: str = "info"):
        """Show a custom alert"""
        alert_html = f'<div class="custom-alert alert-{alert_type}">{message}</div>'
        st.markdown(alert_html, unsafe_allow_html=True)
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    @staticmethod
    def format_duration(seconds: int) -> str:
        """Format duration in human readable format"""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m {seconds % 60}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
        """Truncate text to specified length"""
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix

class PhotoValidator:
    """Validate uploaded photos"""
    
    @staticmethod
    def validate_photo(image: Image.Image, filename: str) -> ValidationResult:
        """Comprehensive photo validation"""
        errors = []
        warnings = []
        suggestions = []
        metadata = {}
        
        try:
            # Basic image properties
            width, height = image.size
            metadata.update({
                'width': width,
                'height': height,
                'format': image.format,
                'mode': image.mode,
                'filename': filename
            })
            
            # Resolution validation
            if width < 512 or height < 512:
                errors.append("Image resolution too low. Minimum 512x512 pixels required.")
            elif width < 1024 or height < 1024:
                warnings.append("Low resolution image. Higher resolution recommended for better quality.")
            
            # Aspect ratio validation
            aspect_ratio = width / height
            if aspect_ratio < 0.5 or aspect_ratio > 2.0:
                warnings.append("Unusual aspect ratio. Square or portrait images work best.")
            
            # File format validation
            if image.format not in ['JPEG', 'PNG', 'WEBP']:
                errors.append(f"Unsupported format: {image.format}")
            
            # Color mode validation
            if image.mode not in ['RGB', 'RGBA']:
                warnings.append(f"Color mode {image.mode} may not be optimal. RGB recommended.")
            
            # Quality assessment (simplified)
            quality_score = PhotoValidator._assess_quality(image)
            metadata['quality_score'] = quality_score
            
            if quality_score < 0.5:
                errors.append("Image quality too low. Please use a clearer photo.")
            elif quality_score < 0.7:
                warnings.append("Image quality could be better. Consider using a higher quality photo.")
            
            # Face detection (mock - in real implementation, use face detection library)
            has_face, face_confidence = PhotoValidator._detect_face(image)
            metadata.update({
                'has_face': has_face,
                'face_confidence': face_confidence
            })
            
            if not has_face:
                errors.append("No face detected. Please upload a photo with a clear, visible face.")
            elif face_confidence < 0.8:
                warnings.append("Face detection confidence is low. Ensure face is clearly visible and well-lit.")
            
            # Suggestions
            if width > 4000 or height > 4000:
                suggestions.append("Consider resizing image for faster processing.")
            
            if quality_score > 0.9:
                suggestions.append("Excellent image quality! This should produce great results.")
            
            is_valid = len(errors) == 0
            confidence = min(quality_score, face_confidence) if has_face else 0.0
            
        except Exception as e:
            logger.error(f"Error validating photo: {str(e)}")
            errors.append(f"Validation error: {str(e)}")
            is_valid = False
            confidence = 0.0
        
        return ValidationResult(
            is_valid=is_valid,
            confidence=confidence,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            metadata=metadata
        )
    
    @staticmethod
    def _assess_quality(image: Image.Image) -> float:
        """Assess image quality (simplified implementation)"""
        try:
            # Convert to grayscale for analysis
            gray = image.convert('L')
            
            # Calculate variance (higher variance = sharper image)
            import numpy as np
            np_image = np.array(gray)
            variance = np.var(np_image)
            
            # Normalize variance to 0-1 scale (rough approximation)
            quality_score = min(variance / 10000, 1.0)
            
            return max(quality_score, 0.1)  # Minimum score of 0.1
            
        except Exception:
            return 0.5  # Default score if assessment fails
    
    @staticmethod
    def _detect_face(image: Image.Image) -> Tuple[bool, float]:
        """Detect face in image (mock implementation)"""
        # In a real implementation, this would use a face detection library
        # like OpenCV, MediaPipe, or a cloud service
        
        # For demo purposes, assume 80% of images have faces
        import random
        has_face = random.random() > 0.2
        confidence = random.uniform(0.7, 0.95) if has_face else 0.0
        
        return has_face, confidence

class TextValidator:
    """Validate and process text input"""
    
    @staticmethod
    def validate_text(text: str) -> ValidationResult:
        """Validate text input for video generation"""
        errors = []
        warnings = []
        suggestions = []
        metadata = {}
        
        # Basic properties
        char_count = len(text)
        word_count = len(text.split())
        sentence_count = len(re.findall(r'[.!?]+', text))
        
        metadata.update({
            'character_count': char_count,
            'word_count': word_count,
            'sentence_count': sentence_count
        })
        
        # Length validation
        if char_count < 10:
            errors.append("Text too short. Minimum 10 characters required.")
        elif char_count > 500:
            errors.append("Text too long. Maximum 500 characters allowed.")
        elif char_count > 400:
            warnings.append("Text is quite long. Consider shortening for better results.")
        
        # Content validation
        if not text.strip():
            errors.append("Text cannot be empty or only whitespace.")
        
        # Check for special characters that might cause issues
        if re.search(r'[^\w\s.,!?;:\'"()-]', text):
            warnings.append("Text contains special characters that might affect speech generation.")
        
        # Language detection (simplified)
        if not re.search(r'[a-zA-Z]', text):
            warnings.append("Text doesn't appear to contain English characters.")
        
        # Reading time estimation
        reading_time = word_count / 150 * 60  # Assuming 150 WPM, convert to seconds
        metadata['estimated_duration'] = reading_time
        
        if reading_time > 120:  # 2 minutes
            warnings.append("Text might result in a very long video.")
        
        # Suggestions
        if word_count < 5:
            suggestions.append("Consider adding more content for a more engaging video.")
        
        if sentence_count == 0:
            suggestions.append("Add punctuation to improve speech pacing.")
        
        is_valid = len(errors) == 0
        confidence = max(0.5, min(1.0, char_count / 100))  # Simple confidence score
        
        return ValidationResult(
            is_valid=is_valid,
            confidence=confidence,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            metadata=metadata
        )

class SessionManager:
    """Manage Streamlit session state"""
    
    @staticmethod
    def init_session_state():
        """Initialize session state with default values"""
        defaults = {
            'authenticated': False,
            'user_token': None,
            'user_info': {},
            'current_page': 'upload',
            'uploaded_photos': [],
            'generation_history': [],
            'current_generation': None,
            'websocket_connected': False,
            'voice_samples': {},
            'saved_templates': [],
            'last_activity': datetime.now(),
            'session_id': hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    @staticmethod
    def clear_session():
        """Clear all session state"""
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        SessionManager.init_session_state()
    
    @staticmethod
    def update_activity():
        """Update last activity timestamp"""
        st.session_state.last_activity = datetime.now()
    
    @staticmethod
    def is_session_expired(timeout_minutes: int = 60) -> bool:
        """Check if session has expired"""
        if 'last_activity' not in st.session_state:
            return True
        
        last_activity = st.session_state.last_activity
        timeout = timedelta(minutes=timeout_minutes)
        return datetime.now() - last_activity > timeout

class WebSocketManager:
    """Manage WebSocket connections for real-time updates"""
    
    def __init__(self, ws_url: str):
        self.ws_url = ws_url
        self.connection = None
        self.connected = False
    
    def connect(self):
        """Establish WebSocket connection"""
        try:
            # In a real implementation, establish WebSocket connection
            self.connected = True
            return True
        except Exception as e:
            logger.error(f"WebSocket connection failed: {str(e)}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Close WebSocket connection"""
        if self.connection:
            # Close connection
            self.connected = False
    
    def send_message(self, message: Dict[str, Any]):
        """Send message via WebSocket"""
        if not self.connected:
            return False
        
        try:
            # Send message
            return True
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {str(e)}")
            return False
    
    def receive_message(self) -> Optional[Dict[str, Any]]:
        """Receive message from WebSocket"""
        if not self.connected:
            return None
        
        try:
            # Receive and return message
            return None  # Placeholder
        except Exception as e:
            logger.error(f"Failed to receive WebSocket message: {str(e)}")
            return None

class CacheManager:
    """Manage caching for improved performance"""
    
    @staticmethod
    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def cache_api_response(url: str, params: Dict[str, Any] = None) -> Any:
        """Cache API responses"""
        try:
            response = requests.get(url, params=params)
            return response.json() if response.status_code == 200 else None
        except Exception:
            return None
    
    @staticmethod
    @st.cache_data(ttl=1800)  # Cache for 30 minutes
    def cache_user_data(user_id: str) -> Dict[str, Any]:
        """Cache user-specific data"""
        # Placeholder for user data caching
        return {}
    
    @staticmethod
    def clear_cache():
        """Clear all cached data"""
        st.cache_data.clear()

@contextmanager
def error_handler(operation: str = "operation"):
    """Context manager for error handling"""
    try:
        yield
    except Exception as e:
        logger.error(f"Error during {operation}: {str(e)}")
        st.error(f"An error occurred during {operation}. Please try again.")

def format_timestamp(timestamp: Union[datetime, str], format_type: str = "relative") -> str:
    """Format timestamp for display"""
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    
    if format_type == "relative":
        now = datetime.now()
        if timestamp.date() == now.date():
            return timestamp.strftime("Today at %H:%M")
        elif timestamp.date() == (now - timedelta(days=1)).date():
            return timestamp.strftime("Yesterday at %H:%M")
        else:
            return timestamp.strftime("%B %d at %H:%M")
    else:
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")

def generate_share_link(generation_id: str, base_url: str = "https://talkingphoto.ai") -> str:
    """Generate shareable link for video"""
    return f"{base_url}/share/{generation_id}"

def estimate_generation_time(text_length: int, voice_type: str, quality: str = "standard") -> int:
    """Estimate video generation time in seconds"""
    base_time = 60  # 1 minute base
    text_factor = text_length * 0.5  # 0.5 seconds per character
    
    quality_multiplier = {"standard": 1.0, "hd": 1.5, "4k": 2.5}
    premium_voices = ['sarah_professional', 'emma_energetic', 'david_authoritative', 'james_confident']
    voice_multiplier = 1.3 if voice_type in premium_voices else 1.0
    
    total_time = (base_time + text_factor) * quality_multiplier.get(quality, 1.0) * voice_multiplier
    return int(total_time)