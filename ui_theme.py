"""
Professional UI Theme for TalkingPhoto MVP
Inspired by sunmetalon.com and heimdallpower.com design principles
"""

import streamlit as st

def apply_professional_theme():
    """Apply professional dark theme with orange accents"""
    
    st.markdown("""
    <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;900&display=swap');
        
        /* Root Variables */
        :root {
            --primary-dark: #1b170f;
            --secondary-dark: #2c2416;
            --accent-orange: #d96833;
            --accent-hover: #ff7b3d;
            --text-primary: #ece7e2;
            --text-secondary: #7b756a;
            --card-bg: rgba(255,255,255,0.05);
            --shadow-orange: rgba(217,104,51,0.3);
            --border-radius: 20px;
            --transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
        }
        
        /* Global Styles */
        .stApp {
            background: linear-gradient(180deg, var(--primary-dark) 0%, var(--secondary-dark) 100%);
            font-family: 'Inter', sans-serif;
        }
        
        /* Hide Streamlit Branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Typography */
        h1, h2, h3, h4, h5, h6 {
            color: var(--text-primary) !important;
            font-weight: 700 !important;
            letter-spacing: -0.02em !important;
        }
        
        p, span, label {
            color: var(--text-secondary) !important;
            line-height: 1.6 !important;
        }
        
        /* Hero Section */
        .hero-container {
            background: linear-gradient(135deg, var(--accent-orange) 0%, var(--primary-dark) 100%);
            border-radius: 30px;
            padding: 4rem 2rem;
            margin-bottom: 3rem;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .hero-container::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(217,104,51,0.1) 0%, transparent 70%);
            animation: pulse 4s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 0.5; }
            50% { transform: scale(1.1); opacity: 0.8; }
        }
        
        .hero-title {
            font-size: clamp(2.5rem, 5vw, 4rem);
            font-weight: 900;
            color: white !important;
            margin-bottom: 1rem;
            text-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }
        
        .hero-subtitle {
            font-size: clamp(1.2rem, 2vw, 1.5rem);
            color: rgba(255,255,255,0.9) !important;
            margin-bottom: 2rem;
        }
        
        /* Hero CTA Button */
        .hero-cta-link {
            text-decoration: none;
            display: inline-block;
            margin-top: 1rem;
        }
        
        .hero-cta-button {
            background: linear-gradient(135deg, #ff7b3d 0%, #d96833 100%);
            color: white;
            border: none;
            padding: 1rem 3rem;
            font-size: 1.2rem;
            font-weight: 700;
            border-radius: 50px;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 4px 15px rgba(217, 104, 51, 0.3);
            text-transform: uppercase;
            letter-spacing: 1px;
            position: relative;
            overflow: hidden;
        }
        
        .hero-cta-button:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(217, 104, 51, 0.5);
            background: linear-gradient(135deg, #ff8c4d 0%, #e97943 100%);
        }
        
        .hero-cta-button:active {
            transform: translateY(-1px);
        }
        
        /* Smooth scrolling */
        html {
            scroll-behavior: smooth;
        }
        
        /* Card Components */
        .feature-card {
            background: var(--card-bg);
            border: 1px solid rgba(217,104,51,0.2);
            border-radius: var(--border-radius);
            padding: 2rem;
            margin-bottom: 1.5rem;
            transition: var(--transition);
            backdrop-filter: blur(10px);
            position: relative;
            overflow: hidden;
        }
        
        .feature-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, var(--accent-orange) 0%, transparent 100%);
            transform: scaleX(0);
            transform-origin: left;
            transition: transform 0.3s ease;
        }
        
        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px var(--shadow-orange);
            border-color: var(--accent-orange);
            background: rgba(217,104,51,0.05);
        }
        
        .feature-card:hover::before {
            transform: scaleX(1);
        }
        
        /* Clickable Feature Cards */
        .clickable-card {
            cursor: pointer;
            position: relative;
        }
        
        .click-indicator {
            position: absolute;
            bottom: 1rem;
            right: 1rem;
            color: var(--accent-orange);
            font-size: 0.9rem;
            font-weight: 600;
            opacity: 0;
            transform: translateX(-10px);
            transition: all 0.3s ease;
        }
        
        .clickable-card:hover .click-indicator {
            opacity: 1;
            transform: translateX(0);
        }
        
        .feature-card-link {
            display: block;
            text-decoration: none;
        }
        
        /* Buttons */
        .stButton > button {
            background: linear-gradient(135deg, var(--accent-orange) 0%, #ff7b3d 100%);
            color: white;
            border: none;
            padding: 0.75rem 2rem;
            border-radius: 50px;
            font-weight: 600;
            font-size: 1rem;
            letter-spacing: 0.5px;
            transition: var(--transition);
            box-shadow: 0 4px 15px var(--shadow-orange);
            position: relative;
            overflow: hidden;
        }
        
        .stButton > button::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            border-radius: 50%;
            background: rgba(255,255,255,0.3);
            transform: translate(-50%, -50%);
            transition: width 0.5s, height 0.5s;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px var(--shadow-orange);
            background: linear-gradient(135deg, #ff7b3d 0%, var(--accent-orange) 100%);
        }
        
        .stButton > button:hover::before {
            width: 300px;
            height: 300px;
        }
        
        /* File Uploader - Consistent with text area styling */
        .stFileUploader > div {
            background: var(--card-bg) !important;
            border: 1px solid rgba(217,104,51,0.3) !important;
            border-radius: 12px !important;
            padding: 2rem !important;
            transition: var(--transition);
            box-shadow: 0 0 0 1px transparent;
        }
        
        .stFileUploader > div:hover {
            background: rgba(217,104,51,0.05) !important;
            border-color: var(--accent-orange) !important;
            box-shadow: 0 0 20px rgba(217,104,51,0.2) !important;
        }
        
        /* File uploader dropzone consistent styling */
        [data-testid="stFileUploaderDropzone"] {
            border: 1px solid rgba(217,104,51,0.3) !important;
            background: transparent !important;
        }
        
        [data-testid="stFileUploaderDropzone"]:hover {
            border-color: var(--accent-orange) !important;
        }
        
        /* Input Fields */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            background: var(--card-bg) !important;
            border: 1px solid rgba(217,104,51,0.3) !important;
            border-radius: 12px !important;
            color: var(--text-primary) !important;
            padding: 0.75rem !important;
            transition: var(--transition);
        }
        
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: var(--accent-orange) !important;
            box-shadow: 0 0 0 3px rgba(217,104,51,0.1) !important;
        }
        
        /* Consistent focus glow for file uploader */
        .stFileUploader > div:focus-within,
        [data-testid="stFileUploaderDropzone"]:focus-within {
            border-color: var(--accent-orange) !important;
            box-shadow: 0 0 20px rgba(217,104,51,0.3) !important;
        }
        
        /* Progress Bar */
        .stProgress > div > div {
            background: linear-gradient(90deg, var(--accent-orange) 0%, var(--accent-hover) 100%);
            border-radius: 10px;
            height: 8px;
        }
        
        /* Sidebar */
        .css-1d391kg {
            background: var(--primary-dark);
            border-right: 1px solid rgba(217,104,51,0.2);
        }
        
        /* Metrics */
        [data-testid="metric-container"] {
            background: var(--card-bg);
            border: 1px solid rgba(217,104,51,0.2);
            border-radius: var(--border-radius);
            padding: 1.5rem;
            transition: var(--transition);
        }
        
        [data-testid="metric-container"]:hover {
            transform: scale(1.02);
            box-shadow: 0 10px 30px var(--shadow-orange);
        }
        
        /* Status Indicators */
        .status-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .status-success {
            background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
            color: white;
        }
        
        .status-warning {
            background: linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%);
            color: white;
        }
        
        .status-error {
            background: linear-gradient(135deg, #ef4444 0%, #f87171 100%);
            color: white;
        }
        
        /* Loading Animation */
        .loading-spinner {
            width: 50px;
            height: 50px;
            border: 3px solid var(--card-bg);
            border-top: 3px solid var(--accent-orange);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 2rem auto;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* Grid Layout */
        .grid-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .hero-container {
                padding: 2rem 1rem;
            }
            
            .feature-card {
                padding: 1.5rem;
            }
            
            .grid-container {
                grid-template-columns: 1fr;
            }
        }
        
        /* Custom Scrollbar */
        ::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--primary-dark);
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--accent-orange);
            border-radius: 5px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--accent-hover);
        }
    </style>
    """, unsafe_allow_html=True)

def create_hero_section(title: str, subtitle: str = "", cta_text: str = "Get Started"):
    """Create a hero section with gradient background and smooth scroll CTA"""
    
    st.markdown(f"""
    <div class="hero-container">
        <h1 class="hero-title">{title}</h1>
        <p class="hero-subtitle">{subtitle}</p>
        <a href="#create-section" class="hero-cta-link">
            <button class="hero-cta-button">{cta_text}</button>
        </a>
    </div>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            // Smooth scroll for anchor links
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
                anchor.addEventListener('click', function (e) {{
                    e.preventDefault();
                    const targetId = this.getAttribute('href').substring(1);
                    const targetElement = document.getElementById(targetId);
                    if (targetElement) {{
                        targetElement.scrollIntoView({{
                            behavior: 'smooth',
                            block: 'start'
                        }});
                    }}
                }});
            }});
            
            // Alternative: Scroll on button click
            const ctaButton = document.querySelector('.hero-cta-button');
            if (ctaButton) {{
                ctaButton.addEventListener('click', function(e) {{
                    e.preventDefault();
                    const createSection = document.getElementById('create-section');
                    if (createSection) {{
                        createSection.scrollIntoView({{
                            behavior: 'smooth',
                            block: 'start'
                        }});
                    }}
                }});
            }}
        }});
    </script>
    """, unsafe_allow_html=True)
    
    return False  # Return False since we're handling click via JavaScript

def create_feature_card(title: str, description: str, icon: str = "🚀", link_to: str = None):
    """Create a feature card with hover effects and optional navigation"""
    
    if link_to:
        # Clickable card that navigates to a section
        st.markdown(f"""
        <a href="#{link_to}" class="feature-card-link" style="text-decoration: none; color: inherit;">
            <div class="feature-card clickable-card">
                <div style="font-size: 2rem; margin-bottom: 1rem;">{icon}</div>
                <h3 style="color: var(--accent-orange); margin-bottom: 0.5rem;">{title}</h3>
                <p style="color: var(--text-secondary);">{description}</p>
                <div class="click-indicator">Click to explore →</div>
            </div>
        </a>
        """, unsafe_allow_html=True)
    else:
        # Static card without navigation
        st.markdown(f"""
        <div class="feature-card">
            <div style="font-size: 2rem; margin-bottom: 1rem;">{icon}</div>
            <h3 style="color: var(--accent-orange); margin-bottom: 0.5rem;">{title}</h3>
            <p style="color: var(--text-secondary);">{description}</p>
        </div>
        """, unsafe_allow_html=True)

def create_status_badge(status: str, type: str = "success"):
    """Create a status badge with appropriate styling"""
    
    status_class = f"status-{type}"
    return f'<span class="status-badge {status_class}">{status}</span>'

def create_loading_spinner():
    """Create a custom loading spinner"""
    
    st.markdown("""
    <div class="loading-spinner"></div>
    """, unsafe_allow_html=True)

def create_grid_layout(columns: int = 3):
    """Create a responsive grid layout"""
    
    return st.columns(columns)

# Export all theme functions
__all__ = [
    'apply_professional_theme',
    'create_hero_section',
    'create_feature_card',
    'create_status_badge',
    'create_loading_spinner',
    'create_grid_layout'
]