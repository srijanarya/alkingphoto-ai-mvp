"""
TalkingPhoto AI MVP - Streamlit Frontend Application
Epic 4: User Experience & Interface Implementation

This is the main Streamlit application implementing:
- US-4.1: Photo Upload Interface (8 pts)
- US-4.2: Text Input & Voice Configuration (13 pts)  
- US-4.3: Video Generation Dashboard (21 pts)
"""

import streamlit as st
import requests
import json
import time
import io
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncio
from PIL import Image
import pandas as pd
from pathlib import Path
import websocket
import threading
import plotly.graph_objects as go
import plotly.express as px
from dataclasses import dataclass

# Configure Streamlit page
st.set_page_config(
    page_title="TalkingPhoto AI MVP",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "TalkingPhoto AI MVP - Transform photos into engaging videos with AI"
    }
)

# Custom CSS for professional design
st.markdown("""
<style>
    .main {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .upload-section {
        border: 2px dashed #cccccc;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background: #fafafa;
        margin: 1rem 0;
    }
    .voice-preview {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    .progress-container {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    .status-badge {
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: bold;
        text-transform: uppercase;
    }
    .status-processing {
        background-color: #ffc107;
        color: #212529;
    }
    .status-completed {
        background-color: #28a745;
        color: white;
    }
    .status-error {
        background-color: #dc3545;
        color: white;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000/api')
WS_URL = os.getenv('WS_URL', 'ws://localhost:5000/ws')
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp']
CHARACTER_LIMIT = 500

@dataclass
class VideoGeneration:
    id: str
    photo_name: str
    text: str
    voice_type: str
    status: str
    progress: int
    created_at: datetime
    estimated_completion: Optional[datetime] = None
    video_url: Optional[str] = None
    error_message: Optional[str] = None

class TalkingPhotoApp:
    def __init__(self):
        self.session_state = st.session_state
        self.init_session_state()
        self.api_client = APIClient()
        
    def init_session_state(self):
        """Initialize session state variables"""
        defaults = {
            'authenticated': False,
            'user_token': None,
            'user_info': None,
            'uploaded_photos': [],
            'generation_history': [],
            'current_generation': None,
            'websocket_connected': False,
            'voice_samples': {},
            'saved_templates': []
        }
        
        for key, value in defaults.items():
            if key not in self.session_state:
                self.session_state[key] = value

    def run(self):
        """Main application entry point"""
        if not self.session_state.authenticated:
            self.render_auth_page()
        else:
            self.render_main_app()

    def render_auth_page(self):
        """Render authentication page"""
        st.title("🎬 TalkingPhoto AI MVP")
        st.subheader("Transform Your Photos into Engaging Videos")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            tab1, tab2 = st.tabs(["Sign In", "Create Account"])
            
            with tab1:
                self.render_login_form()
            
            with tab2:
                self.render_register_form()

    def render_login_form(self):
        """Render login form"""
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="Enter your email")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            remember_me = st.checkbox("Remember me")
            
            submit = st.form_submit_button("Sign In", use_container_width=True)
            
            if submit and email and password:
                success, data = self.api_client.login(email, password)
                if success:
                    self.session_state.authenticated = True
                    self.session_state.user_token = data.get('token')
                    self.session_state.user_info = data.get('user')
                    st.success("Successfully signed in!")
                    st.rerun()
                else:
                    st.error(data.get('message', 'Login failed'))

    def render_register_form(self):
        """Render registration form"""
        with st.form("register_form"):
            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input("First Name", placeholder="John")
            with col2:
                last_name = st.text_input("Last Name", placeholder="Doe")
            
            email = st.text_input("Email", placeholder="john@example.com")
            password = st.text_input("Password", type="password", placeholder="Strong password")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm password")
            
            terms = st.checkbox("I agree to the Terms of Service and Privacy Policy")
            
            submit = st.form_submit_button("Create Account", use_container_width=True)
            
            if submit and all([first_name, last_name, email, password, confirm_password, terms]):
                if password != confirm_password:
                    st.error("Passwords do not match")
                    return
                
                success, data = self.api_client.register(first_name, last_name, email, password)
                if success:
                    st.success("Account created successfully! Please sign in.")
                else:
                    st.error(data.get('message', 'Registration failed'))

    def render_main_app(self):
        """Render main application interface"""
        # Header
        self.render_header()
        
        # Sidebar
        self.render_sidebar()
        
        # Main content based on selected page
        page = self.session_state.get('current_page', 'upload')
        
        if page == 'upload':
            self.render_upload_page()
        elif page == 'generate':
            self.render_generation_page()
        elif page == 'dashboard':
            self.render_dashboard_page()
        elif page == 'history':
            self.render_history_page()
        elif page == 'account':
            self.render_account_page()

    def render_header(self):
        """Render application header"""
        col1, col2, col3 = st.columns([2, 3, 2])
        
        with col1:
            st.title("🎬 TalkingPhoto AI")
        
        with col2:
            # Status indicators
            if self.session_state.current_generation:
                gen = self.session_state.current_generation
                if gen.status == 'processing':
                    st.info(f"🔄 Generating video... {gen.progress}%")
                elif gen.status == 'completed':
                    st.success("✅ Video generated successfully!")
                elif gen.status == 'error':
                    st.error(f"❌ Generation failed: {gen.error_message}")
        
        with col3:
            user_name = self.session_state.user_info.get('name', 'User')
            st.write(f"Welcome, {user_name}!")
            if st.button("Sign Out"):
                self.logout()

    def render_sidebar(self):
        """Render application sidebar navigation"""
        with st.sidebar:
            st.title("Navigation")
            
            pages = {
                'upload': '📤 Upload Photo',
                'generate': '🎬 Generate Video',
                'dashboard': '📊 Dashboard',
                'history': '📋 History',
                'account': '👤 Account'
            }
            
            for page_id, page_name in pages.items():
                if st.button(page_name, key=f"nav_{page_id}"):
                    self.session_state.current_page = page_id
                    st.rerun()
            
            st.divider()
            
            # Account info
            user_info = self.session_state.user_info or {}
            st.write("**Account Details**")
            st.write(f"Plan: {user_info.get('plan', 'Free')}")
            st.write(f"Credits: {user_info.get('credits', 0)}")
            
            # Quick stats
            st.divider()
            st.write("**Quick Stats**")
            st.metric("Videos Created", len(self.session_state.generation_history))
            st.metric("Photos Uploaded", len(self.session_state.uploaded_photos))

    def render_upload_page(self):
        """US-4.1: Photo Upload Interface Implementation"""
        st.header("📤 Photo Upload")
        st.write("Upload your photo to get started. We support JPG, PNG, and WebP formats.")
        
        # Upload section
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Drag and drop upload
            uploaded_file = st.file_uploader(
                "Choose a photo",
                type=ALLOWED_EXTENSIONS,
                help=f"Maximum file size: {MAX_FILE_SIZE // (1024*1024)}MB",
                label_visibility="collapsed"
            )
            
            if uploaded_file:
                self.handle_photo_upload(uploaded_file)
        
        with col2:
            st.write("**Requirements:**")
            st.write("• Clear, well-lit photo")
            st.write("• Face should be visible")
            st.write("• High resolution preferred")
            st.write("• File size < 10MB")
        
        # Upload history
        if self.session_state.uploaded_photos:
            st.subheader("📋 Upload History")
            self.render_upload_history()
        
        # Photo editing tools
        if uploaded_file:
            st.subheader("🎨 Basic Photo Editing")
            self.render_photo_editor(uploaded_file)

    def handle_photo_upload(self, uploaded_file):
        """Handle photo upload with validation and preview"""
        if uploaded_file.size > MAX_FILE_SIZE:
            st.error(f"File too large! Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB")
            return
        
        # Display preview
        image = Image.open(uploaded_file)
        st.image(image, caption=f"Preview: {uploaded_file.name}", use_container_width=True)
        
        # Upload progress simulation
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i in range(101):
            progress_bar.progress(i)
            status_text.text(f'Uploading... {i}%')
            time.sleep(0.01)
        
        # Validate photo
        is_valid, validation_result = self.validate_photo(image)
        
        if is_valid:
            # Upload to backend
            success, photo_id = self.api_client.upload_photo(uploaded_file)
            if success:
                st.success("✅ Photo uploaded successfully!")
                self.session_state.uploaded_photos.append({
                    'id': photo_id,
                    'name': uploaded_file.name,
                    'uploaded_at': datetime.now(),
                    'validation': validation_result
                })
                
                # Show option to proceed to generation
                if st.button("🎬 Generate Video with this Photo", type="primary"):
                    self.session_state.current_page = 'generate'
                    self.session_state.selected_photo = photo_id
                    st.rerun()
            else:
                st.error("Upload failed. Please try again.")
        else:
            st.error(f"Photo validation failed: {validation_result['error']}")

    def validate_photo(self, image):
        """Validate uploaded photo"""
        # Basic validation
        width, height = image.size
        if width < 512 or height < 512:
            return False, {"error": "Image resolution too low. Minimum 512x512 pixels required."}
        
        # Face detection (mock implementation)
        # In real implementation, this would use face detection API
        return True, {
            "face_detected": True,
            "quality_score": 0.85,
            "resolution": f"{width}x{height}",
            "recommendations": ["Good lighting", "Clear facial features"]
        }

    def render_upload_history(self):
        """Render upload history table"""
        df = pd.DataFrame([
            {
                'Photo': photo['name'],
                'Upload Date': photo['uploaded_at'].strftime('%Y-%m-%d %H:%M'),
                'Quality Score': photo['validation'].get('quality_score', 'N/A'),
                'Actions': photo['id']
            }
            for photo in self.session_state.uploaded_photos
        ])
        
        st.dataframe(df, use_container_width=True)

    def render_photo_editor(self, uploaded_file):
        """Basic photo editing tools"""
        image = Image.open(uploaded_file)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            brightness = st.slider("Brightness", -50, 50, 0)
        with col2:
            contrast = st.slider("Contrast", -50, 50, 0)
        with col3:
            crop = st.checkbox("Auto-crop face")
        
        # Apply basic adjustments (simplified)
        if brightness != 0 or contrast != 0 or crop:
            st.write("📝 Editing preview (simplified)")
            st.image(image, caption="Edited preview", use_container_width=True)

    def render_generation_page(self):
        """US-4.2 & US-4.3: Text Input, Voice Configuration & Video Generation"""
        st.header("🎬 Generate Video")
        
        # Check if photo is selected
        if not self.session_state.uploaded_photos:
            st.warning("Please upload a photo first!")
            if st.button("📤 Go to Upload"):
                self.session_state.current_page = 'upload'
                st.rerun()
            return
        
        # Photo selection
        st.subheader("1️⃣ Select Photo")
        photo_options = {photo['id']: photo['name'] for photo in self.session_state.uploaded_photos}
        selected_photo_id = st.selectbox("Choose photo", options=list(photo_options.keys()), 
                                       format_func=lambda x: photo_options[x])
        
        # Text input section
        st.subheader("2️⃣ Enter Your Text")
        self.render_text_input_section()
        
        # Voice configuration section
        st.subheader("3️⃣ Configure Voice")
        voice_config = self.render_voice_configuration()
        
        # Generation section
        st.subheader("4️⃣ Generate Video")
        self.render_generation_section(selected_photo_id, voice_config)

    def render_text_input_section(self):
        """US-4.2: Text Input & Voice Configuration - Text Part"""
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Rich text editor (simplified)
            text_input = st.text_area(
                "Enter the text you want the photo to speak",
                height=150,
                placeholder="Type your message here...",
                max_chars=CHARACTER_LIMIT,
                help=f"Maximum {CHARACTER_LIMIT} characters"
            )
            
            # Character counter
            char_count = len(text_input) if text_input else 0
            char_color = "red" if char_count > CHARACTER_LIMIT * 0.9 else "green"
            st.markdown(f'<p style="color: {char_color}">Characters: {char_count}/{CHARACTER_LIMIT}</p>', 
                       unsafe_allow_html=True)
            
            self.session_state.generation_text = text_input
        
        with col2:
            st.write("**Text Templates**")
            
            # Pre-defined templates
            templates = [
                "Hello! Welcome to our presentation.",
                "Thank you for watching our video.",
                "We're excited to share this with you.",
                "Don't forget to subscribe and follow us!"
            ]
            
            for i, template in enumerate(templates):
                if st.button(f"Template {i+1}", key=f"template_{i}"):
                    self.session_state.generation_text = template
                    st.rerun()
            
            st.divider()
            
            # Save/Load custom templates
            if st.button("💾 Save Template"):
                if text_input:
                    self.session_state.saved_templates.append(text_input)
                    st.success("Template saved!")
            
            # Load saved templates
            if self.session_state.saved_templates:
                saved_template = st.selectbox("Load saved", self.session_state.saved_templates)
                if st.button("Load Template"):
                    self.session_state.generation_text = saved_template
                    st.rerun()

    def render_voice_configuration(self):
        """US-4.2: Voice Configuration Part"""
        col1, col2 = st.columns(2)
        
        with col1:
            # Voice selection
            voice_options = {
                'sarah_professional': 'Sarah (Professional)',
                'michael_friendly': 'Michael (Friendly)',
                'emma_energetic': 'Emma (Energetic)',
                'david_authoritative': 'David (Authoritative)',
                'lisa_warm': 'Lisa (Warm)',
                'james_confident': 'James (Confident)'
            }
            
            selected_voice = st.selectbox("Select Voice", options=list(voice_options.keys()),
                                        format_func=lambda x: voice_options[x])
            
            # Voice preview
            if st.button("🔊 Preview Voice", key="voice_preview"):
                self.play_voice_sample(selected_voice)
        
        with col2:
            # Voice parameters
            st.write("**Voice Parameters**")
            speed = st.slider("Speech Speed", 0.5, 2.0, 1.0, 0.1)
            pitch = st.slider("Pitch", -20, 20, 0, 1)
            emotion = st.select_slider("Emotion", 
                                     options=['Sad', 'Neutral', 'Happy', 'Excited'], 
                                     value='Neutral')
        
        # Text-to-speech preview
        if self.session_state.get('generation_text') and st.button("🎵 Preview Speech"):
            self.preview_text_to_speech()
        
        return {
            'voice': selected_voice,
            'speed': speed,
            'pitch': pitch,
            'emotion': emotion.lower()
        }

    def play_voice_sample(self, voice_id):
        """Play voice sample preview"""
        # Mock voice sample playing
        with st.spinner("Loading voice sample..."):
            time.sleep(1)
            st.success(f"Playing sample for {voice_id}")
            # In real implementation, this would play actual audio

    def preview_text_to_speech(self):
        """Preview text-to-speech with selected voice"""
        with st.spinner("Generating speech preview..."):
            time.sleep(2)
            st.audio("https://www.soundjay.com/misc/sounds/bell-ringing-05.wav", format="audio/wav")
            st.success("Speech preview generated!")

    def render_generation_section(self, photo_id, voice_config):
        """US-4.3: Video Generation Dashboard - Generation Part"""
        text = self.session_state.get('generation_text', '')
        
        if not text.strip():
            st.warning("Please enter some text first!")
            return
        
        # Cost estimation
        self.render_cost_estimation(text, voice_config)
        
        # Generation button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Generate Video", type="primary", use_container_width=True):
                self.start_video_generation(photo_id, text, voice_config)

    def render_cost_estimation(self, text, voice_config):
        """Display cost estimation for video generation"""
        # Mock cost calculation
        base_cost = 0.50  # Base cost per video
        text_cost = len(text) * 0.001  # Per character
        voice_premium = 0.10 if 'professional' in voice_config['voice'] else 0.05
        
        total_cost = base_cost + text_cost + voice_premium
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Base Cost", f"${base_cost:.2f}")
        with col2:
            st.metric("Text Cost", f"${text_cost:.3f}")
        with col3:
            st.metric("Voice Premium", f"${voice_premium:.2f}")
        with col4:
            st.metric("Total Cost", f"${total_cost:.2f}", delta=f"-${0.05:.2f}")

    def start_video_generation(self, photo_id, text, voice_config):
        """Start video generation process"""
        # Create generation record
        generation_id = f"gen_{int(time.time())}"
        generation = VideoGeneration(
            id=generation_id,
            photo_name=next(p['name'] for p in self.session_state.uploaded_photos if p['id'] == photo_id),
            text=text,
            voice_type=voice_config['voice'],
            status='processing',
            progress=0,
            created_at=datetime.now(),
            estimated_completion=datetime.now() + timedelta(minutes=5)
        )
        
        # Start generation via API
        success, response = self.api_client.start_generation(photo_id, text, voice_config)
        
        if success:
            self.session_state.current_generation = generation
            self.session_state.generation_history.append(generation)
            st.success("Video generation started!")
            
            # Switch to dashboard to monitor progress
            self.session_state.current_page = 'dashboard'
            st.rerun()
        else:
            st.error(f"Failed to start generation: {response.get('message', 'Unknown error')}")

    def render_dashboard_page(self):
        """US-4.3: Video Generation Dashboard - Progress Tracking"""
        st.header("📊 Generation Dashboard")
        
        # Current generation status
        if self.session_state.current_generation:
            self.render_current_generation_status()
        
        # Queue status
        self.render_queue_status()
        
        # Recent generations
        self.render_recent_generations()
        
        # Real-time updates via WebSocket simulation
        self.setup_realtime_updates()

    def render_current_generation_status(self):
        """Render current generation progress"""
        gen = self.session_state.current_generation
        
        st.subheader("🔄 Current Generation")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Photo", gen.photo_name)
        with col2:
            st.metric("Voice", gen.voice_type.replace('_', ' ').title())
        with col3:
            status_color = {"processing": "orange", "completed": "green", "error": "red"}[gen.status]
            st.markdown(f'<span class="status-badge status-{gen.status}">🔄 {gen.status.title()}</span>', 
                       unsafe_allow_html=True)
        
        # Progress bar
        progress_placeholder = st.empty()
        
        if gen.status == 'processing':
            # Simulate progress update
            progress = gen.progress if hasattr(gen, 'progress') else 0
            progress_placeholder.progress(progress / 100)
            
            # Estimated completion
            if gen.estimated_completion:
                time_remaining = gen.estimated_completion - datetime.now()
                if time_remaining.total_seconds() > 0:
                    minutes_remaining = int(time_remaining.total_seconds() / 60)
                    st.info(f"⏱️ Estimated completion: {minutes_remaining} minutes")
        
        elif gen.status == 'completed':
            progress_placeholder.progress(100)
            st.success("✅ Generation completed!")
            
            # Video player and download options
            if gen.video_url:
                st.video(gen.video_url)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.download_button("💾 Download Video", 
                                     data=b"fake_video_data",  # In real app, fetch actual video
                                     file_name=f"{gen.photo_name}_talking.mp4",
                                     mime="video/mp4")
                with col2:
                    if st.button("🔗 Get Share Link"):
                        st.code(f"https://talkingphoto.ai/share/{gen.id}")
                with col3:
                    if st.button("🎬 Generate Another"):
                        self.session_state.current_page = 'generate'
                        st.rerun()
        
        elif gen.status == 'error':
            progress_placeholder.error("❌ Generation failed")
            st.error(f"Error: {gen.error_message}")
            
            if st.button("🔄 Retry Generation"):
                gen.status = 'processing'
                gen.progress = 0
                st.rerun()

    def render_queue_status(self):
        """Render generation queue status"""
        st.subheader("📋 Queue Status")
        
        # Mock queue data
        queue_data = [
            {"position": 1, "photo": "portrait1.jpg", "status": "processing", "eta": "2 min"},
            {"position": 2, "photo": "portrait2.jpg", "status": "queued", "eta": "7 min"},
            {"position": 3, "photo": "portrait3.jpg", "status": "queued", "eta": "12 min"},
        ]
        
        for item in queue_data:
            col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
            with col1:
                st.write(f"#{item['position']}")
            with col2:
                st.write(item['photo'])
            with col3:
                status_emoji = {"processing": "🔄", "queued": "⏳"}[item['status']]
                st.write(f"{status_emoji} {item['status'].title()}")
            with col4:
                st.write(f"ETA: {item['eta']}")

    def render_recent_generations(self):
        """Render recent generations with analytics"""
        st.subheader("📈 Recent Activity")
        
        if not self.session_state.generation_history:
            st.info("No generations yet. Start by uploading a photo!")
            return
        
        # Statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Videos", len(self.session_state.generation_history))
        with col2:
            completed = sum(1 for g in self.session_state.generation_history if g.status == 'completed')
            st.metric("Completed", completed)
        with col3:
            processing = sum(1 for g in self.session_state.generation_history if g.status == 'processing')
            st.metric("In Progress", processing)
        with col4:
            failed = sum(1 for g in self.session_state.generation_history if g.status == 'error')
            st.metric("Failed", failed)
        
        # Recent generations table
        df = pd.DataFrame([
            {
                'Photo': g.photo_name,
                'Created': g.created_at.strftime('%m/%d %H:%M'),
                'Status': g.status.title(),
                'Voice': g.voice_type.replace('_', ' ').title(),
                'Text Preview': g.text[:50] + '...' if len(g.text) > 50 else g.text
            }
            for g in reversed(self.session_state.generation_history[-10:])  # Last 10
        ])
        
        st.dataframe(df, use_container_width=True)

    def setup_realtime_updates(self):
        """Setup real-time progress updates via WebSocket simulation"""
        if not self.session_state.websocket_connected:
            # Simulate WebSocket connection
            with st.spinner("Connecting to real-time updates..."):
                time.sleep(1)
                self.session_state.websocket_connected = True
                st.success("🔗 Connected to real-time updates")
        
        # Auto-refresh for progress updates
        if self.session_state.current_generation and self.session_state.current_generation.status == 'processing':
            # Simulate progress updates
            if st.button("🔄 Refresh Status"):
                self.update_generation_progress()
                st.rerun()

    def update_generation_progress(self):
        """Update generation progress (simulation)"""
        if self.session_state.current_generation:
            gen = self.session_state.current_generation
            if gen.status == 'processing':
                # Simulate progress
                gen.progress = min(gen.progress + 10, 95)
                
                # Randomly complete generation for demo
                if gen.progress >= 95:
                    gen.status = 'completed'
                    gen.progress = 100
                    gen.video_url = "https://sample-videos.com/zip/10/mp4/SampleVideo_360x240_1mb.mp4"

    def render_history_page(self):
        """Render generation history page with search and filters"""
        st.header("📋 Generation History")
        
        if not self.session_state.generation_history:
            st.info("No generation history yet.")
            if st.button("🎬 Create Your First Video"):
                self.session_state.current_page = 'generate'
                st.rerun()
            return
        
        # Filters and search
        col1, col2, col3 = st.columns(3)
        with col1:
            search_query = st.text_input("🔍 Search", placeholder="Search by photo name or text...")
        with col2:
            status_filter = st.selectbox("Filter by Status", 
                                       ['All', 'Completed', 'Processing', 'Error'])
        with col3:
            date_filter = st.selectbox("Time Period", 
                                     ['All Time', 'Today', 'This Week', 'This Month'])
        
        # Apply filters
        filtered_history = self.filter_history(search_query, status_filter, date_filter)
        
        # Display filtered results
        for generation in filtered_history:
            self.render_generation_card(generation)

    def filter_history(self, search_query, status_filter, date_filter):
        """Filter generation history based on criteria"""
        filtered = self.session_state.generation_history
        
        # Search filter
        if search_query:
            filtered = [g for g in filtered if 
                       search_query.lower() in g.photo_name.lower() or 
                       search_query.lower() in g.text.lower()]
        
        # Status filter
        if status_filter != 'All':
            filtered = [g for g in filtered if g.status == status_filter.lower()]
        
        # Date filter
        now = datetime.now()
        if date_filter == 'Today':
            filtered = [g for g in filtered if g.created_at.date() == now.date()]
        elif date_filter == 'This Week':
            week_ago = now - timedelta(days=7)
            filtered = [g for g in filtered if g.created_at >= week_ago]
        elif date_filter == 'This Month':
            month_ago = now - timedelta(days=30)
            filtered = [g for g in filtered if g.created_at >= month_ago]
        
        return filtered

    def render_generation_card(self, generation):
        """Render a card for each generation"""
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 3, 2, 2])
            
            with col1:
                st.write(f"**{generation.photo_name}**")
                st.caption(generation.created_at.strftime('%Y-%m-%d %H:%M'))
            
            with col2:
                st.write(f"*{generation.text[:100]}...*")
                st.caption(f"Voice: {generation.voice_type.replace('_', ' ').title()}")
            
            with col3:
                status_colors = {"completed": "green", "processing": "orange", "error": "red"}
                st.markdown(f":{status_colors.get(generation.status, 'gray')}[{generation.status.title()}]")
            
            with col4:
                if generation.status == 'completed' and generation.video_url:
                    if st.button("▶️ Play", key=f"play_{generation.id}"):
                        st.video(generation.video_url)
                elif generation.status == 'error':
                    if st.button("🔄 Retry", key=f"retry_{generation.id}"):
                        generation.status = 'processing'
                        generation.progress = 0
                        st.rerun()
            
            st.divider()

    def render_account_page(self):
        """Render account management page"""
        st.header("👤 Account Settings")
        
        user_info = self.session_state.user_info or {}
        
        # Account information
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📋 Profile Information")
            with st.form("profile_form"):
                first_name = st.text_input("First Name", value=user_info.get('first_name', ''))
                last_name = st.text_input("Last Name", value=user_info.get('last_name', ''))
                email = st.text_input("Email", value=user_info.get('email', ''))
                
                if st.form_submit_button("Update Profile"):
                    st.success("Profile updated successfully!")
        
        with col2:
            st.subheader("💳 Subscription & Usage")
            st.metric("Current Plan", user_info.get('plan', 'Free'))
            st.metric("Credits Remaining", user_info.get('credits', 0))
            st.metric("Videos This Month", user_info.get('monthly_usage', 0))
            
            if st.button("⬆️ Upgrade Plan", type="primary"):
                st.info("🚀 Upgrade features coming soon!")
        
        # Usage analytics
        st.subheader("📊 Usage Analytics")
        self.render_usage_analytics()
        
        # Settings
        st.subheader("⚙️ Settings")
        col1, col2 = st.columns(2)
        
        with col1:
            st.checkbox("Email notifications", value=True)
            st.checkbox("Real-time updates", value=True)
        
        with col2:
            st.selectbox("Default voice", ['sarah_professional', 'michael_friendly'])
            st.slider("Default speech speed", 0.5, 2.0, 1.0, 0.1)

    def render_usage_analytics(self):
        """Render usage analytics charts"""
        # Mock data for demonstration
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
        usage_data = pd.DataFrame({
            'Date': dates,
            'Videos Created': [abs(int(x)) for x in (2 + 3 * np.random.randn(len(dates))).round()],
            'Credits Used': [abs(int(x)) for x in (5 + 10 * np.random.randn(len(dates))).round()]
        })
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.line(usage_data, x='Date', y='Videos Created', title='Daily Video Creation')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.bar(usage_data.tail(7), x='Date', y='Credits Used', title='Weekly Credits Usage')
            st.plotly_chart(fig, use_container_width=True)

    def logout(self):
        """Handle user logout"""
        # Clear session state
        for key in list(self.session_state.keys()):
            del self.session_state[key]
        
        self.init_session_state()
        st.rerun()


class APIClient:
    """API client for backend communication"""
    
    def __init__(self):
        self.base_url = API_BASE_URL
        self.session = requests.Session()
    
    def login(self, email: str, password: str) -> tuple[bool, dict]:
        """Login user"""
        try:
            response = self.session.post(f"{self.base_url}/auth/login", 
                                       json={"email": email, "password": password})
            if response.status_code == 200:
                data = response.json()
                self.session.headers.update({"Authorization": f"Bearer {data.get('token')}"})
                return True, data
            else:
                return False, response.json()
        except Exception as e:
            return False, {"message": str(e)}
    
    def register(self, first_name: str, last_name: str, email: str, password: str) -> tuple[bool, dict]:
        """Register new user"""
        try:
            response = self.session.post(f"{self.base_url}/auth/register", 
                                       json={
                                           "first_name": first_name,
                                           "last_name": last_name,
                                           "email": email,
                                           "password": password
                                       })
            return response.status_code == 201, response.json()
        except Exception as e:
            return False, {"message": str(e)}
    
    def upload_photo(self, file) -> tuple[bool, Optional[str]]:
        """Upload photo to backend"""
        try:
            files = {'photo': (file.name, file.getvalue(), file.type)}
            response = self.session.post(f"{self.base_url}/upload/photo", files=files)
            if response.status_code == 200:
                data = response.json()
                return True, data.get('photo_id')
            else:
                return False, None
        except Exception as e:
            return False, None
    
    def start_generation(self, photo_id: str, text: str, voice_config: dict) -> tuple[bool, dict]:
        """Start video generation"""
        try:
            response = self.session.post(f"{self.base_url}/video/generate", 
                                       json={
                                           "photo_id": photo_id,
                                           "text": text,
                                           "voice_config": voice_config
                                       })
            return response.status_code == 200, response.json()
        except Exception as e:
            return False, {"message": str(e)}


# Initialize numpy for analytics
import numpy as np

# Main application
if __name__ == "__main__":
    app = TalkingPhotoApp()
    app.run()