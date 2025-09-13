"""
TalkingPhoto AI MVP - Streamlit Components
Epic 4: User Experience & Interface Components

Specialized UI components for the TalkingPhoto AI application
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json
import base64
from PIL import Image
import io
import time
from dataclasses import dataclass

from streamlit_config import config
from streamlit_utils import StreamlitUtils, PhotoValidator, TextValidator

class PhotoUploadComponent:
    """US-4.1: Photo Upload Interface Component"""
    
    def __init__(self):
        self.utils = StreamlitUtils()
        self.validator = PhotoValidator()
    
    def render(self) -> Optional[Dict[str, Any]]:
        """Render the photo upload interface"""
        st.subheader("📤 Upload Your Photo")
        
        # Upload instructions
        with st.expander("📋 Upload Guidelines", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("""
                **✅ Good Photos:**
                - Clear, well-lit face
                - Looking at camera
                - Minimal background
                - High resolution (1024x1024+)
                """)
            with col2:
                st.markdown("""
                **❌ Avoid:**
                - Blurry or dark images
                - Multiple people
                - Sunglasses or face coverings
                - Very small faces
                """)
        
        # File uploader with drag-and-drop
        uploaded_file = st.file_uploader(
            "Choose a photo file",
            type=config.ALLOWED_EXTENSIONS,
            help=f"Maximum file size: {config.MAX_FILE_SIZE // (1024*1024)}MB",
            key="photo_uploader"
        )
        
        if uploaded_file is not None:
            return self._process_upload(uploaded_file)
        
        # Show recent uploads if available
        if st.session_state.uploaded_photos:
            st.divider()
            self._render_recent_uploads()
        
        return None
    
    def _process_upload(self, uploaded_file) -> Dict[str, Any]:
        """Process the uploaded file"""
        # Validate file size
        if uploaded_file.size > config.MAX_FILE_SIZE:
            st.error(f"File too large! Maximum size is {config.MAX_FILE_SIZE // (1024*1024)}MB")
            return None
        
        # Load and display image
        try:
            image = Image.open(uploaded_file)
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.image(image, caption=f"Preview: {uploaded_file.name}", use_column_width=True)
            
            with col2:
                st.write("**File Details:**")
                st.write(f"Filename: {uploaded_file.name}")
                st.write(f"Size: {self.utils.format_file_size(uploaded_file.size)}")
                st.write(f"Dimensions: {image.size[0]}×{image.size[1]}")
                st.write(f"Format: {image.format}")
            
            # Validate photo
            validation_result = self.validator.validate_photo(image, uploaded_file.name)
            self._display_validation_results(validation_result)
            
            if validation_result.is_valid:
                # Show upload button
                if st.button("🚀 Upload Photo", type="primary", key="upload_button"):
                    return self._upload_to_backend(uploaded_file, image, validation_result)
            
        except Exception as e:
            st.error(f"Error processing image: {str(e)}")
        
        return None
    
    def _display_validation_results(self, result):
        """Display photo validation results"""
        # Confidence score
        confidence_color = "green" if result.confidence > 0.8 else "orange" if result.confidence > 0.6 else "red"
        st.markdown(f'**Quality Score:** <span style="color: {confidence_color}; font-weight: bold;">{result.confidence:.1%}</span>', unsafe_allow_html=True)
        
        # Errors
        if result.errors:
            for error in result.errors:
                st.error(f"❌ {error}")
        
        # Warnings
        if result.warnings:
            for warning in result.warnings:
                st.warning(f"⚠️ {warning}")
        
        # Suggestions
        if result.suggestions:
            with st.expander("💡 Suggestions"):
                for suggestion in result.suggestions:
                    st.info(f"💡 {suggestion}")
    
    def _upload_to_backend(self, uploaded_file, image, validation_result) -> Dict[str, Any]:
        """Upload photo to backend with progress tracking"""
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Simulate upload progress
        for i in range(101):
            progress_bar.progress(i)
            status_text.text(f'Uploading... {i}%')
            time.sleep(0.02)  # Simulate upload time
        
        # Create photo record
        photo_data = {
            'id': f"photo_{int(time.time())}",
            'name': uploaded_file.name,
            'uploaded_at': datetime.now(),
            'size': uploaded_file.size,
            'dimensions': image.size,
            'format': image.format,
            'validation': validation_result,
            'file_path': f"uploads/{uploaded_file.name}"  # Mock path
        }
        
        # Add to session state
        st.session_state.uploaded_photos.append(photo_data)
        
        status_text.empty()
        progress_bar.empty()
        st.success("✅ Photo uploaded successfully!")
        
        # Option to proceed to generation
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🎬 Generate Video with this Photo", type="primary", key="proceed_to_generate"):
                st.session_state.current_page = 'generate'
                st.session_state.selected_photo_id = photo_data['id']
                st.rerun()
        
        return photo_data
    
    def _render_recent_uploads(self):
        """Render recent uploads section"""
        st.subheader("📋 Recent Uploads")
        
        for photo in reversed(st.session_state.uploaded_photos[-5:]):  # Show last 5
            with st.container():
                col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
                
                with col1:
                    st.write(f"**{photo['name'][:20]}...**" if len(photo['name']) > 20 else f"**{photo['name']}**")
                
                with col2:
                    st.write(f"Uploaded: {photo['uploaded_at'].strftime('%m/%d %H:%M')}")
                
                with col3:
                    quality_score = photo['validation'].confidence
                    color = "green" if quality_score > 0.8 else "orange" if quality_score > 0.6 else "red"
                    st.markdown(f'Quality: <span style="color: {color}">{quality_score:.1%}</span>', unsafe_allow_html=True)
                
                with col4:
                    if st.button("Use", key=f"use_{photo['id']}"):
                        st.session_state.selected_photo_id = photo['id']
                        st.session_state.current_page = 'generate'
                        st.rerun()
                
                st.divider()


class TextInputComponent:
    """US-4.2: Text Input & Voice Configuration - Text Part"""
    
    def __init__(self):
        self.utils = StreamlitUtils()
        self.validator = TextValidator()
    
    def render(self) -> Tuple[str, Dict[str, Any]]:
        """Render text input interface"""
        st.subheader("✍️ Enter Your Text")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            text_input = self._render_text_editor()
        
        with col2:
            self._render_text_templates()
        
        # Validation and preview
        if text_input:
            validation_result = self.validator.validate_text(text_input)
            self._display_text_validation(validation_result)
        
        return text_input, validation_result.metadata if text_input else {}
    
    def _render_text_editor(self) -> str:
        """Render the text input editor"""
        # Text area with character counter
        text = st.text_area(
            "Your message",
            height=150,
            max_chars=config.CHARACTER_LIMIT,
            placeholder="Enter the text you want your photo to speak...",
            help=f"Maximum {config.CHARACTER_LIMIT} characters",
            key="text_input"
        )
        
        # Character counter with color coding
        char_count = len(text) if text else 0
        char_percentage = (char_count / config.CHARACTER_LIMIT) * 100
        
        if char_percentage < 70:
            color = "green"
        elif char_percentage < 90:
            color = "orange"
        else:
            color = "red"
        
        st.markdown(
            f'<p style="color: {color}; text-align: right; margin-top: 0;">Characters: {char_count}/{config.CHARACTER_LIMIT}</p>', 
            unsafe_allow_html=True
        )
        
        # Text formatting options (basic)
        if text:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("📝 Add Emphasis", help="Add emphasis markers"):
                    text = f"*{text}*"
                    st.session_state.text_input = text
                    st.rerun()
            
            with col2:
                if st.button("⏸️ Add Pause", help="Add natural pause"):
                    text += "... "
                    st.session_state.text_input = text
                    st.rerun()
            
            with col3:
                if st.button("🎭 Add Emotion", help="Add emotional tone"):
                    emotion = st.selectbox("Select emotion", ["excitement", "sadness", "joy", "calm"])
                    text = f"[{emotion}] {text}"
                    st.session_state.text_input = text
                    st.rerun()
            
            with col4:
                if st.button("🔤 Clear Text"):
                    st.session_state.text_input = ""
                    st.rerun()
        
        return text
    
    def _render_text_templates(self):
        """Render text templates section"""
        st.write("**📝 Quick Templates**")
        
        # Default templates
        for i, template in enumerate(config.DEFAULT_TEMPLATES):
            if st.button(f"Template {i+1}", key=f"default_template_{i}", help=template[:50] + "..."):
                st.session_state.text_input = template
                st.rerun()
        
        st.divider()
        
        # Custom template management
        st.write("**💾 Custom Templates**")
        
        # Save current text as template
        if st.button("💾 Save Current Text", key="save_template"):
            current_text = st.session_state.get('text_input', '')
            if current_text and len(current_text.strip()) > 10:
                if 'saved_templates' not in st.session_state:
                    st.session_state.saved_templates = []
                
                st.session_state.saved_templates.append(current_text)
                st.success("Template saved!")
            else:
                st.warning("Enter at least 10 characters to save as template")
        
        # Load saved templates
        if st.session_state.get('saved_templates'):
            template_names = [f"Custom {i+1}: {self.utils.truncate_text(t, 30)}" 
                            for i, t in enumerate(st.session_state.saved_templates)]
            
            selected_template = st.selectbox(
                "Load template",
                range(len(template_names)),
                format_func=lambda x: template_names[x],
                key="template_selector"
            )
            
            if st.button("📖 Load Template", key="load_template"):
                st.session_state.text_input = st.session_state.saved_templates[selected_template]
                st.rerun()
    
    def _display_text_validation(self, result):
        """Display text validation results"""
        # Show validation status
        if result.errors:
            for error in result.errors:
                st.error(f"❌ {error}")
        
        if result.warnings:
            for warning in result.warnings:
                st.warning(f"⚠️ {warning}")
        
        # Show text statistics
        with st.expander("📊 Text Statistics"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Characters", result.metadata['character_count'])
            
            with col2:
                st.metric("Words", result.metadata['word_count'])
            
            with col3:
                st.metric("Est. Duration", f"{result.metadata.get('estimated_duration', 0):.1f}s")


class VoiceConfigComponent:
    """US-4.2: Voice Configuration Component"""
    
    def render(self) -> Dict[str, Any]:
        """Render voice configuration interface"""
        st.subheader("🎤 Voice Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            voice_config = self._render_voice_selection()
        
        with col2:
            voice_params = self._render_voice_parameters()
        
        # Voice preview
        self._render_voice_preview(voice_config)
        
        return {**voice_config, **voice_params}
    
    def _render_voice_selection(self) -> Dict[str, Any]:
        """Render voice selection interface"""
        st.write("**🎭 Select Voice**")
        
        # Voice options grouped by type
        voice_options = config.get_voice_options()
        
        # Create voice selection with preview info
        selected_voice = st.selectbox(
            "Choose voice",
            options=list(voice_options.keys()),
            format_func=lambda x: voice_options[x],
            key="voice_selector"
        )
        
        # Voice details
        voice_info = config.AVAILABLE_VOICES[selected_voice]
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Gender:** {voice_info['gender'].title()}")
            st.write(f"**Language:** {voice_info['language']}")
        
        with col2:
            st.write(f"**Style:** {voice_info['style'].title()}")
            premium_badge = "⭐ Premium" if voice_info['premium'] else "🆓 Free"
            st.write(f"**Type:** {premium_badge}")
        
        return {'voice': selected_voice, 'voice_info': voice_info}
    
    def _render_voice_parameters(self) -> Dict[str, Any]:
        """Render voice parameter controls"""
        st.write("**⚙️ Voice Parameters**")
        
        # Speech speed
        speed = st.slider(
            "Speech Speed",
            min_value=0.5,
            max_value=2.0,
            value=1.0,
            step=0.1,
            help="Adjust how fast the voice speaks"
        )
        
        # Pitch adjustment
        pitch = st.slider(
            "Pitch",
            min_value=-20,
            max_value=20,
            value=0,
            step=1,
            help="Adjust voice pitch (negative = lower, positive = higher)"
        )
        
        # Emotion/Style
        emotion = st.select_slider(
            "Emotion",
            options=['Sad', 'Neutral', 'Happy', 'Excited'],
            value='Neutral',
            help="Choose the emotional tone"
        )
        
        # Volume
        volume = st.slider(
            "Volume",
            min_value=0.1,
            max_value=1.0,
            value=0.8,
            step=0.1,
            help="Audio volume level"
        )
        
        return {
            'speed': speed,
            'pitch': pitch,
            'emotion': emotion.lower(),
            'volume': volume
        }
    
    def _render_voice_preview(self, voice_config):
        """Render voice preview section"""
        st.write("**🔊 Voice Preview**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Sample text for preview
            sample_text = st.text_input(
                "Preview text",
                value="Hello, this is how I will sound in your video.",
                key="voice_preview_text"
            )
        
        with col2:
            # Preview button
            if st.button("🎵 Preview Voice", key="preview_voice"):
                self._play_voice_preview(sample_text, voice_config)
        
        # Current text preview
        current_text = st.session_state.get('text_input', '')
        if current_text:
            if st.button("🎬 Preview with Your Text", key="preview_user_text"):
                self._play_voice_preview(current_text, voice_config)
    
    def _play_voice_preview(self, text, voice_config):
        """Play voice preview (mock implementation)"""
        with st.spinner("Generating voice preview..."):
            time.sleep(2)  # Simulate generation time
        
        # Mock audio player
        st.success(f"🔊 Playing preview with {voice_config['voice_info']['name']}")
        
        # In real implementation, this would generate and play actual audio
        # st.audio(audio_data, format="audio/wav")
        
        # Show preview info
        st.info(f"""
        **Preview Settings:**
        - Voice: {voice_config['voice_info']['name']}
        - Speed: {voice_config.get('speed', 1.0)}x
        - Pitch: {voice_config.get('pitch', 0):+d}
        - Emotion: {voice_config.get('emotion', 'neutral').title()}
        """)


class GenerationProgressComponent:
    """US-4.3: Video Generation Progress Component"""
    
    def render(self, generation_data: Dict[str, Any]):
        """Render generation progress interface"""
        st.subheader("🎬 Video Generation Progress")
        
        # Current generation status
        self._render_current_status(generation_data)
        
        # Progress tracking
        self._render_progress_tracking(generation_data)
        
        # Queue information
        self._render_queue_status()
        
        # Real-time updates
        self._setup_realtime_updates()
    
    def _render_current_status(self, generation_data):
        """Render current generation status"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Photo", generation_data.get('photo_name', 'N/A'))
        
        with col2:
            voice_type = generation_data.get('voice_type', '').replace('_', ' ').title()
            st.metric("Voice", voice_type)
        
        with col3:
            status = generation_data.get('status', 'unknown')
            status_badge = StreamlitUtils.create_status_badge(status)
            st.markdown(f"**Status:** {status_badge}", unsafe_allow_html=True)
        
        with col4:
            progress = generation_data.get('progress', 0)
            st.metric("Progress", f"{progress}%")
    
    def _render_progress_tracking(self, generation_data):
        """Render detailed progress tracking"""
        status = generation_data.get('status', 'unknown')
        progress = generation_data.get('progress', 0)
        
        # Progress bar
        progress_html = StreamlitUtils.create_progress_bar(progress, status)
        st.markdown(progress_html, unsafe_allow_html=True)
        
        # Status-specific information
        if status == 'processing':
            self._render_processing_status(generation_data)
        elif status == 'completed':
            self._render_completed_status(generation_data)
        elif status == 'error':
            self._render_error_status(generation_data)
        elif status == 'queued':
            self._render_queued_status(generation_data)
    
    def _render_processing_status(self, generation_data):
        """Render processing status information"""
        col1, col2 = st.columns(2)
        
        with col1:
            # Estimated completion time
            estimated_completion = generation_data.get('estimated_completion')
            if estimated_completion:
                time_remaining = estimated_completion - datetime.now()
                if time_remaining.total_seconds() > 0:
                    minutes_remaining = int(time_remaining.total_seconds() / 60)
                    st.info(f"⏱️ Estimated completion: {minutes_remaining} minutes")
        
        with col2:
            # Processing stage
            stages = ['Analyzing photo', 'Generating speech', 'Creating video', 'Finalizing']
            current_stage = min(int((generation_data.get('progress', 0) / 100) * len(stages)), len(stages) - 1)
            st.info(f"🔄 Stage: {stages[current_stage]}")
        
        # Live progress updates
        if st.button("🔄 Refresh Status", key="refresh_progress"):
            # Simulate progress update
            if generation_data['progress'] < 100:
                generation_data['progress'] = min(generation_data['progress'] + 10, 95)
            st.rerun()
    
    def _render_completed_status(self, generation_data):
        """Render completed status with download options"""
        st.success("✅ Video generation completed successfully!")
        
        # Video player (mock)
        video_url = generation_data.get('video_url')
        if video_url:
            st.video(video_url)
        else:
            st.info("🎬 Video player will appear here once processing is complete")
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Download Video", type="primary", key="download_video"):
                # Mock download
                st.download_button(
                    label="📥 Download MP4",
                    data=b"mock_video_data",
                    file_name=f"{generation_data.get('photo_name', 'video')}_talking.mp4",
                    mime="video/mp4"
                )
        
        with col2:
            if st.button("🔗 Get Share Link", key="get_share_link"):
                share_link = f"https://talkingphoto.ai/share/{generation_data.get('id')}"
                st.code(share_link)
                st.info("Link copied to clipboard!")
        
        with col3:
            if st.button("🎬 Create Another", key="create_another"):
                st.session_state.current_page = 'generate'
                st.rerun()
    
    def _render_error_status(self, generation_data):
        """Render error status with retry options"""
        error_message = generation_data.get('error_message', 'Unknown error occurred')
        st.error(f"❌ Generation failed: {error_message}")
        
        # Error details
        with st.expander("🔍 Error Details"):
            st.write("**Error Type:** Processing Error")
            st.write(f"**Message:** {error_message}")
            st.write(f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            st.write("**Suggestion:** Please try again or contact support if the issue persists.")
        
        # Retry button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔄 Retry Generation", type="primary", key="retry_generation"):
                generation_data['status'] = 'processing'
                generation_data['progress'] = 0
                generation_data['error_message'] = None
                st.rerun()
    
    def _render_queued_status(self, generation_data):
        """Render queued status information"""
        queue_position = generation_data.get('queue_position', 1)
        estimated_wait = generation_data.get('estimated_wait', 5)
        
        st.info(f"⏳ Your video is in queue (Position: {queue_position})")
        st.write(f"Estimated wait time: {estimated_wait} minutes")
        
        # Queue progress
        queue_progress = max(0, 100 - (queue_position * 20))
        progress_html = StreamlitUtils.create_progress_bar(queue_progress, 'queued')
        st.markdown(progress_html, unsafe_allow_html=True)
    
    def _render_queue_status(self):
        """Render overall queue status"""
        st.subheader("📋 Queue Status")
        
        # Mock queue data
        queue_data = [
            {"position": 1, "photo": "portrait1.jpg", "status": "processing", "eta": "2 min"},
            {"position": 2, "photo": "portrait2.jpg", "status": "queued", "eta": "7 min"},
            {"position": 3, "photo": "portrait3.jpg", "status": "queued", "eta": "12 min"},
        ]
        
        # Queue table
        df = pd.DataFrame(queue_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    def _setup_realtime_updates(self):
        """Setup real-time progress updates"""
        if not st.session_state.get('websocket_connected', False):
            with st.spinner("Connecting to real-time updates..."):
                time.sleep(1)
                st.session_state.websocket_connected = True
                st.success("🔗 Connected to real-time updates")
        
        # Auto-refresh toggle
        auto_refresh = st.checkbox("🔄 Auto-refresh progress", value=True, key="auto_refresh")
        
        if auto_refresh:
            # Use st.empty() for live updates
            placeholder = st.empty()
            with placeholder.container():
                st.info("Real-time updates active. Progress will update automatically.")


class AnalyticsComponent:
    """Analytics and metrics component"""
    
    def render_user_analytics(self):
        """Render user analytics dashboard"""
        st.subheader("📊 Your Analytics")
        
        # Generate mock data
        analytics_data = self._generate_mock_analytics()
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            metric_html = StreamlitUtils.create_metric_card(
                "Videos Created", 
                str(analytics_data['total_videos']), 
                f"+{analytics_data['videos_this_week']} this week"
            )
            st.markdown(metric_html, unsafe_allow_html=True)
        
        with col2:
            metric_html = StreamlitUtils.create_metric_card(
                "Total Views", 
                f"{analytics_data['total_views']:,}", 
                f"+{analytics_data['views_this_week']:,} this week"
            )
            st.markdown(metric_html, unsafe_allow_html=True)
        
        with col3:
            metric_html = StreamlitUtils.create_metric_card(
                "Avg. Quality", 
                f"{analytics_data['avg_quality']:.1%}", 
                "+2% vs last month"
            )
            st.markdown(metric_html, unsafe_allow_html=True)
        
        with col4:
            metric_html = StreamlitUtils.create_metric_card(
                "Credits Used", 
                f"{analytics_data['credits_used']}/{analytics_data['credits_total']}", 
                f"{analytics_data['credits_remaining']} remaining"
            )
            st.markdown(metric_html, unsafe_allow_html=True)
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_creation_timeline(analytics_data)
        
        with col2:
            self._render_voice_usage_chart(analytics_data)
    
    def _generate_mock_analytics(self) -> Dict[str, Any]:
        """Generate mock analytics data"""
        return {
            'total_videos': 15,
            'videos_this_week': 3,
            'total_views': 1250,
            'views_this_week': 180,
            'avg_quality': 0.87,
            'credits_used': 45,
            'credits_total': 50,
            'credits_remaining': 5,
            'creation_dates': pd.date_range('2024-01-01', periods=15, freq='3D'),
            'voice_usage': {
                'Sarah (Professional)': 6,
                'Michael (Friendly)': 4,
                'Emma (Energetic)': 3,
                'David (Authoritative)': 2
            }
        }
    
    def _render_creation_timeline(self, data):
        """Render video creation timeline"""
        st.write("**📈 Creation Timeline**")
        
        # Mock timeline data
        timeline_df = pd.DataFrame({
            'Date': data['creation_dates'],
            'Videos': [1, 0, 1, 2, 0, 1, 1, 0, 2, 1, 1, 0, 1, 2, 1]
        })
        
        fig = px.line(timeline_df, x='Date', y='Videos', 
                      title='Videos Created Over Time')
        fig.update_traces(line_color='#667eea')
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_voice_usage_chart(self, data):
        """Render voice usage distribution"""
        st.write("**🎤 Voice Usage**")
        
        fig = px.pie(
            values=list(data['voice_usage'].values()),
            names=list(data['voice_usage'].keys()),
            title='Voice Selection Distribution'
        )
        fig.update_traces(
            textposition='inside', 
            textinfo='percent+label',
            marker_colors=['#667eea', '#764ba2', '#f093fb', '#f5576c']
        )
        st.plotly_chart(fig, use_container_width=True)


class CostEstimatorComponent:
    """Cost estimation component"""
    
    def render(self, text_length: int, voice_config: Dict[str, Any], quality: str = 'standard') -> float:
        """Render cost estimation"""
        st.subheader("💰 Cost Estimation")
        
        # Calculate costs
        costs = self._calculate_detailed_costs(text_length, voice_config, quality)
        
        # Cost breakdown
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Cost Breakdown:**")
            for item, cost in costs['breakdown'].items():
                st.write(f"• {item}: ${cost:.3f}")
            
            st.divider()
            st.write(f"**Total: ${costs['total']:.2f}**")
        
        with col2:
            # Cost comparison chart
            self._render_cost_comparison(costs)
        
        # Credits information
        user_credits = st.session_state.get('user_info', {}).get('credits', 0)
        credits_needed = max(1, int(costs['total'] * 2))  # Assuming 1 credit = $0.50
        
        if user_credits >= credits_needed:
            st.success(f"✅ You have {user_credits} credits. This will use {credits_needed} credits.")
        else:
            st.warning(f"⚠️ You need {credits_needed} credits but only have {user_credits}. Please upgrade your plan.")
        
        return costs['total']
    
    def _calculate_detailed_costs(self, text_length: int, voice_config: Dict[str, Any], quality: str) -> Dict[str, Any]:
        """Calculate detailed cost breakdown"""
        base_cost = config.COST_STRUCTURE['base_cost']
        character_cost = text_length * config.COST_STRUCTURE['character_cost']
        
        # Voice premium
        voice_premium = 0.0
        if voice_config.get('voice_info', {}).get('premium', False):
            voice_premium = base_cost * (config.COST_STRUCTURE['premium_voice_multiplier'] - 1)
        
        # Quality premium
        quality_premium = 0.0
        if quality == 'hd':
            quality_premium = base_cost * (config.COST_STRUCTURE['hd_quality_multiplier'] - 1)
        elif quality == '4k':
            quality_premium = base_cost * (config.COST_STRUCTURE['4k_quality_multiplier'] - 1)
        
        total = base_cost + character_cost + voice_premium + quality_premium
        
        return {
            'total': round(total, 2),
            'breakdown': {
                'Base Cost': base_cost,
                'Text Processing': character_cost,
                'Premium Voice': voice_premium,
                'Quality Enhancement': quality_premium
            }
        }
    
    def _render_cost_comparison(self, costs):
        """Render cost comparison chart"""
        st.write("**Cost Distribution:**")
        
        fig = px.pie(
            values=list(costs['breakdown'].values()),
            names=list(costs['breakdown'].keys()),
            title='Cost Breakdown'
        )
        st.plotly_chart(fig, use_container_width=True)