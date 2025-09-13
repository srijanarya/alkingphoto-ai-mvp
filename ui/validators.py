"""
TalkingPhoto AI MVP - Input Validation

Provides file validation and input sanitization using pure Python only.
No C++ dependencies or compiled libraries.
Enhanced with security validation.
"""

import io
from typing import Tuple, Optional
import streamlit as st
from core.security import SecurityValidator, InputSanitizer


class FileValidator:
    """File validation for uploaded content"""
    
    # Configuration constants
    MAX_SIZE = 50 * 1024 * 1024  # 50MB max file size
    ALLOWED_TYPES = ['image/jpeg', 'image/jpg', 'image/png']
    ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png']
    
    @staticmethod
    def validate_file(uploaded_file) -> Tuple[bool, str]:
        """
        Validate uploaded file for size and type
        
        Args:
            uploaded_file: Streamlit UploadedFile object
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if uploaded_file is None:
            return False, "No file uploaded"
        
        # Check file size
        if uploaded_file.size > FileValidator.MAX_SIZE:
            size_mb = uploaded_file.size / (1024 * 1024)
            return False, f"File too large: {size_mb:.1f}MB. Maximum allowed: 50MB"
        
        # Check file type by MIME type
        if uploaded_file.type not in FileValidator.ALLOWED_TYPES:
            return False, f"Invalid file type: {uploaded_file.type}. Allowed: JPEG, PNG"
        
        # Check file extension
        file_name = uploaded_file.name.lower()
        if not any(file_name.endswith(ext) for ext in FileValidator.ALLOWED_EXTENSIONS):
            return False, f"Invalid file extension. Allowed: {', '.join(FileValidator.ALLOWED_EXTENSIONS)}"
        
        # Basic file structure validation (check for minimum file size)
        if uploaded_file.size < 100:  # Less than 100 bytes is suspicious
            return False, "File appears to be corrupted or empty"
        
        return True, "File validation passed"
    
    @staticmethod
    def get_file_info(uploaded_file) -> dict:
        """
        Extract basic file information
        
        Args:
            uploaded_file: Streamlit UploadedFile object
            
        Returns:
            dict: File information
        """
        if uploaded_file is None:
            return {}
        
        size_mb = uploaded_file.size / (1024 * 1024)
        
        return {
            'name': uploaded_file.name,
            'size_bytes': uploaded_file.size,
            'size_mb': round(size_mb, 2),
            'type': uploaded_file.type,
            'extension': uploaded_file.name.split('.')[-1].lower() if '.' in uploaded_file.name else ''
        }


class TextValidator:
    """Text input validation and sanitization"""
    
    MIN_LENGTH = 10
    MAX_LENGTH = 1000
    
    @staticmethod
    def validate_text(text: str) -> Tuple[bool, str]:
        """
        Validate text input for video generation
        
        Args:
            text: Input text string
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if not text or not text.strip():
            return False, "Text cannot be empty"
        
        text = text.strip()
        
        if len(text) < TextValidator.MIN_LENGTH:
            return False, f"Text too short. Minimum {TextValidator.MIN_LENGTH} characters required"
        
        if len(text) > TextValidator.MAX_LENGTH:
            return False, f"Text too long. Maximum {TextValidator.MAX_LENGTH} characters allowed"
        
        # Check for potentially harmful content (basic XSS prevention)
        dangerous_patterns = ['<script', '<iframe', '<object', '<embed', 'javascript:', 'vbscript:']
        text_lower = text.lower()
        
        for pattern in dangerous_patterns:
            if pattern in text_lower:
                return False, "Text contains potentially harmful content"
        
        return True, "Text validation passed"
    
    @staticmethod
    def sanitize_text(text: str) -> str:
        """
        Basic text sanitization
        
        Args:
            text: Input text
            
        Returns:
            str: Sanitized text
        """
        if not text:
            return ""
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Replace multiple whitespaces with single space
        import re
        text = re.sub(r'\s+', ' ', text)
        
        # Remove basic HTML tags (if any)
        text = re.sub(r'<[^>]+>', '', text)
        
        return text
    
    @staticmethod
    def get_text_stats(text: str) -> dict:
        """
        Get text statistics
        
        Args:
            text: Input text
            
        Returns:
            dict: Text statistics
        """
        if not text:
            return {'length': 0, 'words': 0, 'sentences': 0}
        
        text = text.strip()
        words = len(text.split())
        sentences = len([s for s in text.split('.') if s.strip()])
        
        return {
            'length': len(text),
            'words': words,
            'sentences': sentences,
            'estimated_duration': f"{words * 0.6:.1f}s"  # Rough estimate: ~100 WPM
        }


class FormValidator:
    """Complete form validation for video creation"""
    
    @staticmethod
    def validate_creation_form(uploaded_file, text: str) -> Tuple[bool, str, dict]:
        """
        Validate entire video creation form
        
        Args:
            uploaded_file: Uploaded photo file
            text: Input text for video
            
        Returns:
            Tuple[bool, str, dict]: (is_valid, error_message, validation_data)
        """
        validation_data = {
            'file_info': {},
            'text_stats': {},
            'errors': []
        }
        
        # Validate file
        file_valid, file_error = FileValidator.validate_file(uploaded_file)
        if not file_valid:
            validation_data['errors'].append(f"Photo: {file_error}")
        else:
            validation_data['file_info'] = FileValidator.get_file_info(uploaded_file)
        
        # Validate text
        text_valid, text_error = TextValidator.validate_text(text)
        if not text_valid:
            validation_data['errors'].append(f"Text: {text_error}")
        else:
            validation_data['text_stats'] = TextValidator.get_text_stats(text)
        
        # Overall validation
        is_valid = file_valid and text_valid
        error_message = "; ".join(validation_data['errors']) if validation_data['errors'] else ""
        
        return is_valid, error_message, validation_data