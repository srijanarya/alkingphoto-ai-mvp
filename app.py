"""
TalkingPhoto MVP - Professional UI Implementation
Inspired by sunmetalon.com and heimdallpower.com
"""

import streamlit as st
import time
from ui_theme import (
    apply_professional_theme,
    create_hero_section,
    create_feature_card,
    create_status_badge,
    create_loading_spinner,
    create_grid_layout
)

# Page configuration
st.set_page_config(
    page_title="TalkingPhoto AI - Bring Photos to Life",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply professional theme
apply_professional_theme()

# Initialize session state
if 'credits' not in st.session_state:
    st.session_state.credits = 3
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'video_generated' not in st.session_state:
    st.session_state.video_generated = False

def main():
    # Hero Section
    hero_clicked = create_hero_section(
        title="Transform Photos Into Living Stories",
        subtitle="AI-powered technology that makes your images speak with ultra-realistic voice and expressions",
        cta_text="Start Creating Magic ✨"
    )
    
    # Features Grid
    st.markdown("<h2 style='text-align: center; margin: 3rem 0 2rem 0; color: #ece7e2;'>Why Choose TalkingPhoto AI?</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = create_grid_layout(3)
    
    with col1:
        create_feature_card(
            "Lightning Fast",
            "Generate talking photos in under 60 seconds with our optimized AI pipeline",
            "⚡",
            link_to="create-section"  # Navigate to main creation section
        )
    
    with col2:
        create_feature_card(
            "Studio Quality",
            "Professional-grade output with natural voice synthesis and lip-sync accuracy",
            "🎭",
            link_to="voice-section"  # Navigate to voice selection
        )
    
    with col3:
        create_feature_card(
            "Multi-Language",
            "Support for 120+ languages including Hindi and regional Indian languages",
            "🌍",
            link_to="language-section"  # Make it clickable to navigate to language selection
        )
    
    # Main Application Section with ID anchor for smooth scrolling
    st.markdown("""
    <div id="create-section" style='margin: 4rem 0 2rem 0; text-align: center; scroll-margin-top: 20px;'>
        <h2 style='color: #ece7e2; font-size: 2.5rem; margin-bottom: 1rem;'>Create Your Talking Photo</h2>
        <p style='color: #7b756a; font-size: 1.2rem;'>Upload an image and write your script to begin</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Credits Display
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown(f"""
        <div class="feature-card" style="text-align: center; margin-bottom: 2rem;">
            <h3 style="color: #d96833; margin-bottom: 1rem;">Available Credits</h3>
            <div style="font-size: 3rem; font-weight: 900; color: #ece7e2;">{st.session_state.credits}</div>
            <p style="color: #7b756a; margin-top: 0.5rem;">videos remaining</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Upload Section
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3 style="color: #d96833; margin-bottom: 1rem;">📸 Upload Your Photo</h3>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Choose a high-quality portrait image",
            type=['png', 'jpg', 'jpeg'],
            help="For best results, use a front-facing portrait with clear facial features"
        )
        
        if uploaded_file:
            st.image(uploaded_file, caption="Your Photo", use_column_width=True)
            st.markdown(f"""
            <div style="margin-top: 1rem;">
                {create_status_badge("Image ready", "success")}
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3 style="color: #d96833; margin-bottom: 1rem;">✍️ Write Your Script</h3>
        </div>
        """, unsafe_allow_html=True)
        
        script_text = st.text_area(
            "What should your photo say?",
            placeholder="Example: Hello! I'm excited to share this amazing product with you. It has transformed my life and I know it will transform yours too...",
            height=150,
            max_chars=500,
            help="Keep it under 30 seconds for best results (approximately 80-100 words)"
        )
        
        # Voice Selection with ID anchor
        st.markdown("""
        <div id="voice-section" style="scroll-margin-top: 100px;">
            <h4 style="color: #d96833; margin-top: 1rem; margin-bottom: 0.5rem;">🎤 Select Voice Type</h4>
        </div>
        """, unsafe_allow_html=True)
        
        voice_type = st.selectbox(
            "",
            ["Professional Male", "Professional Female", "Friendly Male", "Friendly Female", "Energetic", "Calm & Soothing"],
            key="voice_selector"
        )
        
        # Language Selection with ID anchor
        st.markdown("""
        <div id="language-section" style="scroll-margin-top: 100px;">
            <h4 style="color: #d96833; margin-top: 1rem; margin-bottom: 0.5rem;">🌍 Select Language</h4>
        </div>
        """, unsafe_allow_html=True)
        
        language = st.selectbox(
            "",
            ["English", "Hindi", "Spanish", "French", "German", "Mandarin", "Tamil", "Telugu", "Bengali", 
             "Arabic", "Japanese", "Korean", "Italian", "Portuguese", "Russian", "Dutch", "Turkish",
             "Polish", "Swedish", "Norwegian", "Danish", "Finnish", "Greek", "Hebrew", "Thai",
             "Vietnamese", "Indonesian", "Malay", "Urdu", "Punjabi", "Gujarati", "Marathi", "Kannada",
             "Malayalam", "Odia", "Assamese", "Nepali", "Sinhala", "Swahili", "Yoruba", "Zulu"],
            key="language_selector"
        )
        
        if script_text:
            word_count = len(script_text.split())
            duration = word_count * 0.3  # Rough estimate
            st.markdown(f"""
            <div style="margin-top: 1rem;">
                {create_status_badge(f"~{duration:.1f} seconds", "warning")}
                {create_status_badge(f"{word_count} words", "success")}
            </div>
            """, unsafe_allow_html=True)
    
    # Generate Button
    st.markdown("<div style='margin: 3rem 0;'>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    
    with col2:
        if uploaded_file and script_text and st.session_state.credits > 0:
            if st.button("🎬 Generate Talking Photo", use_container_width=True, disabled=st.session_state.processing):
                st.session_state.processing = True
                
                # Progress indicators
                progress_container = st.empty()
                status_container = st.empty()
                
                # Simulate processing steps
                steps = [
                    ("Analyzing facial features...", 0.2),
                    ("Processing voice synthesis...", 0.4),
                    ("Generating lip-sync mapping...", 0.6),
                    ("Creating final video...", 0.8),
                    ("Applying post-processing...", 1.0)
                ]
                
                progress_bar = progress_container.progress(0)
                
                for step_text, progress_value in steps:
                    status_container.markdown(f"""
                    <div style="text-align: center; margin: 1rem 0;">
                        <p style="color: #d96833; font-size: 1.1rem;">{step_text}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    progress_bar.progress(progress_value)
                    time.sleep(1.5)
                
                # Success state
                st.session_state.credits -= 1
                st.session_state.processing = False
                st.session_state.video_generated = True
                
                progress_container.empty()
                status_container.empty()
                
                # Show success message
                st.balloons()
                st.success("🎉 Your talking photo is ready!")
                
                # Video display (mock)
                st.markdown("""
                <div class="feature-card" style="text-align: center; padding: 3rem;">
                    <h2 style="color: #d96833;">Your Talking Photo is Ready!</h2>
                    <p style="color: #7b756a; margin: 1rem 0;">Preview and download your creation below</p>
                    <div style="background: #1b170f; border-radius: 20px; padding: 2rem; margin: 2rem 0;">
                        <video controls style="width: 100%; max-width: 600px; border-radius: 15px;">
                            <source src="demo.mp4" type="video/mp4">
                            Your browser does not support the video tag.
                        </video>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Download buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.button("📥 Download HD Video", use_container_width=True)
                with col2:
                    st.button("🔗 Share Link", use_container_width=True)
                with col3:
                    st.button("🎬 Create Another", use_container_width=True)
        
        elif st.session_state.credits == 0:
            st.error("❌ No credits remaining. Please purchase more credits to continue.")
            if st.button("💳 Get More Credits", use_container_width=True):
                st.info("Payment integration coming soon! 🚀")
        
        elif not uploaded_file:
            st.info("📸 Please upload a photo to continue")
        
        elif not script_text:
            st.info("✍️ Please write a script for your photo")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Testimonials Section
    st.markdown("""
    <div style='margin: 5rem 0 3rem 0; text-align: center;'>
        <h2 style='color: #ece7e2; font-size: 2.5rem; margin-bottom: 3rem;'>Loved by Creators Worldwide</h2>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        create_feature_card(
            "Sarah Chen",
            "\"TalkingPhoto AI helped me create engaging content that increased my engagement by 300%!\"",
            "⭐⭐⭐⭐⭐"
        )
    
    with col2:
        create_feature_card(
            "Raj Patel", 
            "\"The quality is incredible! My clients can't believe these are AI-generated videos.\"",
            "⭐⭐⭐⭐⭐"
        )
    
    with col3:
        create_feature_card(
            "Maria Garcia",
            "\"Game-changer for my marketing campaigns. ROI increased by 250% in just 2 months!\"",
            "⭐⭐⭐⭐⭐"
        )
    
    # Footer
    st.markdown("""
    <div style='margin-top: 5rem; padding: 2rem 0; border-top: 1px solid rgba(217,104,51,0.2); text-align: center;'>
        <p style='color: #7b756a;'>© 2025 TalkingPhoto AI. Powered by cutting-edge AI technology.</p>
        <p style='color: #7b756a; margin-top: 0.5rem;'>
            <a href='#' style='color: #d96833; text-decoration: none; margin: 0 1rem;'>Terms</a>
            <a href='#' style='color: #d96833; text-decoration: none; margin: 0 1rem;'>Privacy</a>
            <a href='#' style='color: #d96833; text-decoration: none; margin: 0 1rem;'>Support</a>
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()