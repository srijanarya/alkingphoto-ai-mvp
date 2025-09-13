# TalkingPhoto MVP - Technical Implementation Guidelines

## Quick Reference Implementation Guide

### 🎯 Approved UI/UX Changes - Technical Specifications

## 1. CSS-Based Color Scheme Implementation

### Approach: Inline CSS with Streamlit Markdown

```python
# theme.py - Color scheme module
THEME_CSS = """
<style>
    :root {
        --primary-color: #FF6B6B;
        --secondary-color: #4ECDC4;
        --background: #FFFFFF;
        --text-primary: #2C3E50;
        --text-secondary: #7F8C8D;
        --success: #27AE60;
        --warning: #F39C12;
        --error: #E74C3C;
        --border-radius: 8px;
        --shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .stButton > button {
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        color: white;
        border: none;
        border-radius: var(--border-radius);
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: transform 0.2s;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow);
    }

    .main-header {
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        padding: 2rem;
        border-radius: var(--border-radius);
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }

    .credit-badge {
        background: var(--success);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        display: inline-block;
    }
</style>
"""

def apply_theme():
    """Apply custom theme to the app"""
    st.markdown(THEME_CSS, unsafe_allow_html=True)
```

### Integration in app.py:

```python
from ui.theme import apply_theme

# Apply at the start of the app
apply_theme()
```

## 2. Streamlit Native Progress Indicators

### Implementation Pattern:

```python
# progress_indicators.py
def show_video_generation_progress():
    """Multi-step progress indicator for video generation"""

    # Option 1: Simple progress bar
    progress_bar = st.progress(0, text="Initializing...")
    for i in range(100):
        progress_bar.progress(i + 1, text=f"Processing... {i+1}%")

    # Option 2: Status container (better UX)
    with st.status("Generating video...", expanded=True) as status:
        st.write("📸 Analyzing photo...")
        time.sleep(1)
        st.write("🎤 Processing audio...")
        time.sleep(1)
        st.write("🎬 Creating video...")
        time.sleep(1)
        status.update(label="✅ Video complete!", state="complete", expanded=False)

    # Option 3: Spinner for quick operations
    with st.spinner('Uploading...'):
        time.sleep(2)
```

### Best Practice Implementation:

```python
def generate_video_with_progress(photo, text):
    """Production-ready progress implementation"""

    # Create container for progress
    progress_container = st.container()

    with progress_container:
        # Initialize progress tracking
        progress = st.progress(0)
        status_text = st.empty()

        steps = [
            ("Validating input", 10),
            ("Processing image", 30),
            ("Generating speech", 50),
            ("Syncing lips", 80),
            ("Finalizing video", 100)
        ]

        for step_name, step_progress in steps:
            status_text.text(f"⏳ {step_name}...")
            progress.progress(step_progress / 100)
            time.sleep(0.5)  # Simulate processing

        # Clear progress on completion
        progress.empty()
        status_text.empty()

        return True
```

## 3. Input Validation Implementation

### Validation Module Structure:

```python
# validators.py
from typing import Tuple, Optional
import re

class InputValidator:
    """Centralized input validation"""

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    MIN_TEXT_LENGTH = 10
    MAX_TEXT_LENGTH = 500

    @staticmethod
    def validate_photo(file) -> Tuple[bool, Optional[str]]:
        """Validate uploaded photo"""
        if not file:
            return False, "Please upload a photo"

        # Check file size
        if file.size > InputValidator.MAX_FILE_SIZE:
            return False, f"File too large. Maximum size is {InputValidator.MAX_FILE_SIZE // (1024*1024)}MB"

        # Check file extension
        file_ext = file.name.split('.')[-1].lower()
        if file_ext not in InputValidator.ALLOWED_EXTENSIONS:
            return False, f"Invalid file type. Allowed: {', '.join(InputValidator.ALLOWED_EXTENSIONS)}"

        return True, None

    @staticmethod
    def validate_text(text: str) -> Tuple[bool, Optional[str]]:
        """Validate input text"""
        if not text or not text.strip():
            return False, "Please enter text for the video"

        text_length = len(text.strip())

        if text_length < InputValidator.MIN_TEXT_LENGTH:
            return False, f"Text too short. Minimum {InputValidator.MIN_TEXT_LENGTH} characters"

        if text_length > InputValidator.MAX_TEXT_LENGTH:
            return False, f"Text too long. Maximum {InputValidator.MAX_TEXT_LENGTH} characters"

        # Check for inappropriate content (basic filter)
        inappropriate_patterns = [
            r'\b(spam|scam)\b',
            # Add more patterns as needed
        ]

        for pattern in inappropriate_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False, "Content contains inappropriate material"

        return True, None

    @staticmethod
    def validate_email(email: str) -> Tuple[bool, Optional[str]]:
        """Validate email format"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not email:
            return False, "Email is required"

        if not re.match(email_pattern, email):
            return False, "Invalid email format"

        return True, None
```

### Integration with UI:

```python
# In app.py or create_video.py
from ui.validators import InputValidator

def handle_video_generation():
    """Handle video generation with validation"""

    # Get inputs
    photo = st.file_uploader("Upload Photo", type=['png', 'jpg', 'jpeg'])
    text = st.text_area("Enter text for the video")

    if st.button("Generate Video", type="primary"):
        # Validate inputs
        photo_valid, photo_error = InputValidator.validate_photo(photo)
        text_valid, text_error = InputValidator.validate_text(text)

        # Show errors if validation fails
        if not photo_valid:
            st.error(f"❌ {photo_error}")
            return

        if not text_valid:
            st.error(f"❌ {text_error}")
            return

        # Proceed with generation
        with st.spinner("Creating your video..."):
            # Process video
            pass
```

## 4. Professional Layout Components

### Header Component:

```python
# header.py
def render_header():
    """Render professional header with branding"""

    # Create header container
    header_container = st.container()

    with header_container:
        # Apply custom styling
        st.markdown("""
            <div class="main-header">
                <h1 style="margin: 0; font-size: 2.5rem;">🎬 TalkingPhoto AI</h1>
                <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">
                    Transform Your Photos Into Talking Videos
                </p>
            </div>
        """, unsafe_allow_html=True)

        # Status bar
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            credits = st.session_state.get('credits', 1)
            if credits > 0:
                st.markdown(f'<span class="credit-badge">🎁 {credits} Free Credits</span>',
                          unsafe_allow_html=True)
            else:
                st.markdown('<span class="credit-badge" style="background: var(--warning);">No Credits</span>',
                          unsafe_allow_html=True)

        with col2:
            st.metric("Status", "✅ Ready", delta=None)

        with col3:
            st.metric("Quality", "HD", delta=None)

        with col4:
            if st.button("👤 Account", key="header_account"):
                st.session_state.show_account = True
```

### Footer Component:

```python
# footer.py
def render_footer():
    """Render professional footer"""

    st.markdown("---")

    footer_cols = st.columns([2, 1, 1, 1])

    with footer_cols[0]:
        st.markdown("""
            <div style="opacity: 0.7;">
                <p>© 2024 TalkingPhoto AI. All rights reserved.</p>
                <p style="font-size: 0.9rem;">Made with ❤️ using AI</p>
            </div>
        """, unsafe_allow_html=True)

    with footer_cols[1]:
        st.markdown("**Quick Links**")
        st.markdown("[Privacy Policy](#)")
        st.markdown("[Terms of Service](#)")

    with footer_cols[2]:
        st.markdown("**Support**")
        st.markdown("[Help Center](#)")
        st.markdown("[Contact Us](#)")

    with footer_cols[3]:
        st.markdown("**Connect**")
        st.markdown("[Twitter](#)")
        st.markdown("[LinkedIn](#)")
```

### Main Layout Structure:

```python
# app.py - Main application
import streamlit as st
from ui.theme import apply_theme
from ui.header import render_header
from ui.footer import render_footer
from ui.create_video import render_create_video_tab
from ui.pricing import render_pricing_tab
from core.session import initialize_session

# Page configuration
st.set_page_config(
    page_title="TalkingPhoto AI",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize
initialize_session()
apply_theme()

# Main layout
render_header()

# Navigation tabs
tab1, tab2, tab3, tab4 = st.tabs(["🎬 Create", "💎 Pricing", "📚 How It Works", "🎯 Examples"])

with tab1:
    render_create_video_tab()

with tab2:
    render_pricing_tab()

with tab3:
    render_how_it_works_tab()

with tab4:
    render_examples_tab()

render_footer()
```

## 5. Session State Management

```python
# session.py
import streamlit as st
from typing import Any, Dict

class SessionManager:
    """Centralized session state management"""

    DEFAULT_STATE = {
        'credits': 1,
        'user': None,
        'theme': 'light',
        'current_video': None,
        'generation_history': [],
        'show_account': False,
        'upload_count': 0
    }

    @staticmethod
    def initialize():
        """Initialize session state with defaults"""
        for key, default_value in SessionManager.DEFAULT_STATE.items():
            if key not in st.session_state:
                st.session_state[key] = default_value

    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        """Get value from session state"""
        return st.session_state.get(key, default)

    @staticmethod
    def set(key: str, value: Any) -> None:
        """Set value in session state"""
        st.session_state[key] = value

    @staticmethod
    def update(updates: Dict[str, Any]) -> None:
        """Update multiple values"""
        for key, value in updates.items():
            st.session_state[key] = value

    @staticmethod
    def clear():
        """Clear all session state"""
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        SessionManager.initialize()

    @staticmethod
    def use_credit() -> bool:
        """Use a credit if available"""
        if st.session_state.credits > 0:
            st.session_state.credits -= 1
            return True
        return False
```

## 6. Error Handling Pattern

```python
# error_handler.py
import streamlit as st
from functools import wraps
import traceback

def safe_execution(func):
    """Decorator for safe function execution"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            st.error(error_message)

            # Log to console for debugging
            print(f"Error in {func.__name__}: {traceback.format_exc()}")

            # Return safe default
            return None
    return wrapper

# Usage example
@safe_execution
def process_video(photo, text):
    """Process video with error handling"""
    # Video processing logic
    pass
```

## 7. Mobile Responsive Design

```python
# responsive.py
def get_column_config():
    """Get responsive column configuration"""
    # Detect mobile (simplified - Streamlit doesn't provide direct detection)
    # Use container width as proxy

    return {
        'mobile': [1],  # Single column
        'tablet': [1, 1],  # Two columns
        'desktop': [2, 3]  # Asymmetric columns
    }

def render_responsive_layout():
    """Render responsive layout"""
    # For mobile-first approach
    container = st.container()

    with container:
        # Use full width on mobile
        st.markdown("""
            <style>
                @media (max-width: 768px) {
                    .block-container {
                        padding: 1rem;
                    }
                    .stButton > button {
                        width: 100%;
                    }
                }
            </style>
        """, unsafe_allow_html=True)

        # Responsive columns
        if st.session_state.get('layout_mode', 'desktop') == 'mobile':
            # Single column for mobile
            render_mobile_layout()
        else:
            # Multi-column for desktop
            col1, col2 = st.columns([1, 1])
            with col1:
                render_upload_section()
            with col2:
                render_text_section()
```

## 8. Performance Optimization

```python
# performance.py
import streamlit as st
from functools import lru_cache

@st.cache_data(ttl=3600)
def load_static_resources():
    """Cache static resources"""
    return {
        'voices': ['Natural', 'Professional', 'Friendly'],
        'languages': ['English', 'Spanish', 'French'],
        'quality_options': ['Standard', 'HD', '4K']
    }

@st.cache_resource
def get_service_client():
    """Cache service connections"""
    # Future: Return actual service client
    return MockServiceClient()

# Lazy loading for heavy components
def lazy_load_component(component_name: str):
    """Lazy load components on demand"""
    if component_name not in st.session_state.loaded_components:
        # Load component
        st.session_state.loaded_components[component_name] = True
        return import_component(component_name)
```

## 9. Deployment Configuration

### .streamlit/config.toml

```toml
[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#2C3E50"
font = "sans serif"

[server]
port = 8501
enableCORS = false
enableXsrfProtection = true
maxUploadSize = 10
enableWebsocketCompression = true

[browser]
gatherUsageStats = false
serverAddress = "localhost"
```

### requirements.txt (Minimal)

```
streamlit==1.29.0
```

## 10. Testing Implementation

```python
# test_app.py
import pytest
from streamlit.testing.v1 import AppTest

def test_app_loads():
    """Test app loads without errors"""
    app = AppTest.from_file("app.py")
    app.run()
    assert not app.exception

def test_credit_system():
    """Test credit deduction"""
    app = AppTest.from_file("app.py")
    app.run()

    # Initial state
    assert app.session_state.credits == 1

    # Simulate video generation
    app.button[0].click()  # Generate button
    app.run()

    # Check credit deducted
    assert app.session_state.credits == 0

def test_input_validation():
    """Test input validation"""
    from ui.validators import InputValidator

    # Test photo validation
    valid, error = InputValidator.validate_photo(None)
    assert not valid
    assert "upload a photo" in error.lower()

    # Test text validation
    valid, error = InputValidator.validate_text("")
    assert not valid
    assert "enter text" in error.lower()
```

## Summary Checklist

### Immediate Implementation Tasks:

- [x] Create ui/ directory structure
- [x] Implement theme.py with CSS
- [x] Create validators.py module
- [x] Build session state manager
- [x] Add progress indicators
- [x] Create header/footer components

### Quality Assurance:

- [x] No C++ dependencies
- [x] Pure Python/Streamlit only
- [x] Mobile responsive design
- [x] Error handling in place
- [x] Input validation complete
- [x] Session state managed

### Deployment Ready:

- [x] Single dependency (streamlit)
- [x] Config.toml prepared
- [x] File size limits set
- [x] Error messages user-friendly
- [x] Fallback for failures

---

_Implementation Guide Version: 1.0_
_Last Updated: 2024-12-27_
_Next Review: Post-Implementation_
