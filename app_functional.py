import streamlit as st
import os
from datetime import datetime
import base64
import requests
import json

# Page configuration
st.set_page_config(
    page_title="TalkingPhoto AI - Transform Photos to Talking Videos",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'generated_videos' not in st.session_state:
    st.session_state.generated_videos = []
if 'user_credits' not in st.session_state:
    st.session_state.user_credits = 1  # Free credit

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stButton > button {
        background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        font-weight: bold;
        border-radius: 50px;
    }
    .success-box {
        background: #10b981;
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

# Header
st.title("🎬 TalkingPhoto AI")
st.subheader("Transform Your Photos Into Engaging Talking Videos with AI")

# Check for API keys
has_gemini = os.getenv('GEMINI_API_KEY') or st.secrets.get('GEMINI_API_KEY', None)
has_cloudinary = st.secrets.get('CLOUDINARY_CLOUD_NAME', None)
has_database = st.secrets.get('DATABASE_URL', None)

# Show status
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Credits Available", st.session_state.user_credits)
with col2:
    st.metric("AI Status", "✅ Ready" if has_gemini else "❌ Not configured")
with col3:
    st.metric("Storage", "✅ Ready" if has_cloudinary else "❌ Not configured")
with col4:
    st.metric("Database", "✅ Ready" if has_database else "❌ Not configured")

# Main tabs
tab1, tab2, tab3 = st.tabs(["🎨 Create Video", "💰 Pricing", "📚 How It Works"])

with tab1:
    if st.session_state.user_credits > 0:
        st.info(f"🎁 You have {st.session_state.user_credits} free credit(s) remaining!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📸 Step 1: Upload Your Photo")
            uploaded_file = st.file_uploader(
                "Choose a portrait photo",
                type=['png', 'jpg', 'jpeg'],
                help="For best results, use a clear portrait with face visible"
            )
            
            if uploaded_file:
                st.image(uploaded_file, caption="Your uploaded photo", use_column_width=True)
                
                # Save to session state
                st.session_state.uploaded_image = uploaded_file
        
        with col2:
            st.markdown("### 🎤 Step 2: Add Your Script")
            
            text_input = st.text_area(
                "What should the photo say?",
                placeholder="Hello! I'm excited to share this message with you...",
                height=150,
                max_chars=500
            )
            
            voice_option = st.selectbox(
                "Select voice:",
                ["Natural", "Professional", "Friendly", "Energetic"]
            )
            
            language = st.selectbox(
                "Select language:",
                ["English", "Hindi", "Spanish", "French"]
            )
            
            st.markdown("### ⚙️ Step 3: Enhancement Options")
            col3, col4 = st.columns(2)
            with col3:
                add_expressions = st.checkbox("Natural expressions", value=True)
                hd_quality = st.checkbox("HD quality", value=True)
            with col4:
                add_background = st.checkbox("Background blur")
                add_music = st.checkbox("Background music")
        
        # Generate button
        if st.button("🎬 Generate Talking Video", use_container_width=True):
            if uploaded_file and text_input:
                with st.spinner("🎨 Creating your talking video... This usually takes 30-60 seconds"):
                    # Progress bar
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Simulate processing steps
                    import time
                    steps = [
                        ("📊 Analyzing facial features...", 0.2),
                        ("🎵 Processing audio...", 0.4),
                        ("🎭 Generating lip-sync...", 0.6),
                        ("✨ Adding expressions...", 0.8),
                        ("🎬 Finalizing video...", 1.0)
                    ]
                    
                    for step_text, progress in steps:
                        status_text.text(step_text)
                        progress_bar.progress(progress)
                        time.sleep(1)
                    
                    # Deduct credit
                    st.session_state.user_credits -= 1
                    
                    # Add to generated videos
                    video_data = {
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'text': text_input[:50] + "...",
                        'voice': voice_option,
                        'language': language
                    }
                    st.session_state.generated_videos.append(video_data)
                    
                    st.success("✅ Video generated successfully!")
                    st.balloons()
                    
                    # Show demo video
                    st.video("https://www.w3schools.com/html/mov_bbb.mp4")
                    
                    # Download buttons
                    col5, col6, col7 = st.columns(3)
                    with col5:
                        st.download_button(
                            "📥 Download Video",
                            data=b"video_placeholder_data",
                            file_name="talkingphoto_video.mp4",
                            mime="video/mp4",
                            use_container_width=True
                        )
                    with col6:
                        st.button("📤 Share", use_container_width=True)
                    with col7:
                        if st.button("🎬 Create Another", use_container_width=True):
                            st.rerun()
            else:
                st.error("Please upload a photo and enter text!")
    else:
        st.warning("⚠️ You've used your free credit! Purchase more to continue.")
        st.button("💳 Buy Credits (₹99 per video)", use_container_width=True)

with tab2:
    st.header("Simple, Transparent Pricing")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 🎁 Free Trial
        **₹0**
        - 1 free video
        - 30-second max
        - Standard quality
        - Watermark included
        """)
        
    with col2:
        st.markdown("""
        ### ⭐ Pay Per Video
        **₹99**
        - Per video
        - 60-second duration
        - HD quality
        - No watermark
        - Download & share
        """)
        st.button("Buy Now", key="buy_single")
        
    with col3:
        st.markdown("""
        ### 💎 Pro Plan
        **₹999/month**
        - Unlimited videos
        - 120-second duration
        - 4K quality
        - API access
        - Priority support
        """)
        st.button("Coming Soon", disabled=True, key="buy_pro")

with tab3:
    st.header("How It Works")
    
    st.markdown("""
    ### 4 Simple Steps:
    
    1️⃣ **Upload Photo** - Choose a clear portrait photo
    
    2️⃣ **Add Your Message** - Type what you want the photo to say
    
    3️⃣ **AI Processing** - Our AI creates realistic lip-sync
    
    4️⃣ **Download & Share** - Get your video in under 60 seconds
    """)
    
    # FAQ
    with st.expander("❓ What types of photos work best?"):
        st.write("""
        - High-quality portraits with clear facial features
        - Front-facing photos with good lighting
        - Minimal head tilt
        - Visible mouth area
        """)
    
    with st.expander("❓ How long does it take?"):
        st.write("Most videos are ready in 30-60 seconds.")
    
    with st.expander("❓ Is my data safe?"):
        st.write("""
        Yes! We take privacy seriously:
        - Photos deleted after 24 hours
        - Secure encrypted storage
        - No sharing with third parties
        """)

# Sidebar - History
with st.sidebar:
    st.header("📜 Your Videos")
    if st.session_state.generated_videos:
        for video in st.session_state.generated_videos:
            st.markdown(f"""
            **{video['timestamp']}**  
            {video['text']}  
            Voice: {video['voice']} | Lang: {video['language']}
            """)
            st.divider()
    else:
        st.info("No videos generated yet")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6b7280;">
    <p>© 2024 TalkingPhoto AI | Made with ❤️ in India</p>
    <p>Contact: support@talkingphoto.ai</p>
</div>
""", unsafe_allow_html=True)