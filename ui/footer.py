"""
TalkingPhoto AI MVP - Footer Component

Bottom section with links, information, and branding.
"""

import streamlit as st
from typing import Dict, List
from core.config import config
import time


class Footer:
    """Footer component with links and information"""
    
    @staticmethod
    def render() -> None:
        """Render the main footer component"""
        Footer.render_main_footer()
    
    @staticmethod
    def render_main_footer() -> None:
        """Render main footer with links and information"""
        
        # Footer separator
        st.markdown("""
        <hr style="margin: 3rem 0 2rem 0; border: none; height: 1px; background: #e2e8f0;">
        """, unsafe_allow_html=True)
        
        # Main footer content
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            Footer._render_product_links()
        
        with col2:
            Footer._render_company_links()
        
        with col3:
            Footer._render_support_links()
        
        with col4:
            Footer._render_legal_links()
        
        # Footer bottom
        Footer.render_footer_bottom()
    
    @staticmethod
    def _render_product_links() -> None:
        """Render product-related links"""
        st.markdown("""
        **Product**
        
        🎬 Create Videos  
        💰 Pricing  
        ✨ Features  
        📱 Mobile App (Soon)  
        🔧 API Access (Soon)
        """)
    
    @staticmethod
    def _render_company_links() -> None:
        """Render company information links"""
        st.markdown("""
        **Company**
        
        ℹ️ About Us  
        📝 Blog  
        💼 Careers  
        📰 Press Kit  
        🤝 Partnerships
        """)
    
    @staticmethod
    def _render_support_links() -> None:
        """Render support and help links"""
        st.markdown("""
        **Support**
        
        📚 Help Center  
        💬 Live Chat  
        📧 Contact Us  
        🎥 Tutorials  
        ❓ FAQs
        """)
    
    @staticmethod
    def _render_legal_links() -> None:
        """Render legal and policy links"""
        st.markdown("""
        **Legal**
        
        📋 Terms of Service  
        🔒 Privacy Policy  
        🍪 Cookie Policy  
        ⚖️ Refund Policy  
        🛡️ Security
        """)
    
    @staticmethod
    def render_footer_bottom() -> None:
        """Render footer bottom with copyright and social links"""
        ui_config = config.get_ui_config()
        current_year = time.strftime("%Y")
        
        st.markdown(f"""
        <div class="footer">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
                <div>
                    <p style="margin: 0;">© {current_year} {ui_config['app_name']}. All rights reserved.</p>
                    <p style="margin: 0.25rem 0 0 0; font-size: 0.8rem; opacity: 0.8;">
                        Made in India 🇮🇳 with ❤️ for creators worldwide
                    </p>
                </div>
                <div>
                    {Footer._get_social_links_html()}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def _get_social_links_html() -> str:
        """Get social media links HTML"""
        return """
        <div style="display: flex; gap: 1rem; align-items: center;">
            <span style="font-size: 0.9rem; opacity: 0.8;">Follow us:</span>
            <a href="#" style="text-decoration: none; font-size: 1.2rem;">🐦</a>
            <a href="#" style="text-decoration: none; font-size: 1.2rem;">📘</a>
            <a href="#" style="text-decoration: none; font-size: 1.2rem;">📸</a>
            <a href="#" style="text-decoration: none; font-size: 1.2rem;">🎥</a>
        </div>
        """
    
    @staticmethod
    def render_minimal_footer() -> None:
        """Render minimal footer for mobile or compact views"""
        ui_config = config.get_ui_config()
        current_year = time.strftime("%Y")
        
        st.markdown(f"""
        <div class="footer" style="text-align: center; padding: 1.5rem 1rem;">
            <p style="margin: 0; font-size: 0.9rem;">© {current_year} {ui_config['app_name']}</p>
            <p style="margin: 0.5rem 0 0 0; font-size: 0.8rem; opacity: 0.7;">
                <a href="#" style="color: #ff882e; text-decoration: none;">Terms</a> • 
                <a href="#" style="color: #ff882e; text-decoration: none;">Privacy</a> • 
                <a href="#" style="color: #ff882e; text-decoration: none;">Contact</a>
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_status_footer() -> None:
        """Render footer with system status information"""
        if config.is_development():
            debug_info = config.get_debug_info()
            
            with st.expander("🔧 Debug Information", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.json({
                        "Environment": debug_info["environment"],
                        "Debug Mode": debug_info["debug_mode"],
                        "App Version": config.get("app_version", "2.0")
                    })
                
                with col2:
                    st.json({
                        "Features Enabled": debug_info["features_enabled"],
                        "Config Keys": len(debug_info["config_keys"])
                    })
    
    @staticmethod
    def render_newsletter_signup() -> None:
        """Render newsletter signup section"""
        st.markdown("""
        <div style="background: #f7fafc; padding: 2rem; border-radius: 10px; text-align: center; margin: 2rem 0;">
            <h3 style="color: #2d3748; margin-bottom: 1rem;">Stay Updated</h3>
            <p style="color: #4a5568; margin-bottom: 1.5rem;">
                Get notified about new features, tutorials, and special offers!
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            email = st.text_input("", placeholder="Enter your email address", key="newsletter_email")
            if st.button("Subscribe", type="primary", use_container_width=True):
                if email:
                    st.success("🎉 Thank you for subscribing! (Feature coming soon)")
                else:
                    st.error("Please enter a valid email address")
    
    @staticmethod
    def render_trust_badges() -> None:
        """Render trust badges and security information"""
        st.markdown("""
        <div style="text-align: center; padding: 1.5rem; background: white; border-radius: 10px; margin: 1rem 0;">
            <h4 style="color: #2d3748; margin-bottom: 1rem;">Trusted & Secure</h4>
            <div style="display: flex; justify-content: center; align-items: center; gap: 2rem; flex-wrap: wrap;">
                <div style="text-align: center;">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">🔒</div>
                    <div style="font-size: 0.9rem; color: #4a5568;">SSL Encrypted</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">🛡️</div>
                    <div style="font-size: 0.9rem; color: #4a5568;">Privacy First</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">⚡</div>
                    <div style="font-size: 0.9rem; color: #4a5568;">Fast Processing</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">🇮🇳</div>
                    <div style="font-size: 0.9rem; color: #4a5568;">Made in India</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)