import streamlit as st
from datetime import datetime

# Page config
st.set_page_config(
    page_title="TalkingPhoto AI",
    page_icon="🎬",
    layout="wide"
)

# Session state
if 'credits' not in st.session_state:
    st.session_state.credits = 1

# Header
st.title("🎬 TalkingPhoto AI")
st.subheader("Transform Your Photos Into Talking Videos")

# Status
cols = st.columns(4)
with cols[0]:
    st.metric("Free Credits", st.session_state.credits)
with cols[1]:
    st.metric("Status", "✅ Ready")

# Main tabs
tab1, tab2, tab3 = st.tabs(["Create Video", "Pricing", "How It Works"])

with tab1:
    if st.session_state.credits > 0:
        st.success(f"🎁 You have {st.session_state.credits} free credit!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📸 Upload Photo")
            photo = st.file_uploader("Choose photo", type=['png', 'jpg', 'jpeg'])
            if photo:
                st.image(photo, use_container_width=True)
        
        with col2:
            st.markdown("### 🎤 Add Script")
            text = st.text_area("What to say?", height=100)
            voice = st.selectbox("Voice", ["Natural", "Professional"])
        
        if st.button("🎬 Generate Video", use_container_width=True, type="primary"):
            if photo and text:
                with st.spinner("Creating video..."):
                    import time
                    bar = st.progress(0)
                    for i in range(100):
                        time.sleep(0.01)
                        bar.progress(i + 1)
                    st.session_state.credits -= 1
                    st.success("✅ Video ready!")
                    st.balloons()
                    st.video("https://www.w3schools.com/html/mov_bbb.mp4")
            else:
                st.error("Upload photo and add text!")
    else:
        st.warning("No credits left! Buy more to continue.")

with tab2:
    st.header("Pricing")
    col1, col2 = st.columns(2)
    with col1:
        st.info("**Free Trial**\n- 1 video\n- Watermark")
    with col2:
        st.info("**₹99/video**\n- HD quality\n- No watermark")

with tab3:
    st.header("How It Works")
    st.write("1. Upload photo\n2. Add text\n3. Get video!")

st.markdown("---")
st.caption("© 2024 TalkingPhoto AI")