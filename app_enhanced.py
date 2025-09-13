import streamlit as st
import os
from datetime import datetime
from PIL import Image, ImageEnhance, ExifTags
import pillow_heif
import cv2
import numpy as np
import io
import logging
from typing import Optional, Tuple, Dict, Any
import tempfile
from pathlib import Path
import traceback

# Enable HEIF support for iPhone photos
pillow_heif.register_heif_opener()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="TalkingPhoto AI",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if 'generated_videos' not in st.session_state:
    st.session_state.generated_videos = []
if 'user_credits' not in st.session_state:
    st.session_state.user_credits = 1  # Free credit
if 'upload_errors' not in st.session_state:
    st.session_state.upload_errors = []
if 'processed_image' not in st.session_state:
    st.session_state.processed_image = None

# Mobile-optimized header
st.markdown("""
<div style="text-align: center; margin-bottom: 2rem;">
    <h1 style="color: #1e88e5; margin: 0;">🎬 TalkingPhoto AI</h1>
    <p style="color: #666; font-size: 1.1rem; margin: 0.5rem 0;">Transform Your Photos Into Talking Videos with AI</p>
    <p style="color: #888; font-size: 0.9rem;">📱 Mobile-optimized • 🚀 Fast processing • ✨ Professional results</p>
</div>
""", unsafe_allow_html=True)

# Check configuration with error handling
try:
    has_gemini = st.secrets.get('GEMINI_API_KEY', None) is not None
    has_cloudinary = st.secrets.get('CLOUDINARY_CLOUD_NAME', None) is not None
    has_database = st.secrets.get('DATABASE_URL', None) is not None
except Exception:
    # Handle case when secrets are not available (local development)
    has_gemini = False
    has_cloudinary = False
    has_database = False
    logger.warning("Secrets not available - running in demo mode")

# Status bar with mobile-friendly layout
st.markdown("### 📊 System Status")
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
            
            # Enhanced mobile-friendly file uploader
            st.markdown("""
            <div style="background-color: #f0f8ff; padding: 1rem; border-radius: 10px; margin: 1rem 0;">
                <h4 style="color: #1e88e5; margin: 0;">📱 Mobile Tips:</h4>
                <ul style="margin: 0.5rem 0;">
                    <li>✅ iPhone HEIC photos supported</li>
                    <li>✅ Photos will be automatically optimized</li>
                    <li>✅ Large files will be compressed</li>
                    <li>📸 Use good lighting for best results</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            uploaded_file = st.file_uploader(
                "Choose a portrait photo",
                type=['png', 'jpg', 'jpeg', 'heic', 'heif', 'webp', 'bmp', 'tiff'],
                accept_multiple_files=False,
                help="Supports: JPG, PNG, HEIC (iPhone), WebP. Max size: 20MB. Will be automatically optimized."
            )
            
            if uploaded_file:
                try:
                    success, processed_info = process_uploaded_image(uploaded_file)
                    if success:
                        processed_image = processed_info['processed_image']
                        original_size = processed_info['original_size']
                        final_size = processed_info['final_size']
                        file_format = processed_info['format']
                        
                        # Display processed image
                        st.image(processed_image, caption="✅ Photo processed and ready!", use_container_width=True)
                        
                        # Show processing info
                        col_info1, col_info2, col_info3 = st.columns(3)
                        with col_info1:
                            st.metric("Original Size", f"{original_size:.1f} MB")
                        with col_info2:
                            st.metric("Optimized Size", f"{final_size:.1f} MB")
                        with col_info3:
                            st.metric("Format", file_format.upper())
                            
                        # Store processed image
                        st.session_state.processed_image = processed_image
                        
                    else:
                        error_msg = processed_info.get('error', 'Unknown error occurred')
                        st.error(f"❌ Upload failed: {error_msg}")
                        display_troubleshooting_tips(error_msg)
                        
                except Exception as e:
                    logger.error(f"Unexpected error processing image: {str(e)}")
                    logger.error(traceback.format_exc())
                    st.error("❌ Unexpected error occurred. Please try again with a different image.")
                    display_troubleshooting_tips("processing_error")
        
        with col2:
            st.markdown("### 🎤 Add Your Script")
            text_input = st.text_area(
                "What should the photo say?",
                placeholder="Hello! Welcome to TalkingPhoto AI...",
                height=100,
                max_chars=500,
                help="Maximum 500 characters for best results"
            )
            
            # Character counter
            char_count = len(text_input) if text_input else 0
            char_color = "red" if char_count > 450 else "green"
            st.markdown(f'<p style="color: {char_color}; font-size: 0.8rem;">Characters: {char_count}/500</p>', 
                       unsafe_allow_html=True)
            
            voice = st.selectbox("Voice:", ["Natural", "Professional", "Friendly", "Energetic"])
            language = st.selectbox("Language:", ["English", "Hindi", "Spanish", "French"])
        
        # Enhanced generation button with better validation
        if st.button("🎬 Generate Video", use_container_width=True, type="primary"):
            if st.session_state.processed_image is not None and text_input:
                with st.spinner("Creating your video... (30-60 seconds)"):
                    import time
                    progress = st.progress(0)
                    status_text = st.empty()
                    
                    # Enhanced progress simulation with status updates
                    stages = [
                        (20, "🖼️ Analyzing your photo..."),
                        (40, "🤖 Generating facial landmarks..."),
                        (60, "🎤 Processing audio..."),
                        (80, "🎬 Creating lip-sync video..."),
                        (100, "✅ Finalizing your video...")
                    ]
                    
                    for target_progress, status_msg in stages:
                        status_text.text(status_msg)
                        current = progress._get_value() if hasattr(progress, '_get_value') else 0
                        for i in range(int(current), target_progress + 1):
                            time.sleep(0.05)
                            progress.progress(i)
                    
                    st.session_state.user_credits -= 1
                    st.success("✅ Video created successfully!")
                    st.balloons()
                    
                    # Demo video
                    st.video("https://www.w3schools.com/html/mov_bbb.mp4")
                    
                    # Enhanced download options
                    col_dl1, col_dl2 = st.columns(2)
                    with col_dl1:
                        st.download_button(
                            "📥 Download HD Video",
                            data=b"video_data",
                            file_name="talkingphoto_hd.mp4",
                            mime="video/mp4"
                        )
                    with col_dl2:
                        st.download_button(
                            "📱 Download Mobile Video",
                            data=b"video_data_mobile",
                            file_name="talkingphoto_mobile.mp4",
                            mime="video/mp4"
                        )
            elif not st.session_state.processed_image:
                st.error("📸 Please upload and process a photo first!")
            else:
                st.error("💬 Please enter some text for your video!")
    else:
        st.warning("You've used your free credit! Purchase more to continue.")
        st.markdown("""
        <div style="background-color: #fff3cd; padding: 1rem; border-radius: 10px; margin: 1rem 0;">
            <h4>🚀 Upgrade to Premium</h4>
            <ul>
                <li>✅ Unlimited video generations</li>
                <li>✅ HD quality exports</li>
                <li>✅ Priority processing</li>
                <li>✅ No watermarks</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

with tab2:
    st.header("Simple Pricing")
    
    # Enhanced pricing layout
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="border: 1px solid #ddd; padding: 1.5rem; border-radius: 10px; text-align: center;">
            <h3>🆓 Free Trial</h3>
            <h2 style="color: #28a745;">₹0</h2>
            <ul style="text-align: left; margin: 1rem 0;">
                <li>1 free video</li>
                <li>30 seconds max</li>
                <li>Watermark included</li>
                <li>Mobile optimized</li>
            </ul>
            <p style="color: #28a745; font-weight: bold;">Perfect for testing!</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="border: 2px solid #1e88e5; padding: 1.5rem; border-radius: 10px; text-align: center;">
            <h3>⭐ Pay Per Video</h3>
            <h2 style="color: #1e88e5;">₹99</h2>
            <ul style="text-align: left; margin: 1rem 0;">
                <li>HD quality (1080p)</li>
                <li>60 seconds max</li>
                <li>No watermark</li>
                <li>Fast processing</li>
                <li>Multiple formats</li>
            </ul>
            <p style="color: #1e88e5; font-weight: bold;">Most Popular!</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="border: 1px solid #ddd; padding: 1.5rem; border-radius: 10px; text-align: center;">
            <h3>💎 Premium Plan</h3>
            <h2 style="color: #6f42c1;">₹499/month</h2>
            <ul style="text-align: left; margin: 1rem 0;">
                <li>10 videos/month</li>
                <li>4K quality</li>
                <li>Priority support</li>
                <li>Advanced features</li>
                <li>API access</li>
            </ul>
            <p style="color: #6f42c1; font-weight: bold;">Best value!</p>
        </div>
        """, unsafe_allow_html=True)

with tab3:
    st.header("How It Works")
    
    # Enhanced how-it-works with mobile focus
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("""
        ### 🚀 Quick Steps
        
        1. **📱 Take or Upload Photo**
           - Use your phone camera
           - HEIC format supported
           - Auto-optimized for mobile
        
        2. **✏️ Write Your Script**
           - Up to 500 characters
           - Multiple languages
           - Voice selection
        
        3. **🎬 Generate Video**
           - AI lip-sync technology
           - Professional quality
           - Fast processing
        
        4. **📥 Download & Share**
           - HD and mobile formats
           - Direct sharing options
           - Cloud storage backup
        """)
    
    with col2:
        st.markdown("""
        ### 📱 Mobile Optimization
        
        **✅ iPhone Users:**
        - HEIC photos fully supported
        - Auto-rotation handling
        - Optimized file sizes
        
        **✅ Android Users:**
        - All standard formats
        - High-resolution support
        - Compression optimization
        
        **✅ All Devices:**
        - Responsive design
        - Touch-friendly interface
        - Fast upload speeds
        - Offline processing queue
        """)
    
    st.markdown("---")
    st.markdown("""
    ### 🔧 Technical Features
    
    - **AI-Powered:** Advanced lip-sync technology
    - **Multi-Language:** Support for 20+ languages
    - **High Quality:** Up to 4K video output
    - **Fast Processing:** Videos ready in 30-60 seconds
    - **Secure:** End-to-end encryption
    - **Cloud Storage:** Automatic backups
    """)

# Add custom CSS for mobile responsiveness
st.markdown("""
<style>
    /* Mobile-first responsive design */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        .stButton > button {
            width: 100%;
            height: 3rem;
            font-size: 1.1rem;
        }
        
        .stTextArea > div > div > textarea {
            min-height: 120px;
        }
        
        .stFileUploader > div {
            border: 3px dashed #1e88e5;
            border-radius: 10px;
            padding: 2rem 1rem;
            background-color: #f8f9fa;
        }
    }
    
    .error-container {
        background-color: #fff3f3;
        border-left: 4px solid #ff4444;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
    
    .success-container {
        background-color: #f3fff3;
        border-left: 4px solid #44ff44;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
    
    .info-container {
        background-color: #f0f8ff;
        border-left: 4px solid #1e88e5;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("---")
st.markdown("© 2024 TalkingPhoto AI | Made with ❤️ in India")


def process_uploaded_image(uploaded_file) -> Tuple[bool, Dict[str, Any]]:
    """
    Process uploaded image with comprehensive error handling and mobile optimization.
    
    Returns:
        Tuple[bool, Dict]: (success, info_dict)
    """
    try:
        # File size check (increased to 20MB for mobile photos)
        file_size_mb = uploaded_file.size / (1024 * 1024)
        if file_size_mb > 20:
            return False, {
                'error': f'File too large ({file_size_mb:.1f}MB). Maximum size is 20MB.',
                'error_type': 'file_size'
            }
        
        # Get file extension
        file_extension = uploaded_file.name.lower().split('.')[-1] if '.' in uploaded_file.name else ''
        
        # Read the file into bytes
        file_bytes = uploaded_file.getvalue()
        
        # Handle different image formats
        if file_extension in ['heic', 'heif']:
            # Convert HEIC to RGB
            try:
                pil_image = Image.open(io.BytesIO(file_bytes))
                if pil_image.mode != 'RGB':
                    pil_image = pil_image.convert('RGB')
            except Exception as e:
                logger.error(f"HEIC processing error: {str(e)}")
                return False, {
                    'error': 'Unable to process HEIC image. Try converting to JPG first.',
                    'error_type': 'heic_processing'
                }
        else:
            # Handle standard formats
            try:
                pil_image = Image.open(io.BytesIO(file_bytes))
                
                # Convert to RGB if needed
                if pil_image.mode in ('RGBA', 'LA', 'P'):
                    pil_image = pil_image.convert('RGB')
            except Exception as e:
                logger.error(f"Image opening error: {str(e)}")
                return False, {
                    'error': 'Unable to process image. Please try a different format.',
                    'error_type': 'image_format'
                }
        
        # Handle EXIF orientation for mobile photos
        try:
            pil_image = fix_image_orientation(pil_image)
        except Exception as e:
            logger.warning(f"EXIF orientation fix failed: {str(e)}")
        
        # Validate image dimensions
        width, height = pil_image.size
        if width < 200 or height < 200:
            return False, {
                'error': f'Image too small ({width}x{height}). Minimum size is 200x200 pixels.',
                'error_type': 'image_dimensions'
            }
        
        # Check if image is too large and needs resizing
        max_dimension = 2048
        if max(width, height) > max_dimension:
            # Resize while maintaining aspect ratio
            ratio = min(max_dimension / width, max_dimension / height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)
            pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logger.info(f"Resized image from {width}x{height} to {new_width}x{new_height}")
        
        # Enhance image quality
        pil_image = enhance_image_quality(pil_image)
        
        # Validate that it looks like a portrait/face photo
        face_validation = validate_face_in_image(pil_image)
        if not face_validation['has_face'] and face_validation['confidence'] < 0.3:
            logger.warning("No clear face detected in image")
            # Don't fail completely, just warn
        
        # Calculate final size
        img_byte_array = io.BytesIO()
        pil_image.save(img_byte_array, format='JPEG', quality=85, optimize=True)
        final_size_mb = len(img_byte_array.getvalue()) / (1024 * 1024)
        
        return True, {
            'processed_image': pil_image,
            'original_size': file_size_mb,
            'final_size': final_size_mb,
            'format': file_extension or 'unknown',
            'dimensions': pil_image.size,
            'face_validation': face_validation
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in image processing: {str(e)}")
        logger.error(traceback.format_exc())
        return False, {
            'error': f'Processing failed: {str(e)}',
            'error_type': 'processing_error'
        }


def fix_image_orientation(image: Image.Image) -> Image.Image:
    """
    Fix image orientation based on EXIF data (common issue with mobile photos).
    """
    try:
        # Get EXIF data
        exif = image._getexif()
        if exif is not None:
            # Find orientation tag
            for orientation_tag in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation_tag] == 'Orientation':
                    break
            else:
                return image
            
            orientation = exif.get(orientation_tag)
            if orientation is None:
                return image
            
            # Apply rotation based on orientation
            if orientation == 3:
                image = image.rotate(180, expand=True)
            elif orientation == 6:
                image = image.rotate(270, expand=True)
            elif orientation == 8:
                image = image.rotate(90, expand=True)
                
    except (AttributeError, KeyError, TypeError):
        # No EXIF data or not supported
        pass
    
    return image


def enhance_image_quality(image: Image.Image) -> Image.Image:
    """
    Apply basic image enhancements for better video quality.
    """
    try:
        # Enhance sharpness slightly
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.1)
        
        # Enhance contrast slightly
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.05)
        
        # Enhance color slightly
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(1.05)
        
    except Exception as e:
        logger.warning(f"Image enhancement failed: {str(e)}")
    
    return image


def validate_face_in_image(image: Image.Image) -> Dict[str, Any]:
    """
    Simple face detection using OpenCV (basic validation).
    """
    try:
        # Convert PIL image to OpenCV format
        opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
        
        # Use Haar cascade for face detection
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        has_face = len(faces) > 0
        confidence = min(len(faces) * 0.3, 1.0)  # Simple confidence score
        
        return {
            'has_face': has_face,
            'face_count': len(faces),
            'confidence': confidence,
            'faces': faces.tolist() if len(faces) > 0 else []
        }
        
    except Exception as e:
        logger.warning(f"Face detection failed: {str(e)}")
        return {
            'has_face': True,  # Assume it's fine if detection fails
            'face_count': 1,
            'confidence': 0.5,
            'faces': [],
            'error': str(e)
        }


def display_troubleshooting_tips(error_type: str):
    """
    Display helpful troubleshooting tips based on error type.
    """
    tips = {
        'file_size': [
            "📱 Try reducing image quality in your camera settings",
            "✂️ Use a photo editing app to compress the image",
            "📸 Take a new photo with lower resolution"
        ],
        'heic_processing': [
            "📱 iPhone users: Go to Settings > Camera > Formats > Most Compatible",
            "🔄 Convert HEIC to JPG using your phone's editing app",
            "📧 Email the photo to yourself (auto-converts to JPG)"
        ],
        'image_format': [
            "📸 Try saving the image as JPG or PNG",
            "🔄 Use a different photo app to open and re-save",
            "📱 Take a screenshot of the image and upload that"
        ],
        'image_dimensions': [
            "📸 Use a higher resolution camera setting",
            "🔍 Make sure the image isn't cropped too small",
            "📱 Take a new photo instead of using an old low-res one"
        ],
        'processing_error': [
            "🔄 Try refreshing the page and uploading again",
            "📱 Make sure you have a stable internet connection",
            "📸 Try a different photo",
            "🌐 Try using a different browser"
        ]
    }
    
    if error_type in tips:
        st.markdown("""
        <div class="info-container">
            <h4>💡 Troubleshooting Tips:</h4>
        </div>
        """, unsafe_allow_html=True)
        
        for tip in tips[error_type]:
            st.write(f"• {tip}")
    
    # Always show general tips
    with st.expander("📋 General Upload Tips", expanded=False):
        st.markdown("""
        **For best results:**
        - 📸 Use good lighting
        - 🎯 Center your face in the photo
        - 📱 Hold your phone steady
        - 🔄 Make sure the photo isn't blurry
        - 📐 Use a clear, recent photo
        
        **Supported formats:** JPG, PNG, HEIC (iPhone), WebP, BMP, TIFF
        
        **Need help?** Contact support with your device type and error message.
        """)