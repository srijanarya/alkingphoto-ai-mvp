import streamlit as st
import os
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="TalkingPhoto AI",
    page_icon="🎬",
    layout="wide"
)

# Initialize session state
if 'generated_videos' not in st.session_state:
    st.session_state.generated_videos = []
if 'user_credits' not in st.session_state:
    st.session_state.user_credits = 1  # Free credit

# Header
st.title("🎬 TalkingPhoto AI")
st.subheader("Transform Your Photos Into Talking Videos with AI")

# Check configuration
has_gemini = st.secrets.get('GEMINI_API_KEY', None) is not None
has_cloudinary = st.secrets.get('CLOUDINARY_CLOUD_NAME', None) is not None
has_database = st.secrets.get('DATABASE_URL', None) is not None

# Status bar
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Free Credits", st.session_state.user_credits)
with col2:
    st.metric("AI", "✅ Ready" if has_gemini else "⚠️ Setup needed")
with col3:
    st.metric("Storage", "✅ Ready" if has_cloudinary else "⚠️ Setup needed")
with col4:
    st.metric("Database", "✅ Ready" if has_database else "⚠️ Setup needed")

# Main interface
tab1, tab2, tab3 = st.tabs(["🎨 Create Video", "💰 Pricing", "📚 How It Works"])

with tab1:
    if st.session_state.user_credits > 0:
        st.info(f"🎁 You have {st.session_state.user_credits} free credit remaining!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📸 Upload Your Photo")
            uploaded_file = st.file_uploader(
                "Choose a portrait photo",
                type=['png', 'jpg', 'jpeg'],
                accept_multiple_files=False,
                help="Max file size: 5MB. Use a clear portrait photo."
            )
            
            if uploaded_file:
                # Check file size (5MB limit)
                file_size = uploaded_file.size
                if file_size > 5 * 1024 * 1024:  # 5MB in bytes
                    st.error("⚠️ File too large! Please use an image under 5MB.")
                    uploaded_file = None
                else:
                    try:
                        st.image(uploaded_file, caption="Uploaded photo", use_container_width=True)
                    except Exception as e:
                        st.error(f"⚠️ Error displaying image. Please try a different photo.")
        
        with col2:
            st.markdown("### 🎤 Add Your Script")
            text_input = st.text_area(
                "What should the photo say?",
                placeholder="Hello! Welcome to TalkingPhoto AI...",
                height=100
            )
            
            voice = st.selectbox("Voice:", ["Natural", "Professional", "Friendly"])
            language = st.selectbox("Language:", ["English", "Hindi", "Spanish"])
        
        if st.button("🎬 Generate Video", use_container_width=True, type="primary"):
            if uploaded_file and text_input:
                with st.spinner("Creating your video... (30-60 seconds)"):
                    import time
                    progress = st.progress(0)
                    for i in range(100):
                        time.sleep(0.01)
                        progress.progress(i + 1)
                    
                    st.session_state.user_credits -= 1
                    st.success("✅ Video created successfully!")
                    st.balloons()
                    
                    # Demo video
                    st.video("https://www.w3schools.com/html/mov_bbb.mp4")
                    
                    st.download_button(
                        "📥 Download Video",
                        data=b"video_data",
                        file_name="talkingphoto.mp4",
                        mime="video/mp4"
                    )
            else:
                st.error("Please upload a photo and enter text!")
    else:
        st.warning("You've used your free credit! Purchase more to continue.")

with tab2:
    st.header("Simple Pricing")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        ### Free Trial
        - 1 free video
        - 30 seconds max
        - Watermark
        """)
    
    with col2:
        st.markdown("""
        ### Pay Per Video - ₹99
        - HD quality
        - 60 seconds
        - No watermark
        """)

with tab3:
    st.header("How It Works")
    st.markdown("""
    1. Upload a portrait photo
    2. Enter text or audio
    3. AI generates lip-sync
    4. Download your video!
    """)

st.markdown("---")
st.markdown("© 2024 TalkingPhoto AI | Made with ❤️ in India")