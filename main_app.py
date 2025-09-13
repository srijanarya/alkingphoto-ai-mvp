"""
TalkingPhoto AI MVP - Main Streamlit Application
Epic 4: User Experience & Interface Implementation

Comprehensive Streamlit frontend implementing all Epic 4 user stories:
- US-4.1: Photo Upload Interface (8 pts)
- US-4.2: Text Input & Voice Configuration (13 pts)  
- US-4.3: Video Generation Dashboard (21 pts)
"""

import streamlit as st
import logging
import sys
import os
from pathlib import Path

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from streamlit_config import config
    from streamlit_utils import StreamlitUtils, SessionManager
    from components import (
        PhotoUploadComponent, 
        TextInputComponent, 
        VoiceConfigComponent, 
        GenerationProgressComponent,
        AnalyticsComponent,
        CostEstimatorComponent
    )
except ImportError as e:
    st.error(f"Import error: {str(e)}")
    st.stop()

# Configure Streamlit page
st.set_page_config(**config.get_streamlit_config())

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TalkingPhotoApp:
    """Main TalkingPhoto AI Streamlit Application"""
    
    def __init__(self):
        # Initialize utilities and session management
        self.utils = StreamlitUtils()
        self.session_manager = SessionManager()
        
        # Initialize components
        self.photo_upload = PhotoUploadComponent()
        self.text_input = TextInputComponent()
        self.voice_config = VoiceConfigComponent()
        self.generation_progress = GenerationProgressComponent()
        self.analytics = AnalyticsComponent()
        self.cost_estimator = CostEstimatorComponent()
        
        # Initialize session state
        self.session_manager.init_session_state()
    
    def run(self):
        """Main application entry point"""
        try:
            # Apply custom styling
            self.utils.apply_custom_css()
            
            # Check session expiration
            if self.session_manager.is_session_expired():
                self._handle_session_expiry()
                return
            
            # Update activity timestamp
            self.session_manager.update_activity()
            
            # Route to appropriate page
            if not st.session_state.authenticated:
                self._render_auth_page()
            else:
                self._render_main_app()
                
        except Exception as e:
            logger.error(f"Application error: {str(e)}")
            st.error("An unexpected error occurred. Please refresh the page.")
    
    def _handle_session_expiry(self):
        """Handle session expiration"""
        st.warning("Your session has expired. Please sign in again.")
        self.session_manager.clear_session()
        st.rerun()
    
    def _render_auth_page(self):
        """Render authentication page with modern design"""
        # Hero section
        st.markdown("""
        <div style="text-align: center; padding: 3rem 0;">
            <h1 style="font-size: 3rem; margin-bottom: 1rem;">🎬 TalkingPhoto AI MVP</h1>
            <p style="font-size: 1.2rem; color: #666; margin-bottom: 2rem;">
                Transform Your Photos into Engaging Videos with AI
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Authentication forms
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            # Feature highlights
            st.markdown("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        color: white; padding: 2rem; border-radius: 12px; margin-bottom: 2rem;">
                <h3 style="text-align: center; margin-bottom: 1rem;">✨ Key Features</h3>
                <ul style="list-style: none; padding: 0;">
                    <li style="padding: 0.5rem 0;">📤 <strong>Easy Upload:</strong> Drag & drop photo upload with validation</li>
                    <li style="padding: 0.5rem 0;">🎤 <strong>Premium Voices:</strong> 6+ professional voice options</li>
                    <li style="padding: 0.5rem 0;">🎬 <strong>Real-time Progress:</strong> Live generation tracking</li>
                    <li style="padding: 0.5rem 0;">📱 <strong>Mobile Ready:</strong> Works perfectly on all devices</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            # Authentication tabs
            auth_tab1, auth_tab2 = st.tabs(["🔐 Sign In", "📝 Create Account"])
            
            with auth_tab1:
                self._render_login_form()
            
            with auth_tab2:
                self._render_register_form()
    
    def _render_login_form(self):
        """Render enhanced login form"""
        with st.form("login_form", clear_on_submit=False):
            st.subheader("Welcome Back!")
            
            email = st.text_input(
                "Email Address",
                placeholder="your.email@example.com",
                help="Enter your registered email address"
            )
            
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                help="Your account password"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                remember_me = st.checkbox("Remember me")
            with col2:
                forgot_password = st.button("Forgot password?", help="Reset your password")
            
            submit = st.form_submit_button("🚀 Sign In", type="primary", use_container_width=True)
            
            if submit and email and password:
                self._handle_login(email, password, remember_me)
            
            if forgot_password:
                st.info("Password reset functionality will be available soon!")
    
    def _render_register_form(self):
        """Render enhanced registration form"""
        with st.form("register_form", clear_on_submit=False):
            st.subheader("Create Your Account")
            
            col1, col2 = st.columns(2)
            
            with col1:
                first_name = st.text_input("First Name", placeholder="John")
            
            with col2:
                last_name = st.text_input("Last Name", placeholder="Doe")
            
            email = st.text_input(
                "Email Address",
                placeholder="john.doe@example.com",
                help="We'll send you a verification email"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Strong password",
                    help="At least 8 characters with mix of letters, numbers"
                )
            
            with col2:
                confirm_password = st.text_input(
                    "Confirm Password",
                    type="password",
                    placeholder="Confirm password"
                )
            
            # Plan selection
            st.write("**Choose Your Plan:**")
            plan_col1, plan_col2, plan_col3 = st.columns(3)
            
            with plan_col1:
                if st.radio("Free Plan", [True], key="free_plan"):
                    selected_plan = "free"
                st.caption("✅ 5 videos/month\n✅ Basic voices\n✅ Standard quality")
            
            with plan_col2:
                if st.radio("Pro Plan", [False], key="pro_plan"):
                    selected_plan = "pro"
                st.caption("⭐ 50 videos/month\n⭐ Premium voices\n⭐ HD quality")
            
            with plan_col3:
                if st.radio("Enterprise", [False], key="enterprise_plan"):
                    selected_plan = "enterprise"
                st.caption("🏆 200 videos/month\n🏆 All features\n🏆 API access")
            
            # Terms and conditions
            terms_accepted = st.checkbox(
                "I agree to the Terms of Service and Privacy Policy",
                help="Required to create an account"
            )
            
            newsletter = st.checkbox(
                "Subscribe to updates and tips (optional)",
                value=True
            )
            
            submit = st.form_submit_button("🎉 Create Account", type="primary", use_container_width=True)
            
            if submit:
                self._handle_registration(
                    first_name, last_name, email, password, confirm_password,
                    selected_plan if 'selected_plan' in locals() else 'free',
                    terms_accepted, newsletter
                )
    
    def _handle_login(self, email: str, password: str, remember_me: bool = False):
        """Handle user login"""
        # Input validation
        if not email or not password:
            st.error("Please enter both email and password")
            return
        
        # Mock authentication (in real implementation, call backend API)
        with st.spinner("Signing you in..."):
            import time
            time.sleep(1)  # Simulate API call
        
        # Simulate successful login
        user_data = {
            'id': 'user_123',
            'name': email.split('@')[0].replace('.', ' ').title(),
            'email': email,
            'plan': 'pro',
            'credits': 45,
            'profile_picture': None
        }
        
        # Update session state
        st.session_state.authenticated = True
        st.session_state.user_token = 'mock_jwt_token'
        st.session_state.user_info = user_data
        
        st.success("Successfully signed in! Welcome back!")
        time.sleep(1)
        st.rerun()
    
    def _handle_registration(self, first_name: str, last_name: str, email: str, 
                           password: str, confirm_password: str, plan: str,
                           terms_accepted: bool, newsletter: bool):
        """Handle user registration"""
        # Validation
        errors = []
        
        if not all([first_name, last_name, email, password, confirm_password]):
            errors.append("Please fill in all required fields")
        
        if password != confirm_password:
            errors.append("Passwords do not match")
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters")
        
        if not terms_accepted:
            errors.append("You must accept the Terms of Service")
        
        if '@' not in email:
            errors.append("Please enter a valid email address")
        
        if errors:
            for error in errors:
                st.error(error)
            return
        
        # Mock registration
        with st.spinner("Creating your account..."):
            time.sleep(2)  # Simulate API call
        
        st.success("Account created successfully! Please sign in to continue.")
        
        # Show welcome message
        st.balloons()
        
        st.info(f"""
        🎉 **Welcome to TalkingPhoto AI, {first_name}!**
        
        Your {plan.title()} plan is now active. You can now:
        - Upload photos and create videos
        - Access {'premium' if plan != 'free' else 'basic'} voice options
        - Track your generation progress in real-time
        
        Please switch to the "Sign In" tab to get started!
        """)
    
    def _render_main_app(self):
        """Render main application interface"""
        # Header with user info
        self._render_header()
        
        # Sidebar navigation
        self._render_sidebar()
        
        # Main content area
        self._render_main_content()
        
        # Footer
        self._render_footer()
    
    def _render_header(self):
        """Render application header"""
        header_col1, header_col2, header_col3 = st.columns([2, 3, 2])
        
        with header_col1:
            st.markdown("### 🎬 TalkingPhoto AI")
        
        with header_col2:
            # Status indicators
            self._render_status_indicators()
        
        with header_col3:
            self._render_user_menu()
        
        st.divider()
    
    def _render_status_indicators(self):
        """Render real-time status indicators"""
        if st.session_state.get('current_generation'):
            gen = st.session_state.current_generation
            
            if hasattr(gen, 'status'):
                if gen.status == 'processing':
                    progress = getattr(gen, 'progress', 0)
                    st.info(f"🔄 Generating video... {progress}%")
                elif gen.status == 'completed':
                    st.success("✅ Video generated successfully!")
                elif gen.status == 'error':
                    error_msg = getattr(gen, 'error_message', 'Unknown error')
                    st.error(f"❌ Generation failed: {error_msg}")
    
    def _render_user_menu(self):
        """Render user menu and account info"""
        user_info = st.session_state.get('user_info', {})
        user_name = user_info.get('name', 'User')
        
        # User greeting and menu
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.write(f"👋 Welcome, **{user_name}**!")
            
            # Quick stats
            plan = user_info.get('plan', 'Free')
            credits = user_info.get('credits', 0)
            st.caption(f"{plan} Plan • {credits} credits remaining")
        
        with col2:
            if st.button("⚙️", help="Account Settings"):
                st.session_state.current_page = 'account'
                st.rerun()
            
            if st.button("🚪", help="Sign Out"):
                self._handle_logout()
    
    def _render_sidebar(self):
        """Render enhanced sidebar navigation"""
        with st.sidebar:
            st.markdown("## Navigation")
            
            # Navigation buttons with icons and descriptions
            for page_id, page_info in config.NAVIGATION_PAGES.items():
                # Create button with custom styling
                button_label = f"{page_info['icon']} {page_info['title']}"
                
                if st.button(button_label, key=f"nav_{page_id}", use_container_width=True):
                    st.session_state.current_page = page_id
                    st.rerun()
                
                # Show page description
                if st.session_state.get('current_page') == page_id:
                    st.caption(f"📍 {page_info['description']}")
            
            st.divider()
            
            # Quick stats and account info
            self._render_sidebar_stats()
            
            st.divider()
            
            # Quick actions
            self._render_sidebar_quick_actions()
    
    def _render_sidebar_stats(self):
        """Render sidebar statistics"""
        st.markdown("### 📊 Quick Stats")
        
        user_info = st.session_state.get('user_info', {})
        generation_history = st.session_state.get('generation_history', [])
        uploaded_photos = st.session_state.get('uploaded_photos', [])
        
        # Metrics
        st.metric("Plan", user_info.get('plan', 'Free').title())
        st.metric("Credits", f"{user_info.get('credits', 0)}")
        st.metric("Videos Created", len(generation_history))
        st.metric("Photos Uploaded", len(uploaded_photos))
        
        # Progress towards next milestone
        videos_created = len(generation_history)
        if videos_created < 5:
            st.progress(videos_created / 5)
            st.caption(f"{5 - videos_created} more videos to unlock achievement!")
    
    def _render_sidebar_quick_actions(self):
        """Render sidebar quick actions"""
        st.markdown("### ⚡ Quick Actions")
        
        if st.button("🚀 Generate Video", type="primary", use_container_width=True):
            st.session_state.current_page = 'generate'
            st.rerun()
        
        if st.button("📤 Upload Photo", use_container_width=True):
            st.session_state.current_page = 'upload'
            st.rerun()
        
        if st.button("📈 View Analytics", use_container_width=True):
            st.session_state.current_page = 'account'
            st.rerun()
        
        # Help section
        st.markdown("### 💡 Need Help?")
        
        with st.expander("🎯 Quick Tips"):
            st.markdown("""
            - **Upload**: Use clear, well-lit photos
            - **Text**: Keep messages under 500 characters
            - **Voice**: Preview before generating
            - **Quality**: Higher resolution = better results
            """)
        
        with st.expander("🔗 Resources"):
            st.markdown("""
            - [📚 User Guide](https://docs.talkingphoto.ai)
            - [💬 Community Forum](https://community.talkingphoto.ai)  
            - [📧 Support](mailto:support@talkingphoto.ai)
            - [🐛 Report Bug](https://github.com/talkingphoto/issues)
            """)
    
    def _render_main_content(self):
        """Render main content based on current page"""
        current_page = st.session_state.get('current_page', 'upload')
        
        try:
            if current_page == 'upload':
                self._render_upload_page()
            elif current_page == 'generate':
                self._render_generation_page()
            elif current_page == 'dashboard':
                self._render_dashboard_page()
            elif current_page == 'history':
                self._render_history_page()
            elif current_page == 'account':
                self._render_account_page()
            else:
                st.error(f"Unknown page: {current_page}")
                st.session_state.current_page = 'upload'
                st.rerun()
                
        except Exception as e:
            logger.error(f"Error rendering page {current_page}: {str(e)}")
            st.error(f"Error loading page. Please try again.")
    
    def _render_upload_page(self):
        """US-4.1: Photo Upload Interface"""
        st.header("📤 Photo Upload")
        st.write("Upload your photo to get started creating engaging video content.")
        
        # Use the photo upload component
        uploaded_photo = self.photo_upload.render()
        
        if uploaded_photo:
            # Show option to proceed directly to generation
            st.markdown("---")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🎬 Generate Video with this Photo", 
                           type="primary", use_container_width=True):
                    st.session_state.current_page = 'generate'
                    st.session_state.selected_photo_id = uploaded_photo['id']
                    st.rerun()
    
    def _render_generation_page(self):
        """US-4.2 & US-4.3: Text Input, Voice Config & Generation"""
        st.header("🎬 Generate Video")
        
        # Check prerequisites
        if not st.session_state.get('uploaded_photos'):
            st.warning("⚠️ You need to upload a photo first!")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("📤 Go to Upload", type="primary", use_container_width=True):
                    st.session_state.current_page = 'upload'
                    st.rerun()
            return
        
        # Step 1: Photo Selection
        st.subheader("1️⃣ Select Photo")
        self._render_photo_selection()
        
        st.divider()
        
        # Step 2: Text Input
        st.subheader("2️⃣ Enter Your Text")
        text_input, text_metadata = self.text_input.render()
        
        st.divider()
        
        # Step 3: Voice Configuration
        st.subheader("3️⃣ Configure Voice")
        voice_config = self.voice_config.render()
        
        st.divider()
        
        # Step 4: Cost Estimation & Generation
        if text_input and text_input.strip():
            st.subheader("4️⃣ Generate Video")
            
            # Cost estimation
            estimated_cost = self.cost_estimator.render(
                len(text_input), voice_config, 'standard'
            )
            
            # Generation button
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🚀 Generate Video", type="primary", 
                           use_container_width=True, key="start_generation"):
                    self._start_video_generation(text_input, voice_config, estimated_cost)
    
    def _render_photo_selection(self):
        """Render photo selection interface"""
        uploaded_photos = st.session_state.get('uploaded_photos', [])
        
        if not uploaded_photos:
            st.warning("No photos uploaded yet.")
            return
        
        # Photo selection with preview
        selected_photo_id = st.session_state.get('selected_photo_id')
        
        # Create photo options
        photo_options = {}
        for photo in uploaded_photos:
            quality_score = photo.get('validation', {}).get('confidence', 0)
            photo_options[photo['id']] = f"{photo['name']} (Quality: {quality_score:.1%})"
        
        # Photo selector
        col1, col2 = st.columns([2, 1])
        
        with col1:
            selected_id = st.selectbox(
                "Choose photo",
                options=list(photo_options.keys()),
                format_func=lambda x: photo_options[x],
                index=list(photo_options.keys()).index(selected_photo_id) if selected_photo_id in photo_options else 0
            )
            
            st.session_state.selected_photo_id = selected_id
        
        with col2:
            # Show selected photo details
            selected_photo = next((p for p in uploaded_photos if p['id'] == selected_id), None)
            if selected_photo:
                st.write("**Selected Photo:**")
                st.write(f"Name: {selected_photo['name']}")
                st.write(f"Size: {selected_photo.get('dimensions', 'Unknown')}")
                st.write(f"Quality: {selected_photo.get('validation', {}).get('confidence', 0):.1%}")
    
    def _render_dashboard_page(self):
        """US-4.3: Video Generation Dashboard"""
        st.header("📊 Generation Dashboard")
        
        # Current generation status
        current_generation = st.session_state.get('current_generation')
        if current_generation:
            st.subheader("🔄 Current Generation")
            self.generation_progress.render(current_generation.__dict__ if hasattr(current_generation, '__dict__') else current_generation)
        else:
            st.info("No active generation. Start by uploading a photo and creating a video!")
        
        st.divider()
        
        # Recent activity and analytics
        st.subheader("📈 Recent Activity")
        self._render_recent_activity()
    
    def _render_recent_activity(self):
        """Render recent generation activity"""
        generation_history = st.session_state.get('generation_history', [])
        
        if not generation_history:
            st.info("No generation history yet. Create your first video to see activity here!")
            return
        
        # Statistics overview
        col1, col2, col3, col4 = st.columns(4)
        
        completed = sum(1 for g in generation_history if getattr(g, 'status', 'unknown') == 'completed')
        processing = sum(1 for g in generation_history if getattr(g, 'status', 'unknown') == 'processing')
        failed = sum(1 for g in generation_history if getattr(g, 'status', 'unknown') == 'error')
        
        with col1:
            st.metric("Total Videos", len(generation_history))
        with col2:
            st.metric("Completed", completed, delta=f"{completed/len(generation_history)*100:.0f}%")
        with col3:
            st.metric("In Progress", processing)
        with col4:
            st.metric("Failed", failed)
        
        # Recent generations table
        st.subheader("🔄 Recent Generations")
        
        recent_generations = generation_history[-10:]  # Last 10
        if recent_generations:
            # Create DataFrame for display
            display_data = []
            for gen in reversed(recent_generations):
                display_data.append({
                    'Photo': getattr(gen, 'photo_name', 'Unknown'),
                    'Status': getattr(gen, 'status', 'unknown').title(),
                    'Created': getattr(gen, 'created_at', 'Unknown'),
                    'Progress': f"{getattr(gen, 'progress', 0)}%",
                    'Voice': getattr(gen, 'voice_type', 'Unknown').replace('_', ' ').title()
                })
            
            df = pd.DataFrame(display_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
    
    def _render_history_page(self):
        """Render generation history page"""
        st.header("📋 Generation History")
        
        generation_history = st.session_state.get('generation_history', [])
        
        if not generation_history:
            st.info("No generation history yet.")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🎬 Create Your First Video", 
                           type="primary", use_container_width=True):
                    st.session_state.current_page = 'generate'
                    st.rerun()
            return
        
        # Filters
        self._render_history_filters()
        
        st.divider()
        
        # History list
        self._render_history_list()
    
    def _render_history_filters(self):
        """Render history filtering options"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_query = st.text_input(
                "🔍 Search",
                placeholder="Search by photo name or text...",
                key="history_search"
            )
        
        with col2:
            status_filter = st.selectbox(
                "Filter by Status",
                ['All', 'Completed', 'Processing', 'Error', 'Queued']
            )
        
        with col3:
            date_filter = st.selectbox(
                "Time Period",
                ['All Time', 'Today', 'This Week', 'This Month']
            )
        
        # Store filters in session state for use in filtering
        st.session_state.history_filters = {
            'search': search_query,
            'status': status_filter,
            'date': date_filter
        }
    
    def _render_history_list(self):
        """Render filtered history list"""
        generation_history = st.session_state.get('generation_history', [])
        filters = st.session_state.get('history_filters', {})
        
        # Apply filters (simplified implementation)
        filtered_history = generation_history
        
        if filters.get('search'):
            search_term = filters['search'].lower()
            filtered_history = [
                g for g in filtered_history 
                if search_term in getattr(g, 'photo_name', '').lower() 
                or search_term in getattr(g, 'text', '').lower()
            ]
        
        if filters.get('status') and filters['status'] != 'All':
            status_filter = filters['status'].lower()
            filtered_history = [
                g for g in filtered_history 
                if getattr(g, 'status', 'unknown') == status_filter
            ]
        
        # Display filtered results
        for generation in filtered_history:
            self._render_generation_card(generation)
    
    def _render_generation_card(self, generation):
        """Render individual generation card"""
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 3, 2, 2])
            
            with col1:
                photo_name = getattr(generation, 'photo_name', 'Unknown')
                st.write(f"**{photo_name}**")
                created_at = getattr(generation, 'created_at', 'Unknown')
                st.caption(f"Created: {created_at}")
            
            with col2:
                text = getattr(generation, 'text', '')
                truncated_text = text[:100] + "..." if len(text) > 100 else text
                st.write(f"*{truncated_text}*")
                voice_type = getattr(generation, 'voice_type', 'Unknown')
                st.caption(f"Voice: {voice_type.replace('_', ' ').title()}")
            
            with col3:
                status = getattr(generation, 'status', 'unknown')
                status_colors = {
                    "completed": "green", 
                    "processing": "orange", 
                    "error": "red",
                    "queued": "blue"
                }
                color = status_colors.get(status, "gray")
                st.markdown(f":{color}[{status.title()}]")
            
            with col4:
                if status == 'completed' and hasattr(generation, 'video_url'):
                    if st.button("▶️ Play", key=f"play_{getattr(generation, 'id', 'unknown')}"):
                        video_url = getattr(generation, 'video_url', None)
                        if video_url:
                            st.video(video_url)
                elif status == 'error':
                    if st.button("🔄 Retry", key=f"retry_{getattr(generation, 'id', 'unknown')}"):
                        generation.status = 'processing'
                        generation.progress = 0
                        st.rerun()
            
            st.divider()
    
    def _render_account_page(self):
        """Render account management page"""
        st.header("👤 Account Settings")
        
        user_info = st.session_state.get('user_info', {})
        
        # Account tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Profile", "💳 Subscription", "📊 Analytics", "⚙️ Settings"])
        
        with tab1:
            self._render_profile_tab(user_info)
        
        with tab2:
            self._render_subscription_tab(user_info)
        
        with tab3:
            self._render_analytics_tab()
        
        with tab4:
            self._render_settings_tab()
    
    def _render_profile_tab(self, user_info):
        """Render profile management tab"""
        st.subheader("👤 Profile Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            with st.form("profile_form"):
                first_name = st.text_input("First Name", value=user_info.get('first_name', ''))
                last_name = st.text_input("Last Name", value=user_info.get('last_name', ''))
                email = st.text_input("Email", value=user_info.get('email', ''))
                
                # Profile picture upload
                profile_picture = st.file_uploader("Profile Picture", type=['jpg', 'png'])
                
                if st.form_submit_button("💾 Update Profile", type="primary"):
                    st.success("Profile updated successfully!")
                    # Update user info in session state
                    st.session_state.user_info.update({
                        'first_name': first_name,
                        'last_name': last_name,
                        'name': f"{first_name} {last_name}",
                        'email': email
                    })
        
        with col2:
            st.subheader("📈 Account Statistics")
            
            # Account metrics
            st.metric("Member Since", "January 2024")
            st.metric("Total Videos", len(st.session_state.get('generation_history', [])))
            st.metric("Photos Uploaded", len(st.session_state.get('uploaded_photos', [])))
            st.metric("Account Status", user_info.get('plan', 'Free').title())
    
    def _render_subscription_tab(self, user_info):
        """Render subscription management tab"""
        st.subheader("💳 Subscription & Usage")
        
        current_plan = user_info.get('plan', 'free')
        
        # Current plan info
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Current Plan", current_plan.title())
        with col2:
            st.metric("Credits Remaining", user_info.get('credits', 0))
        with col3:
            st.metric("Videos This Month", user_info.get('monthly_usage', 0))
        
        st.divider()
        
        # Plan comparison
        st.subheader("📋 Available Plans")
        
        plan_col1, plan_col2, plan_col3 = st.columns(3)
        
        with plan_col1:
            st.markdown("""
            **🆓 Free Plan**
            - $0/month
            - 5 videos/month
            - Basic voices
            - Standard quality
            - Community support
            """)
            
            if current_plan != 'free':
                if st.button("Downgrade to Free", key="downgrade_free"):
                    st.warning("Are you sure? You'll lose premium features.")
        
        with plan_col2:
            st.markdown("""
            **⭐ Pro Plan**
            - $9.99/month  
            - 50 videos/month
            - Premium voices
            - HD quality
            - Priority support
            - Custom templates
            """)
            
            if current_plan != 'pro':
                if st.button("Upgrade to Pro", type="primary", key="upgrade_pro"):
                    st.success("🎉 Upgrade to Pro initiated! Redirecting to payment...")
        
        with plan_col3:
            st.markdown("""
            **🏆 Enterprise**
            - $29.99/month
            - 200 videos/month
            - All voices
            - 4K quality  
            - Dedicated support
            - API access
            - White-label options
            """)
            
            if current_plan != 'enterprise':
                if st.button("Upgrade to Enterprise", type="primary", key="upgrade_enterprise"):
                    st.success("🚀 Enterprise upgrade initiated! Our team will contact you.")
    
    def _render_analytics_tab(self):
        """Render analytics tab"""
        st.subheader("📊 Usage Analytics")
        
        # Use the analytics component
        self.analytics.render_user_analytics()
    
    def _render_settings_tab(self):
        """Render settings tab"""
        st.subheader("⚙️ Application Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Notifications**")
            email_notifications = st.checkbox("Email notifications", value=True)
            push_notifications = st.checkbox("Push notifications", value=True)
            generation_updates = st.checkbox("Generation progress updates", value=True)
            
            st.write("**Privacy**")
            analytics_tracking = st.checkbox("Allow analytics tracking", value=True)
            data_sharing = st.checkbox("Share data for improvements", value=False)
        
        with col2:
            st.write("**Preferences**")
            default_voice = st.selectbox(
                "Default voice",
                options=list(config.get_voice_options().keys()),
                format_func=lambda x: config.get_voice_options()[x]
            )
            
            default_speed = st.slider("Default speech speed", 0.5, 2.0, 1.0, 0.1)
            
            auto_save_templates = st.checkbox("Auto-save text templates", value=True)
            
            st.write("**Export**")
            if st.button("📥 Export My Data"):
                st.info("Data export will be available via email within 24 hours.")
            
            if st.button("🗑️ Delete Account", help="This action cannot be undone"):
                st.error("Account deletion requires email confirmation.")
    
    def _render_footer(self):
        """Render application footer"""
        st.divider()
        
        footer_col1, footer_col2, footer_col3 = st.columns(3)
        
        with footer_col1:
            st.caption("🎬 TalkingPhoto AI MVP v1.0.0")
        
        with footer_col2:
            st.caption("Made with ❤️ using Streamlit")
        
        with footer_col3:
            st.caption("© 2024 TalkingPhoto AI. All rights reserved.")
    
    def _start_video_generation(self, text: str, voice_config: dict, estimated_cost: float):
        """Start the video generation process"""
        try:
            # Validate prerequisites
            selected_photo_id = st.session_state.get('selected_photo_id')
            if not selected_photo_id:
                st.error("Please select a photo first.")
                return
            
            # Check user credits
            user_credits = st.session_state.get('user_info', {}).get('credits', 0)
            credits_needed = max(1, int(estimated_cost * 2))
            
            if user_credits < credits_needed:
                st.error(f"Insufficient credits. You need {credits_needed} credits but only have {user_credits}.")
                return
            
            # Create generation record
            from datetime import datetime
            import time
            
            generation_id = f"gen_{int(time.time())}"
            
            # Find selected photo
            selected_photo = next(
                (p for p in st.session_state.uploaded_photos if p['id'] == selected_photo_id), 
                None
            )
            
            if not selected_photo:
                st.error("Selected photo not found.")
                return
            
            # Create generation object (using dict for simplicity)
            generation_data = {
                'id': generation_id,
                'photo_name': selected_photo['name'],
                'photo_id': selected_photo_id,
                'text': text,
                'voice_type': voice_config['voice'],
                'voice_config': voice_config,
                'status': 'processing',
                'progress': 0,
                'created_at': datetime.now(),
                'estimated_completion': datetime.now() + timedelta(minutes=5),
                'estimated_cost': estimated_cost,
                'video_url': None,
                'error_message': None
            }
            
            # Add to session state
            st.session_state.current_generation = generation_data
            
            if 'generation_history' not in st.session_state:
                st.session_state.generation_history = []
            
            st.session_state.generation_history.append(generation_data)
            
            # Deduct credits
            st.session_state.user_info['credits'] -= credits_needed
            
            # Show success message
            st.success("🚀 Video generation started successfully!")
            st.balloons()
            
            # Redirect to dashboard
            st.info("Redirecting to dashboard to monitor progress...")
            time.sleep(2)
            st.session_state.current_page = 'dashboard'
            st.rerun()
            
        except Exception as e:
            logger.error(f"Error starting video generation: {str(e)}")
            st.error("Failed to start video generation. Please try again.")
    
    def _handle_logout(self):
        """Handle user logout"""
        # Clear user session
        st.session_state.authenticated = False
        st.session_state.user_token = None
        st.session_state.user_info = {}
        st.session_state.current_page = 'upload'
        
        # Clear sensitive data but keep some for UX
        keys_to_keep = ['uploaded_photos', 'generation_history', 'saved_templates']
        session_backup = {k: st.session_state.get(k, []) for k in keys_to_keep}
        
        # Clear session
        self.session_manager.clear_session()
        
        # Restore non-sensitive data
        for k, v in session_backup.items():
            st.session_state[k] = v
        
        st.success("Successfully signed out!")
        st.rerun()


def main():
    """Application entry point"""
    try:
        app = TalkingPhotoApp()
        app.run()
    except Exception as e:
        logger.error(f"Application startup error: {str(e)}")
        st.error("Application startup failed. Please refresh the page.")
        
        # Debug information in development
        if os.getenv('STREAMLIT_ENV', 'development') == 'development':
            st.exception(e)


if __name__ == "__main__":
    main()