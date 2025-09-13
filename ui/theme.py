"""
TalkingPhoto AI MVP - Theme and Styling

Provides CSS styling and color scheme for the application.
Uses approved colors and mobile-responsive design patterns.
"""

import streamlit as st


class Theme:
    """Theme configuration and CSS styling for TalkingPhoto AI"""
    
    # Approved Color Scheme
    PRIMARY_COLOR = "#ff882e"      # Orange
    SECONDARY_COLOR = "#1a365d"    # Deep Blue
    TEXT_COLOR = "#2d3748"         # Dark Gray
    BACKGROUND_COLOR = "#f7fafc"   # Light Gray
    SUCCESS_COLOR = "#38a169"      # Green
    WARNING_COLOR = "#ed8936"      # Orange Warning
    ERROR_COLOR = "#e53e3e"        # Red
    
    @staticmethod
    def apply_theme():
        """Apply custom CSS theme to Streamlit app"""
        css = f"""
        <style>
        /* Root Variables */
        :root {{
            --primary-color: {Theme.PRIMARY_COLOR};
            --secondary-color: {Theme.SECONDARY_COLOR};
            --text-color: {Theme.TEXT_COLOR};
            --bg-color: {Theme.BACKGROUND_COLOR};
            --success-color: {Theme.SUCCESS_COLOR};
            --warning-color: {Theme.WARNING_COLOR};
            --error-color: {Theme.ERROR_COLOR};
        }}
        
        /* Global Styling */
        .main {{
            background-color: var(--bg-color);
        }}
        
        /* Header Styling */
        .main-header {{
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            padding: 2rem 1rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            text-align: center;
        }}
        
        .main-header h1 {{
            margin: 0;
            font-size: 2.5rem;
            font-weight: 700;
        }}
        
        .main-header p {{
            margin: 0.5rem 0 0 0;
            font-size: 1.2rem;
            opacity: 0.9;
        }}
        
        /* Button Styling */
        .stButton > button {{
            background-color: var(--primary-color);
            color: white;
            border: none;
            padding: 0.75rem 2rem;
            border-radius: 25px;
            font-weight: 600;
            font-size: 1rem;
            transition: all 0.3s ease;
            cursor: pointer;
        }}
        
        .stButton > button:hover {{
            background-color: var(--secondary-color);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        
        /* File Uploader Styling */
        .uploadedFile {{
            border: 2px dashed var(--primary-color);
            border-radius: 10px;
            padding: 2rem;
            text-align: center;
            background-color: rgba(255, 136, 46, 0.05);
        }}
        
        /* Cards and Containers */
        .custom-card {{
            background: white;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }}
        
        /* Credit Display */
        .credit-display {{
            background: linear-gradient(45deg, var(--success-color), #48bb78);
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 1rem;
        }}
        
        .credit-display h3 {{
            margin: 0;
            font-size: 1.1rem;
        }}
        
        .credit-display p {{
            margin: 0.25rem 0 0 0;
            font-size: 1.8rem;
            font-weight: bold;
        }}
        
        /* Progress Bar */
        .stProgress .st-bo {{
            background-color: var(--primary-color);
        }}
        
        /* Tabs Styling */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 1rem;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            background-color: white;
            border-radius: 10px 10px 0 0;
            padding: 1rem 2rem;
            font-weight: 600;
        }}
        
        .stTabs [aria-selected="true"] {{
            background-color: var(--primary-color);
            color: white;
        }}
        
        /* Footer Styling */
        .footer {{
            text-align: center;
            padding: 2rem 1rem 1rem 1rem;
            color: var(--text-color);
            opacity: 0.7;
            border-top: 1px solid #e2e8f0;
            margin-top: 3rem;
        }}
        
        /* Mobile Responsive */
        @media (max-width: 768px) {{
            .main-header h1 {{
                font-size: 2rem;
            }}
            
            .main-header p {{
                font-size: 1rem;
            }}
            
            .stButton > button {{
                padding: 0.6rem 1.5rem;
                font-size: 0.9rem;
            }}
            
            .custom-card {{
                padding: 1.5rem;
            }}
        }}
        
        /* Success/Error States */
        .stAlert {{
            border-radius: 10px;
            border: none;
            padding: 1rem 1.5rem;
        }}
        
        /* Text Input Styling */
        .stTextArea textarea {{
            border-radius: 10px;
            border: 2px solid #e2e8f0;
            padding: 1rem;
        }}
        
        .stTextArea textarea:focus {{
            border-color: var(--primary-color);
            box-shadow: 0 0 0 2px rgba(255, 136, 46, 0.2);
        }}
        
        /* Loading Animation */
        @keyframes pulse {{
            0% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
            100% {{ opacity: 1; }}
        }}
        
        .loading {{
            animation: pulse 1.5s ease-in-out infinite;
        }}
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)
    
    @staticmethod
    def get_color_scheme():
        """Get the color scheme dictionary for programmatic use"""
        return {
            'primary': Theme.PRIMARY_COLOR,
            'secondary': Theme.SECONDARY_COLOR,
            'text': Theme.TEXT_COLOR,
            'background': Theme.BACKGROUND_COLOR,
            'success': Theme.SUCCESS_COLOR,
            'warning': Theme.WARNING_COLOR,
            'error': Theme.ERROR_COLOR
        }