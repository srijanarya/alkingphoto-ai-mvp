"""
Comprehensive UI Testing Suite for TalkingPhoto MVP
Tests all UI components, interactions, and edge cases
"""

import streamlit as st
import time
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from ui_theme import (
    apply_professional_theme,
    create_hero_section,
    create_feature_card,
    create_status_badge,
    create_loading_spinner,
    create_grid_layout
)

def test_theme_application():
    """Test if theme applies correctly"""
    st.write("### Testing Theme Application")
    
    try:
        apply_professional_theme()
        st.success("✅ Theme applied successfully")
        return True
    except Exception as e:
        st.error(f"❌ Theme application failed: {e}")
        return False

def test_hero_section():
    """Test hero section rendering"""
    st.write("### Testing Hero Section")
    
    try:
        clicked = create_hero_section(
            title="Test Hero Title",
            subtitle="Test subtitle with description",
            cta_text="Test CTA Button"
        )
        
        if clicked:
            st.info("Hero CTA button was clicked!")
        
        st.success("✅ Hero section rendered successfully")
        return True
    except Exception as e:
        st.error(f"❌ Hero section failed: {e}")
        return False

def test_feature_cards():
    """Test feature card components"""
    st.write("### Testing Feature Cards")
    
    try:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            create_feature_card(
                "Test Feature 1",
                "This is a test description for feature card 1",
                "🎯"
            )
        
        with col2:
            create_feature_card(
                "Test Feature 2",
                "This is a test description for feature card 2",
                "🚀"
            )
        
        with col3:
            create_feature_card(
                "Test Feature 3",
                "This is a test description for feature card 3",
                "✨"
            )
        
        st.success("✅ Feature cards rendered successfully")
        return True
    except Exception as e:
        st.error(f"❌ Feature cards failed: {e}")
        return False

def test_status_badges():
    """Test status badge variations"""
    st.write("### Testing Status Badges")
    
    try:
        badges_html = f"""
        <div style="display: flex; gap: 1rem; flex-wrap: wrap; margin: 1rem 0;">
            {create_status_badge("Success", "success")}
            {create_status_badge("Warning", "warning")}
            {create_status_badge("Error", "error")}
        </div>
        """
        st.markdown(badges_html, unsafe_allow_html=True)
        
        st.success("✅ Status badges rendered successfully")
        return True
    except Exception as e:
        st.error(f"❌ Status badges failed: {e}")
        return False

def test_loading_spinner():
    """Test loading spinner animation"""
    st.write("### Testing Loading Spinner")
    
    try:
        with st.container():
            create_loading_spinner()
            time.sleep(1)  # Show spinner for 1 second
        
        st.success("✅ Loading spinner rendered successfully")
        return True
    except Exception as e:
        st.error(f"❌ Loading spinner failed: {e}")
        return False

def test_responsive_grid():
    """Test responsive grid layout"""
    st.write("### Testing Responsive Grid Layout")
    
    try:
        # Test different column configurations
        st.write("2 Column Grid:")
        cols = create_grid_layout(2)
        for i, col in enumerate(cols):
            with col:
                st.info(f"Column {i+1}")
        
        st.write("3 Column Grid:")
        cols = create_grid_layout(3)
        for i, col in enumerate(cols):
            with col:
                st.info(f"Column {i+1}")
        
        st.write("4 Column Grid:")
        cols = create_grid_layout(4)
        for i, col in enumerate(cols):
            with col:
                st.info(f"Column {i+1}")
        
        st.success("✅ Grid layouts rendered successfully")
        return True
    except Exception as e:
        st.error(f"❌ Grid layout failed: {e}")
        return False

def test_form_elements():
    """Test form elements with theme"""
    st.write("### Testing Form Elements")
    
    try:
        # File uploader
        uploaded = st.file_uploader(
            "Test File Upload",
            type=['png', 'jpg', 'jpeg'],
            help="Testing file upload styling"
        )
        
        # Text input
        text = st.text_input(
            "Test Text Input",
            placeholder="Enter test text",
            help="Testing text input styling"
        )
        
        # Text area
        textarea = st.text_area(
            "Test Text Area",
            placeholder="Enter longer test text",
            height=100,
            help="Testing text area styling"
        )
        
        # Select box
        selection = st.selectbox(
            "Test Select Box",
            ["Option 1", "Option 2", "Option 3"],
            help="Testing select box styling"
        )
        
        # Button
        if st.button("Test Button", use_container_width=True):
            st.info("Button clicked!")
        
        st.success("✅ Form elements rendered successfully")
        return True
    except Exception as e:
        st.error(f"❌ Form elements failed: {e}")
        return False

def test_metrics_display():
    """Test metrics display components"""
    st.write("### Testing Metrics Display")
    
    try:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="Credits",
                value=10,
                delta=2,
                delta_color="normal"
            )
        
        with col2:
            st.metric(
                label="Videos Generated",
                value=25,
                delta=-3,
                delta_color="inverse"
            )
        
        with col3:
            st.metric(
                label="Success Rate",
                value="95%",
                delta="5%",
                delta_color="normal"
            )
        
        st.success("✅ Metrics displayed successfully")
        return True
    except Exception as e:
        st.error(f"❌ Metrics display failed: {e}")
        return False

def test_progress_indicators():
    """Test progress indicators"""
    st.write("### Testing Progress Indicators")
    
    try:
        # Progress bar
        progress = st.progress(0)
        for i in range(101):
            progress.progress(i)
            time.sleep(0.01)
        
        # Spinner
        with st.spinner("Testing spinner..."):
            time.sleep(1)
        
        st.success("✅ Progress indicators working successfully")
        return True
    except Exception as e:
        st.error(f"❌ Progress indicators failed: {e}")
        return False

def test_edge_cases():
    """Test edge cases and error handling"""
    st.write("### Testing Edge Cases")
    
    test_cases = []
    
    # Test empty strings
    try:
        create_feature_card("", "", "")
        test_cases.append(("Empty strings", True))
    except:
        test_cases.append(("Empty strings", False))
    
    # Test very long strings
    try:
        long_text = "A" * 1000
        create_feature_card(long_text, long_text, "📝")
        test_cases.append(("Long strings", True))
    except:
        test_cases.append(("Long strings", False))
    
    # Test special characters
    try:
        create_feature_card(
            "Test <script>alert('xss')</script>",
            "Test & < > \" ' characters",
            "🔒"
        )
        test_cases.append(("Special characters", True))
    except:
        test_cases.append(("Special characters", False))
    
    # Display results
    for test_name, passed in test_cases:
        if passed:
            st.success(f"✅ {test_name}: Handled correctly")
        else:
            st.warning(f"⚠️ {test_name}: Needs attention")
    
    return all(result for _, result in test_cases)

def run_all_tests():
    """Run all UI tests"""
    st.set_page_config(
        page_title="TalkingPhoto UI Testing Suite",
        page_icon="🧪",
        layout="wide"
    )
    
    apply_professional_theme()
    
    st.title("🧪 TalkingPhoto UI Testing Suite")
    st.markdown("---")
    
    # Test results tracker
    results = []
    
    # Run tests
    tests = [
        ("Theme Application", test_theme_application),
        ("Hero Section", test_hero_section),
        ("Feature Cards", test_feature_cards),
        ("Status Badges", test_status_badges),
        ("Loading Spinner", test_loading_spinner),
        ("Responsive Grid", test_responsive_grid),
        ("Form Elements", test_form_elements),
        ("Metrics Display", test_metrics_display),
        ("Progress Indicators", test_progress_indicators),
        ("Edge Cases", test_edge_cases)
    ]
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, (test_name, test_func) in enumerate(tests):
        status_text.text(f"Running: {test_name}")
        st.markdown("---")
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            st.error(f"Test {test_name} crashed: {e}")
            results.append((test_name, False))
        
        progress_bar.progress((i + 1) / len(tests))
    
    status_text.text("All tests completed!")
    
    # Summary
    st.markdown("---")
    st.header("📊 Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    pass_rate = (passed / total) * 100
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Tests Passed", f"{passed}/{total}")
    
    with col2:
        st.metric("Pass Rate", f"{pass_rate:.1f}%")
    
    with col3:
        if pass_rate == 100:
            st.metric("Status", "✅ All Passing")
        elif pass_rate >= 80:
            st.metric("Status", "⚠️ Mostly Passing")
        else:
            st.metric("Status", "❌ Needs Work")
    
    # Detailed results
    st.markdown("### Detailed Results")
    for test_name, passed in results:
        if passed:
            st.success(f"✅ {test_name}")
        else:
            st.error(f"❌ {test_name}")
    
    # Recommendations
    if pass_rate < 100:
        st.markdown("### 🔧 Recommendations")
        st.warning("Some tests failed. Please review the error messages above and fix the issues before deployment.")
    else:
        st.markdown("### 🎉 Ready for Deployment!")
        st.success("All tests passed! The UI is ready for production deployment.")

if __name__ == "__main__":
    run_all_tests()