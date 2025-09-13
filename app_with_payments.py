"""
TalkingPhoto AI MVP - Complete Application with Stripe Payment Integration
Enhanced Streamlit app with comprehensive payment processing
"""

import streamlit as st
import time
import os
from datetime import datetime, timedelta

# Import our payment services
from services.payment_service import payment_service
from services.auth_service import streamlit_auth
from services.pricing_strategy import pricing_strategy
from services.security_service import security_service
from services.payment_analytics import analytics_service
from ui.payment_components import PaymentUI
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

# Initialize authentication
streamlit_auth.initialize_session_state()

# Initialize session state for payments
if 'credits' not in st.session_state:
    st.session_state.credits = 3
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'video_generated' not in st.session_state:
    st.session_state.video_generated = False
if 'show_pricing' not in st.session_state:
    st.session_state.show_pricing = False
if 'show_account' not in st.session_state:
    st.session_state.show_account = False
if 'show_billing' not in st.session_state:
    st.session_state.show_billing = False

def main():
    """Main application flow"""
    
    # Check authentication
    is_authenticated = streamlit_auth.check_authentication()
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("## 🎬 TalkingPhoto AI")
        
        if is_authenticated:
            streamlit_auth.render_user_menu()
            
            # User credit display
            user_info = payment_service.get_user_info(st.session_state.user['email'])
            if user_info:
                st.markdown(f"""
                **Your Credits:** {user_info['credits']} 
                
                **Plan:** {user_info['subscription_tier'].title()}
                """)
        else:
            st.markdown("### Access Your Account")
            if st.button("🔐 Sign In"):
                st.session_state.show_login = True
            if st.button("✨ Create Account"):
                st.session_state.show_register = True
    
    # Main content routing
    if st.session_state.get('show_login') and not is_authenticated:
        render_auth_page()
    elif st.session_state.get('show_register') and not is_authenticated:
        render_auth_page()
    elif st.session_state.get('show_pricing'):
        render_pricing_page()
    elif st.session_state.get('show_account') and is_authenticated:
        render_account_page()
    elif st.session_state.get('show_billing') and is_authenticated:
        render_billing_page()
    else:
        render_main_app()

def render_auth_page():
    """Render authentication page"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.session_state.get('show_register'):
            streamlit_auth.render_registration_form()
            
            if st.button("← Back to Sign In"):
                st.session_state.show_register = False
                st.session_state.show_login = True
                st.rerun()
        else:
            streamlit_auth.render_login_form()
            
            if st.button("Create New Account"):
                st.session_state.show_login = False
                st.session_state.show_register = True
                st.rerun()

def render_main_app():
    """Render main application interface"""
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
            "⚡"
        )
    
    with col2:
        create_feature_card(
            "Studio Quality",
            "Professional-grade output with natural voice synthesis and lip-sync accuracy",
            "🎭"
        )
    
    with col3:
        create_feature_card(
            "Multi-Language",
            "Support for 120+ languages including Hindi and regional Indian languages",
            "🌍"
        )
    
    # Pricing teaser
    if not streamlit_auth.check_authentication():
        render_pricing_teaser()
    
    # Main Application Section
    render_video_generation_interface()
    
    # Testimonials Section
    render_testimonials()

def render_pricing_teaser():
    """Render pricing teaser for non-authenticated users"""
    st.markdown("""
    <div style='margin: 4rem 0 2rem 0; text-align: center; background: rgba(217,104,51,0.1); padding: 3rem; border-radius: 20px;'>
        <h2 style='color: #d96833; font-size: 2.5rem; margin-bottom: 1rem;'>Unlock Unlimited Creativity</h2>
        <p style='color: #7b756a; font-size: 1.2rem; margin-bottom: 2rem;'>Join thousands of creators and unlock premium features</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card" style="text-align: center;">
            <h3 style="color: #d96833;">Free Plan</h3>
            <div style="font-size: 3rem; font-weight: 900; color: #ece7e2;">$0</div>
            <p style="color: #7b756a;">3 videos/month</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card" style="text-align: center; border: 2px solid #d96833;">
            <div style="background: #d96833; color: white; padding: 0.3rem 1rem; border-radius: 15px; font-size: 0.8rem; font-weight: bold; margin: -1rem -1rem 1rem -1rem;">Most Popular</div>
            <h3 style="color: #d96833;">Pro Plan</h3>
            <div style="font-size: 3rem; font-weight: 900; color: #ece7e2;">$49</div>
            <p style="color: #7b756a;">100 videos/month</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card" style="text-align: center;">
            <h3 style="color: #d96833;">Enterprise</h3>
            <div style="font-size: 3rem; font-weight: 900; color: #ece7e2;">$199</div>
            <p style="color: #7b756a;">500 videos/month</p>
        </div>
        """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 View All Plans & Features", use_container_width=True):
            st.session_state.show_pricing = True
            st.rerun()

def render_video_generation_interface():
    """Render video generation interface"""
    # Get user credits
    user_credits = 3  # Default for non-authenticated users
    user_email = None
    
    if streamlit_auth.check_authentication():
        user_email = st.session_state.user['email']
        user_info = payment_service.get_user_info(user_email)
        if user_info:
            user_credits = user_info['credits']
    
    st.markdown("""
    <div style='margin: 4rem 0 2rem 0; text-align: center;'>
        <h2 style='color: #ece7e2; font-size: 2.5rem; margin-bottom: 1rem;'>Create Your Talking Photo</h2>
        <p style='color: #7b756a; font-size: 1.2rem;'>Upload an image and write your script to begin</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Credits Display
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <div class="feature-card" style="text-align: center; margin-bottom: 2rem;">
            <h3 style="color: #d96833; margin-bottom: 1rem;">Available Credits</h3>
            <div style="font-size: 3rem; font-weight: 900; color: #ece7e2;">{user_credits}</div>
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
        
        # Voice Selection
        voice_type = st.selectbox(
            "Select Voice Type",
            ["Professional Male", "Professional Female", "Friendly Male", "Friendly Female", "Energetic", "Calm & Soothing"]
        )
        
        # Language Selection
        language = st.selectbox(
            "Select Language",
            ["English", "Hindi", "Spanish", "French", "German", "Mandarin", "Tamil", "Telugu", "Bengali"]
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
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if uploaded_file and script_text and user_credits > 0:
            if st.button("🎬 Generate Talking Photo", use_container_width=True, disabled=st.session_state.processing):
                handle_video_generation(user_email, uploaded_file, script_text, voice_type, language)
        
        elif user_credits == 0:
            st.error("❌ No credits remaining. Please purchase more credits to continue.")
            if st.button("💳 Get More Credits", use_container_width=True):
                if streamlit_auth.check_authentication():
                    st.session_state.show_billing = True
                    st.rerun()
                else:
                    st.session_state.show_pricing = True
                    st.rerun()
        
        elif not uploaded_file:
            st.info("📸 Please upload a photo to continue")
        
        elif not script_text:
            st.info("✍️ Please write a script for your photo")
    
    st.markdown("</div>", unsafe_allow_html=True)

def handle_video_generation(user_email: str, uploaded_file, script_text: str, voice_type: str, language: str):
    """Handle video generation process"""
    st.session_state.processing = True
    
    # Security validation
    if user_email:
        validation_result = security_service.validate_payment_request(
            request_data={
                'action': 'video_generation',
                'user_email': user_email,
                'script_length': len(script_text)
            },
            user_id=None,  # You would get this from auth
            ip_address="127.0.0.1"  # You would get this from request
        )
        
        if not validation_result['is_valid']:
            st.error("Request blocked for security reasons. Please try again later.")
            st.session_state.processing = False
            return
    
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
    
    # Use credit
    if user_email:
        credit_used = payment_service.use_credit(user_email, "Video generation")
        if not credit_used:
            st.error("Failed to use credit. Please contact support.")
            st.session_state.processing = False
            return
        
        # Track analytics
        analytics_service.track_payment_event("credit_usage", {
            "customer_email": user_email,
            "credits_used": 1,
            "feature": "video_generation"
        })
    
    # Success state
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
        if st.button("🎬 Create Another", use_container_width=True):
            st.session_state.video_generated = False
            st.rerun()

def render_pricing_page():
    """Render pricing page"""
    st.markdown("""
    <div style='text-align: center; margin: 2rem 0;'>
        <h1 style='color: #ece7e2; font-size: 3rem;'>Choose Your Plan</h1>
        <p style='color: #7b756a; font-size: 1.2rem;'>Unlock unlimited creativity with our flexible pricing</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Back button
    if st.button("← Back to App"):
        st.session_state.show_pricing = False
        st.rerun()
    
    # Pricing display
    user_country = "US"  # You would detect this from IP
    pricing_display = pricing_strategy.get_optimal_pricing_display(user_country)
    
    PaymentUI.render_pricing_cards()
    PaymentUI.render_credit_purchase()
    PaymentUI.render_payment_form()

def render_account_page():
    """Render account management page"""
    st.markdown("""
    <div style='text-align: center; margin: 2rem 0;'>
        <h1 style='color: #ece7e2; font-size: 3rem;'>Account Settings</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Back button
    if st.button("← Back to App"):
        st.session_state.show_account = False
        st.rerun()
    
    PaymentUI.render_account_management()

def render_billing_page():
    """Render billing and subscription management"""
    st.markdown("""
    <div style='text-align: center; margin: 2rem 0;'>
        <h1 style='color: #ece7e2; font-size: 3rem;'>Billing & Subscriptions</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Back button
    if st.button("← Back to App"):
        st.session_state.show_billing = False
        st.rerun()
    
    # Current subscription info
    user_email = st.session_state.user['email']
    user_info = payment_service.get_user_info(user_email)
    
    if user_info:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div class="feature-card">
                <h3 style="color: #d96833;">Current Subscription</h3>
                <div style="font-size: 1.5rem; font-weight: bold; color: #ece7e2; margin: 1rem 0;">
                    {user_info['subscription_tier'].title()} Plan
                </div>
                <p style="color: #7b756a;">Credits: {user_info['credits']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="feature-card">
                <h3 style="color: #d96833;">Quick Actions</h3>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🔄 Upgrade Plan", use_container_width=True):
                st.session_state.show_pricing = True
                st.rerun()
            
            if st.button("💳 Buy Credits", use_container_width=True):
                st.session_state.show_credit_purchase = True
                st.rerun()
            
            if user_info['subscription_tier'] != 'free':
                if st.button("❌ Cancel Subscription", use_container_width=True):
                    if payment_service.cancel_subscription(user_email):
                        st.success("Subscription canceled successfully.")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Failed to cancel subscription.")
    
    # Payment history
    payments = payment_service.get_payment_history(user_email)
    
    if payments:
        st.markdown("<h3 style='color: #ece7e2; margin: 2rem 0 1rem 0;'>Payment History</h3>", unsafe_allow_html=True)
        
        payment_data = []
        for payment in payments[:10]:
            payment_data.append({
                "Date": payment['created_at'][:10],
                "Type": payment['payment_type'].title(),
                "Amount": f"${payment['amount']:.2f}",
                "Status": payment['status'].title(),
                "Credits": payment['credits_purchased'] or "-"
            })
        
        if payment_data:
            st.dataframe(payment_data, use_container_width=True)

def render_testimonials():
    """Render testimonials section"""
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

# Run the application
if __name__ == "__main__":
    main()
    
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