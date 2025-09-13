"""
TalkingPhoto AI MVP - Header Component

Top navigation and branding component with responsive design.
"""

import streamlit as st
from typing import Optional
from core.session import SessionManager
from core.config import config


class Header:
    """Header component with navigation and branding"""
    
    @staticmethod
    def render() -> None:
        """Render the main header component"""
        ui_config = config.get_ui_config()
        
        # Main header with gradient background
        st.markdown(f"""
        <div class="main-header">
            <h1>{ui_config['app_name']}</h1>
            <p>Transform Photos Into Talking Videos</p>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_navigation() -> Optional[str]:
        """
        Render navigation tabs
        
        Returns:
            str: Selected tab name
        """
        tab_names = ["Create Video", "Pricing", "About"]
        
        # Use Streamlit's native tab functionality
        tabs = st.tabs(tab_names)
        
        # Return the active tab (simplified for now)
        return "create"  # Default tab
    
    @staticmethod
    def render_credits_display() -> None:
        """Render credits display in header area"""
        credits = SessionManager.get_credits()
        generation_count = SessionManager.get_generation_count()
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            # Credits display
            if credits > 0:
                st.markdown(f"""
                <div class="credit-display">
                    <h3>Available Credits</h3>
                    <p>{credits}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="credit-display" style="background: linear-gradient(45deg, #e53e3e, #fc8181);">
                    <h3>No Credits Left</h3>
                    <p>0</p>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            # Session stats
            st.metric("Videos Created", generation_count)
        
        with col3:
            # Session duration
            duration = SessionManager.get_session_duration()
            duration_mins = int(duration / 60)
            st.metric("Session Time", f"{duration_mins}m")
    
    @staticmethod
    def render_status_bar() -> None:
        """Render status bar with current state"""
        if SessionManager.is_processing():
            st.markdown("""
            <div style="background: #ffd93d; padding: 0.5rem 1rem; border-radius: 5px; text-align: center; margin-bottom: 1rem;">
                <strong>🎬 Processing your video...</strong>
            </div>
            """, unsafe_allow_html=True)
        
        # Show last error if exists
        last_error = SessionManager.get_last_error()
        if last_error:
            st.markdown(f"""
            <div style="background: #fed7d7; border-left: 4px solid #e53e3e; padding: 0.5rem 1rem; margin-bottom: 1rem;">
                <strong>Error:</strong> {last_error['message']}
            </div>
            """, unsafe_allow_html=True)
            
            # Clear error after showing
            if st.button("Dismiss Error", key="dismiss_error"):
                SessionManager.clear_error()
                st.rerun()
    
    @staticmethod
    def render_mobile_header() -> None:
        """Render mobile-optimized header"""
        ui_config = config.get_ui_config()
        
        # Compact mobile header
        st.markdown(f"""
        <div class="main-header" style="padding: 1rem; text-align: center;">
            <h1 style="font-size: 1.8rem; margin: 0;">{ui_config['app_name']}</h1>
            <p style="font-size: 0.9rem; margin: 0.25rem 0;">Transform Photos Into Videos</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Mobile-friendly credits display
        credits = SessionManager.get_credits()
        col1, col2 = st.columns(2)
        
        with col1:
            if credits > 0:
                st.success(f"✨ {credits} credits available")
            else:
                st.error("❌ No credits left")
        
        with col2:
            generation_count = SessionManager.get_generation_count()
            st.info(f"🎬 {generation_count} videos created")
    
    @staticmethod  
    def render_breadcrumb(current_section: str) -> None:
        """
        Render breadcrumb navigation
        
        Args:
            current_section: Current section/page name
        """
        breadcrumb_map = {
            "create": "🎬 Create Video",
            "pricing": "💰 Pricing",
            "about": "ℹ️ About"
        }
        
        current_display = breadcrumb_map.get(current_section, current_section)
        
        st.markdown(f"""
        <div style="padding: 0.5rem 0; color: #666; font-size: 0.9rem;">
            <span>Home</span> → <span style="color: #ff882e; font-weight: 600;">{current_display}</span>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_announcement_bar() -> None:
        """Render announcement/promotion bar"""
        if config.is_development():
            st.markdown("""
            <div style="background: #4299e1; color: white; padding: 0.5rem; text-align: center; margin-bottom: 1rem;">
                <strong>🚀 Development Mode</strong> - All features are currently mocked for testing
            </div>
            """, unsafe_allow_html=True)
        else:
            # Promotional messages for production
            st.markdown("""
            <div style="background: linear-gradient(45deg, #ff882e, #ed8936); color: white; padding: 0.5rem; text-align: center; margin-bottom: 1rem;">
                <strong>🎉 Limited Time Offer:</strong> Get 1 FREE video to try TalkingPhoto AI!
            </div>
            """, unsafe_allow_html=True)