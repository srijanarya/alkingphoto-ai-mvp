"""
TalkingPhoto AI MVP - Session Management

Manages Streamlit session state for user interactions and application state.
Pure Python implementation with no external dependencies.
"""

import streamlit as st
from typing import Dict, Any, Optional
import time


class SessionManager:
    """Manages Streamlit session state and user session data"""
    
    # Default session values
    DEFAULT_CREDITS = 1
    DEFAULT_USER_ID = "guest"
    
    @staticmethod
    def init_session() -> None:
        """Initialize session state with default values"""
        
        # User credits system
        if 'credits' not in st.session_state:
            st.session_state.credits = SessionManager.DEFAULT_CREDITS
        
        # User identification (for analytics)
        if 'user_id' not in st.session_state:
            st.session_state.user_id = SessionManager.DEFAULT_USER_ID
        
        # Session timestamp
        if 'session_start' not in st.session_state:
            st.session_state.session_start = time.time()
        
        # Generation history (for this session)
        if 'generation_history' not in st.session_state:
            st.session_state.generation_history = []
        
        # UI state
        if 'current_tab' not in st.session_state:
            st.session_state.current_tab = "create"
        
        # Processing state
        if 'is_processing' not in st.session_state:
            st.session_state.is_processing = False
        
        # Error tracking
        if 'last_error' not in st.session_state:
            st.session_state.last_error = None
    
    @staticmethod
    def get_credits() -> int:
        """Get current user credits"""
        return st.session_state.get('credits', 0)
    
    @staticmethod
    def has_credits() -> bool:
        """Check if user has available credits"""
        return SessionManager.get_credits() > 0
    
    @staticmethod
    def use_credit() -> bool:
        """
        Attempt to use a credit
        
        Returns:
            bool: True if credit was successfully used, False if no credits available
        """
        if SessionManager.has_credits():
            st.session_state.credits -= 1
            return True
        return False
    
    @staticmethod
    def add_credits(count: int) -> None:
        """
        Add credits to user account
        
        Args:
            count: Number of credits to add
        """
        current_credits = st.session_state.get('credits', 0)
        st.session_state.credits = current_credits + count
    
    @staticmethod
    def reset_credits() -> None:
        """Reset credits to default value"""
        st.session_state.credits = SessionManager.DEFAULT_CREDITS
    
    @staticmethod
    def start_processing() -> None:
        """Mark session as currently processing"""
        st.session_state.is_processing = True
    
    @staticmethod
    def stop_processing() -> None:
        """Mark session as not processing"""
        st.session_state.is_processing = False
    
    @staticmethod
    def is_processing() -> bool:
        """Check if session is currently processing"""
        return st.session_state.get('is_processing', False)
    
    @staticmethod
    def add_generation(file_info: Dict[str, Any], text_stats: Dict[str, Any]) -> None:
        """
        Add a generation to session history
        
        Args:
            file_info: Information about the uploaded file
            text_stats: Statistics about the input text
        """
        generation = {
            'timestamp': time.time(),
            'file_info': file_info,
            'text_stats': text_stats,
            'credits_used': 1
        }
        
        if 'generation_history' not in st.session_state:
            st.session_state.generation_history = []
        
        st.session_state.generation_history.append(generation)
        
        # Keep only last 10 generations to manage memory
        if len(st.session_state.generation_history) > 10:
            st.session_state.generation_history = st.session_state.generation_history[-10:]
    
    @staticmethod
    def get_generation_count() -> int:
        """Get total number of generations in this session"""
        return len(st.session_state.get('generation_history', []))
    
    @staticmethod
    def get_session_duration() -> float:
        """Get session duration in seconds"""
        start_time = st.session_state.get('session_start', time.time())
        return time.time() - start_time
    
    @staticmethod
    def set_error(error_message: str) -> None:
        """
        Set last error message
        
        Args:
            error_message: Error message to store
        """
        st.session_state.last_error = {
            'message': error_message,
            'timestamp': time.time()
        }
    
    @staticmethod
    def get_last_error() -> Optional[Dict[str, Any]]:
        """Get last error information"""
        return st.session_state.get('last_error')
    
    @staticmethod
    def clear_error() -> None:
        """Clear the last error"""
        st.session_state.last_error = None
    
    @staticmethod
    def get_session_stats() -> Dict[str, Any]:
        """
        Get comprehensive session statistics
        
        Returns:
            Dict: Session statistics
        """
        return {
            'credits': SessionManager.get_credits(),
            'generations': SessionManager.get_generation_count(),
            'duration_seconds': SessionManager.get_session_duration(),
            'is_processing': SessionManager.is_processing(),
            'has_error': SessionManager.get_last_error() is not None,
            'session_start': st.session_state.get('session_start'),
            'user_id': st.session_state.get('user_id', 'guest')
        }
    
    @staticmethod
    def reset_session() -> None:
        """Reset session to initial state (useful for testing)"""
        # Clear all relevant session state
        for key in ['credits', 'generation_history', 'is_processing', 'last_error']:
            if key in st.session_state:
                del st.session_state[key]
        
        # Re-initialize
        SessionManager.init_session()