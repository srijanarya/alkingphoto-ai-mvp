"""
TalkingPhoto AI MVP - Create Video Component

Main feature component for video generation interface.
Handles photo upload, text input, and video generation process.
"""

import streamlit as st
import time
from typing import Optional, Dict, Any
from ui.validators import FormValidator, FileValidator, TextValidator
from core.session import SessionManager
from core.config import config


class CreateVideoComponent:
    """Main video creation interface component"""
    
    def __init__(self):
        """Initialize the create video component"""
        self.upload_config = config.get_file_upload_config()
        self.processing_config = config.get_processing_config()
    
    def render(self) -> None:
        """Render the main create video interface"""
        
        # Check if user has credits
        if not SessionManager.has_credits():
            self._render_no_credits_state()
            return
        
        # Render main interface
        self._render_credits_banner()
        self._render_upload_interface()
    
    def _render_no_credits_state(self) -> None:
        """Render interface when user has no credits"""
        st.markdown("""
        <div class="custom-card" style="text-align: center; background: #fed7d7; border: 2px solid #e53e3e;">
            <h3 style="color: #c53030; margin-bottom: 1rem;">❌ No Credits Available</h3>
            <p style="color: #742a2a; margin-bottom: 1.5rem;">
                You've used all your free credits. Purchase more credits to continue creating videos.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🛒 View Pricing Plans", type="primary", use_container_width=True):
                st.switch_page("pricing")  # This would switch to pricing tab in real implementation
        
        # Show what they accomplished
        generation_count = SessionManager.get_generation_count()
        if generation_count > 0:
            st.success(f"🎉 You successfully created {generation_count} video{'s' if generation_count > 1 else ''} in this session!")
    
    def _render_credits_banner(self) -> None:
        """Render credits information banner"""
        credits = SessionManager.get_credits()
        
        st.markdown(f"""
        <div class="credit-display" style="text-align: center; margin-bottom: 2rem;">
            <h3>✨ You have {credits} free credit{'s' if credits != 1 else ''} remaining</h3>
            <p style="margin: 0.5rem 0 0 0; font-size: 1rem; opacity: 0.9;">
                Create your first AI talking photo video!
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_upload_interface(self) -> None:
        """Render the main upload and text input interface"""
        
        st.markdown("""
        <div class="custom-card">
            <h3 style="color: #2d3748; margin-bottom: 1rem;">📸 Upload Photo & Add Text</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Two-column layout for desktop, single column for mobile
        col1, col2 = st.columns([1, 1], gap="large")
        
        with col1:
            self._render_photo_upload()
        
        with col2:
            self._render_text_input()
        
        # Generation button and controls
        self._render_generation_controls()
    
    def _render_photo_upload(self) -> None:
        """Render photo upload section"""
        st.markdown("#### 📸 Upload Your Photo")
        st.markdown(f"""
        <small style="color: #718096;">
        Supported formats: JPEG, PNG • Max size: 200MB
        </small>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Choose a photo",
            type=['png', 'jpg', 'jpeg'],
            key="photo_upload",
            help="Upload a clear photo of a person's face for best results"
        )
        
        if uploaded_file:
            # Validate file
            is_valid, error_message = FileValidator.validate_file(uploaded_file)
            
            if is_valid:
                # Show uploaded image
                st.image(uploaded_file, caption="Uploaded Photo", use_container_width=True)
                
                # Show file info
                file_info = FileValidator.get_file_info(uploaded_file)
                st.success(f"✅ Photo uploaded successfully ({file_info['size_mb']}MB)")
                
                # Store in session state for processing
                st.session_state.uploaded_photo = uploaded_file
                st.session_state.photo_file_info = file_info
                
            else:
                st.error(f"❌ {error_message}")
                st.session_state.uploaded_photo = None
        
        else:
            st.session_state.uploaded_photo = None
            
            # Show upload tips
            st.markdown("""
            <div style="background: #edf2f7; padding: 1rem; border-radius: 8px; margin-top: 1rem;">
                <strong>📋 Tips for best results:</strong>
                <ul style="margin: 0.5rem 0 0 0; padding-left: 1.2rem;">
                    <li>Use a clear, high-quality photo</li>
                    <li>Ensure the face is clearly visible</li>
                    <li>Good lighting works best</li>
                    <li>Avoid blurry or pixelated images</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    
    def _render_text_input(self) -> None:
        """Render text input section"""
        st.markdown("#### 💬 Enter Text to Speak")
        st.markdown(f"""
        <small style="color: #718096;">
        {self.upload_config['min_text_length']}-{self.upload_config['max_text_length']} characters
        </small>
        """, unsafe_allow_html=True)
        
        text_input = st.text_area(
            "What should your photo say?",
            height=150,
            key="video_text_input",
            placeholder="Enter the text you want your photo to speak... Be creative!",
            help=f"Enter between {self.upload_config['min_text_length']} and {self.upload_config['max_text_length']} characters"
        )
        
        if text_input:
            # Validate text
            is_valid, error_message = TextValidator.validate_text(text_input)
            
            if is_valid:
                # Show text stats
                text_stats = TextValidator.get_text_stats(text_input)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Characters", text_stats['length'])
                with col2:
                    st.metric("Words", text_stats['words'])
                with col3:
                    st.metric("Est. Duration", text_stats['estimated_duration'])
                
                st.success("✅ Text looks good!")
                
                # Store text stats in session state
                st.session_state.text_stats = text_stats
                st.session_state.video_text_valid = True
                
            else:
                st.error(f"❌ {error_message}")
                if 'video_text_valid' in st.session_state:
                    del st.session_state.video_text_valid
        
        else:
            if 'video_text_valid' in st.session_state:
                del st.session_state.video_text_valid
            
            # Show text examples
            st.markdown("""
            <div style="background: #edf2f7; padding: 1rem; border-radius: 8px; margin-top: 1rem;">
                <strong>💡 Example texts:</strong>
                <ul style="margin: 0.5rem 0 0 0; padding-left: 1.2rem;">
                    <li>"Hello! Welcome to my channel. Today I'll show you something amazing!"</li>
                    <li>"Happy birthday! Hope you have a wonderful day filled with joy."</li>
                    <li>"Thank you for watching. Don't forget to like and subscribe!"</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    
    def _render_generation_controls(self) -> None:
        """Render video generation controls and button"""
        
        # Check if both inputs are ready
        has_photo = hasattr(st.session_state, 'uploaded_photo') and st.session_state.uploaded_photo is not None
        has_text = hasattr(st.session_state, 'video_text_input') and st.session_state.video_text_input and hasattr(st.session_state, 'video_text_valid') and st.session_state.video_text_valid
        can_generate = has_photo and has_text and SessionManager.has_credits()
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if can_generate:
                # Show generation preview
                st.markdown("""
                <div style="background: #f0fff4; border: 2px solid #38a169; border-radius: 10px; padding: 1rem; text-align: center; margin-bottom: 1rem;">
                    <h4 style="color: #2f855a; margin: 0;">🎬 Ready to Generate!</h4>
                    <p style="color: #276749; margin: 0.5rem 0 0 0;">This will use 1 credit</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Generation button
                if st.button("🚀 Generate Talking Video", type="primary", use_container_width=True, key="generate_video"):
                    self._handle_video_generation()
            
            else:
                # Show what's missing
                missing_items = []
                if not has_photo:
                    missing_items.append("📸 Photo")
                if not has_text:
                    missing_items.append("💬 Text")
                if not SessionManager.has_credits():
                    missing_items.append("💳 Credits")
                
                st.markdown(f"""
                <div style="background: #fffaf0; border: 2px solid #ed8936; border-radius: 10px; padding: 1rem; text-align: center;">
                    <h4 style="color: #c05621; margin: 0;">⚠️ Missing Requirements</h4>
                    <p style="color: #9c4221; margin: 0.5rem 0 0 0;">
                        Please provide: {", ".join(missing_items)}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Disabled button
                st.button("🚀 Generate Talking Video", type="primary", disabled=True, use_container_width=True)
    
    def _handle_video_generation(self) -> None:
        """Handle the video generation process"""
        
        # Start processing
        SessionManager.start_processing()
        
        try:
            # Use credit
            if not SessionManager.use_credit():
                st.error("❌ Unable to use credit. Please refresh and try again.")
                return
            
            # Get form data
            photo = st.session_state.uploaded_photo
            text = st.session_state.video_text_input
            
            # Final validation
            is_valid, error_message, validation_data = FormValidator.validate_creation_form(photo, text)
            
            if not is_valid:
                st.error(f"❌ Validation failed: {error_message}")
                # Refund credit on validation failure
                SessionManager.add_credits(1)
                return
            
            # Mock video generation process
            self._render_generation_progress(validation_data)
            
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
            # Refund credit on error
            SessionManager.add_credits(1)
            SessionManager.set_error(f"Generation failed: {str(e)}")
            
        finally:
            SessionManager.stop_processing()
    
    def _render_generation_progress(self, validation_data: Dict[str, Any]) -> None:
        """
        Render video generation progress
        
        Args:
            validation_data: Validated form data
        """
        
        st.markdown("### 🎬 Generating Your Talking Video")
        
        # Progress container
        progress_container = st.container()
        
        with progress_container:
            # Initialize progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Simulate progress steps
            steps = [
                (0, "🔍 Analyzing your photo..."),
                (20, "🧠 Processing facial features..."),
                (40, "💬 Preparing text-to-speech..."),
                (60, "🎯 Mapping speech to face..."),
                (80, "🎬 Generating video frames..."),
                (95, "✨ Finalizing your video..."),
                (100, "🎉 Video generation complete!")
            ]
            
            for progress, message in steps:
                progress_bar.progress(progress)
                status_text.markdown(f"**{message}**")
                time.sleep(0.5)  # Simulate processing time
        
        # Show completion
        self._render_generation_success(validation_data)
    
    def _render_generation_success(self, validation_data: Dict[str, Any]) -> None:
        """
        Render successful generation result
        
        Args:
            validation_data: Validation data from the form
        """
        
        # Add to session history
        SessionManager.add_generation(
            validation_data['file_info'],
            validation_data['text_stats']
        )
        
        # Success message
        st.success("🎉 Your talking video has been generated successfully!")
        st.balloons()
        
        # Mock video player (in real implementation, this would show actual video)
        st.markdown("""
        <div style="background: #1a202c; border-radius: 10px; padding: 2rem; text-align: center; color: white; margin: 2rem 0;">
            <h3>🎬 Your Talking Photo Video</h3>
            <div style="background: #2d3748; border-radius: 8px; padding: 3rem; margin: 1rem 0;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">▶️</div>
                <p>Video Player (Mock)</p>
                <p style="color: #a0aec0; font-size: 0.9rem;">
                    In the full version, your generated video would appear here
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📥 Download Video", use_container_width=True):
                st.info("💡 Download feature will be available in the full version!")
        
        with col2:
            if st.button("📤 Share Video", use_container_width=True):
                st.info("💡 Share feature will be available in the full version!")
        
        with col3:
            if st.button("🎬 Create Another", use_container_width=True):
                # Clear form for new generation
                for key in ['uploaded_photo', 'video_text_input', 'video_text_valid', 'photo_file_info', 'text_stats']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
        
        # Show generation stats
        st.markdown("### 📊 Generation Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📸 Photo Information:**")
            file_info = validation_data['file_info']
            st.json({
                "Filename": file_info['name'],
                "Size": f"{file_info['size_mb']} MB",
                "Format": file_info['type']
            })
        
        with col2:
            st.markdown("**💬 Text Statistics:**")
            text_stats = validation_data['text_stats']
            st.json({
                "Characters": text_stats['length'],
                "Words": text_stats['words'],
                "Estimated Duration": text_stats['estimated_duration']
            })