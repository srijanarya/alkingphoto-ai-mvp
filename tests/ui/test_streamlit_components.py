"""
TalkingPhoto AI MVP - Streamlit UI Component Tests

Comprehensive test suite for Streamlit UI components with focus on:
- Component rendering and state management
- File upload validation and user feedback
- Form interactions and validation
- Progress indicators and user experience
- Error handling and display
"""

import pytest
import streamlit as st
from unittest.mock import Mock, patch, MagicMock
import io
import time
from typing import Dict, Any

# Import UI components
from ui.create_video import CreateVideoComponent
from ui.validators import FileValidator, TextValidator, FormValidator
from ui.theme import Theme
from ui.header import Header
from ui.footer import Footer

# Import core modules
from core.session import SessionManager
from core.config import config
from core.credits import CreditManager, TransactionManager


class TestStreamlitComponents:
    """Test suite for Streamlit component functionality"""
    
    def setup_method(self):
        """Setup for each test method"""
        # Clear streamlit session state
        if hasattr(st, 'session_state'):
            st.session_state.clear()
    
    
class TestCreateVideoComponent:
    """Test suite for the main video creation component"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.component = CreateVideoComponent()
        if hasattr(st, 'session_state'):
            st.session_state.clear()
    
    def test_component_initialization(self):
        """Test component properly initializes with config"""
        assert self.component.upload_config is not None
        assert self.component.processing_config is not None
        assert 'max_file_size' in self.component.upload_config
        assert 'min_text_length' in self.component.upload_config
    
    @patch('streamlit.markdown')
    @patch.object(SessionManager, 'has_credits', return_value=False)
    def test_no_credits_state_rendering(self, mock_has_credits, mock_markdown):
        """Test UI behavior when user has no credits"""
        self.component._render_no_credits_state()
        
        # Verify no credits message is displayed
        mock_markdown.assert_called()
        call_args = [call[0][0] for call in mock_markdown.call_args_list]
        assert any('No Credits Available' in arg for arg in call_args)
    
    @patch('streamlit.markdown')
    @patch.object(SessionManager, 'get_credits', return_value=3)
    def test_credits_banner_rendering(self, mock_get_credits, mock_markdown):
        """Test credits display banner"""
        self.component._render_credits_banner()
        
        mock_markdown.assert_called()
        call_args = [call[0][0] for call in mock_markdown.call_args_list]
        assert any('3 free credit' in arg for arg in call_args)
    
    @patch('streamlit.file_uploader')
    @patch('streamlit.image')
    @patch('streamlit.success')
    def test_photo_upload_success(self, mock_success, mock_image, mock_uploader):
        """Test successful photo upload flow"""
        # Mock uploaded file
        mock_file = Mock()
        mock_file.name = 'test.jpg'
        mock_file.type = 'image/jpeg'
        mock_file.size = 1024000  # 1MB
        mock_file.getvalue.return_value = b'fake_image_data'
        
        mock_uploader.return_value = mock_file
        
        # Mock file validation to pass
        with patch.object(FileValidator, 'validate_file', return_value=(True, "Valid")):
            with patch.object(FileValidator, 'get_file_info', return_value={'size_mb': 1.0, 'name': 'test.jpg'}):
                self.component._render_photo_upload()
        
        # Verify success feedback
        mock_success.assert_called()
        mock_image.assert_called_with(mock_file, caption="Uploaded Photo", use_container_width=True)
    
    @patch('streamlit.file_uploader')
    @patch('streamlit.error')
    def test_photo_upload_failure(self, mock_error, mock_uploader):
        """Test photo upload validation failure"""
        # Mock uploaded file with invalid format
        mock_file = Mock()
        mock_file.name = 'test.exe'
        mock_file.type = 'application/x-executable'
        mock_uploader.return_value = mock_file
        
        # Mock file validation to fail
        with patch.object(FileValidator, 'validate_file', return_value=(False, "Invalid file type")):
            self.component._render_photo_upload()
        
        # Verify error feedback
        mock_error.assert_called_with("❌ Invalid file type")
    
    @patch('streamlit.text_area')
    @patch('streamlit.metric')
    @patch('streamlit.success')
    def test_text_input_validation_success(self, mock_success, mock_metric, mock_text_area):
        """Test successful text input validation"""
        test_text = "This is a valid test message for video generation that meets length requirements."
        mock_text_area.return_value = test_text
        
        with patch.object(TextValidator, 'validate_text', return_value=(True, "Valid")):
            with patch.object(TextValidator, 'get_text_stats', return_value={
                'length': len(test_text),
                'words': 15,
                'estimated_duration': '9.0s'
            }):
                self.component._render_text_input()
        
        # Verify success feedback and metrics display
        mock_success.assert_called_with("✅ Text looks good!")
        assert mock_metric.call_count >= 3  # Characters, Words, Duration metrics
    
    @patch('streamlit.text_area')
    @patch('streamlit.error')
    def test_text_input_validation_failure(self, mock_error, mock_text_area):
        """Test text input validation failure"""
        test_text = "Short"  # Too short text
        mock_text_area.return_value = test_text
        
        with patch.object(TextValidator, 'validate_text', return_value=(False, "Text too short")):
            self.component._render_text_input()
        
        # Verify error feedback
        mock_error.assert_called_with("❌ Text too short")
    
    @patch('streamlit.button')
    @patch.object(SessionManager, 'has_credits', return_value=True)
    def test_generation_button_enabled_state(self, mock_has_credits, mock_button):
        """Test generation button is enabled when requirements are met"""
        # Setup session state for valid inputs
        st.session_state.uploaded_photo = Mock()
        st.session_state.video_text_input = "Valid text input for generation"
        st.session_state.video_text_valid = True
        
        mock_button.return_value = False  # Button not clicked
        
        self.component._render_generation_controls()
        
        # Verify button is called without disabled=True
        button_calls = mock_button.call_args_list
        generate_button_call = next((call for call in button_calls 
                                   if "Generate Talking Video" in call[0][0]), None)
        assert generate_button_call is not None
        # Check if disabled parameter is not True
        call_kwargs = generate_button_call[1] if len(generate_button_call) > 1 else {}
        assert call_kwargs.get('disabled', False) is False
    
    @patch('streamlit.button')
    @patch.object(SessionManager, 'has_credits', return_value=False)
    def test_generation_button_disabled_state(self, mock_has_credits, mock_button):
        """Test generation button is disabled when requirements aren't met"""
        # Setup session state with missing requirements
        st.session_state.uploaded_photo = None
        
        self.component._render_generation_controls()
        
        # Verify disabled button is rendered
        button_calls = mock_button.call_args_list
        disabled_button_call = next((call for call in button_calls 
                                   if call[1].get('disabled') is True), None)
        assert disabled_button_call is not None


class TestFileValidator:
    """Test suite for file validation functionality"""
    
    def test_valid_file_validation(self):
        """Test validation of valid image files"""
        mock_file = Mock()
        mock_file.name = 'test_image.jpg'
        mock_file.type = 'image/jpeg'
        mock_file.size = 1024000  # 1MB
        
        is_valid, message = FileValidator.validate_file(mock_file)
        
        assert is_valid is True
        assert "validation passed" in message.lower()
    
    def test_invalid_file_type_validation(self):
        """Test validation rejection of invalid file types"""
        mock_file = Mock()
        mock_file.name = 'test_file.exe'
        mock_file.type = 'application/x-executable'
        mock_file.size = 1024
        
        is_valid, message = FileValidator.validate_file(mock_file)
        
        assert is_valid is False
        assert "invalid file type" in message.lower()
    
    def test_oversized_file_validation(self):
        """Test validation rejection of oversized files"""
        mock_file = Mock()
        mock_file.name = 'large_image.jpg'
        mock_file.type = 'image/jpeg'
        mock_file.size = 60 * 1024 * 1024  # 60MB (exceeds 50MB limit)
        
        is_valid, message = FileValidator.validate_file(mock_file)
        
        assert is_valid is False
        assert "file too large" in message.lower()
    
    def test_file_info_extraction(self):
        """Test file information extraction"""
        mock_file = Mock()
        mock_file.name = 'test_image.png'
        mock_file.type = 'image/png'
        mock_file.size = 2048000  # 2MB
        
        file_info = FileValidator.get_file_info(mock_file)
        
        assert file_info['name'] == 'test_image.png'
        assert file_info['type'] == 'image/png'
        assert file_info['size_mb'] == 2.0
        assert file_info['extension'] == 'png'


class TestTextValidator:
    """Test suite for text validation functionality"""
    
    def test_valid_text_validation(self):
        """Test validation of valid text input"""
        valid_text = "This is a valid text input for video generation that meets all requirements."
        
        is_valid, message = TextValidator.validate_text(valid_text)
        
        assert is_valid is True
        assert "validation passed" in message.lower()
    
    def test_empty_text_validation(self):
        """Test validation rejection of empty text"""
        empty_text = ""
        
        is_valid, message = TextValidator.validate_text(empty_text)
        
        assert is_valid is False
        assert "cannot be empty" in message.lower()
    
    def test_short_text_validation(self):
        """Test validation rejection of too short text"""
        short_text = "Short"
        
        is_valid, message = TextValidator.validate_text(short_text)
        
        assert is_valid is False
        assert "too short" in message.lower()
    
    def test_long_text_validation(self):
        """Test validation rejection of too long text"""
        long_text = "A" * 1500  # Exceeds 1000 character limit
        
        is_valid, message = TextValidator.validate_text(long_text)
        
        assert is_valid is False
        assert "too long" in message.lower()
    
    def test_malicious_text_validation(self):
        """Test validation rejection of potentially harmful content"""
        malicious_text = "Hello there <script>alert('xss')</script> this is bad"
        
        is_valid, message = TextValidator.validate_text(malicious_text)
        
        assert is_valid is False
        assert "harmful content" in message.lower()
    
    def test_text_statistics_calculation(self):
        """Test text statistics calculation"""
        sample_text = "This is a sample text with multiple words and sentences. It has good length."
        
        stats = TextValidator.get_text_stats(sample_text)
        
        assert stats['length'] == len(sample_text)
        assert stats['words'] > 0
        assert stats['sentences'] > 0
        assert 'estimated_duration' in stats


class TestVideoGenerationFlow:
    """Test suite for complete video generation user flow"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.component = CreateVideoComponent()
        if hasattr(st, 'session_state'):
            st.session_state.clear()
    
    @patch('streamlit.progress')
    @patch('streamlit.empty')
    @patch('time.sleep')
    def test_generation_progress_display(self, mock_sleep, mock_empty, mock_progress):
        """Test video generation progress display"""
        validation_data = {
            'file_info': {'name': 'test.jpg', 'size_mb': 1.0},
            'text_stats': {'length': 50, 'words': 10}
        }
        
        # Mock progress bar and status text
        mock_progress_bar = Mock()
        mock_status_text = Mock()
        mock_progress.return_value = mock_progress_bar
        mock_empty.return_value = mock_status_text
        
        self.component._render_generation_progress(validation_data)
        
        # Verify progress updates were called
        assert mock_progress_bar.progress.call_count >= 5
        assert mock_status_text.markdown.call_count >= 5
    
    @patch('streamlit.success')
    @patch('streamlit.balloons')
    @patch.object(SessionManager, 'add_generation')
    def test_generation_success_display(self, mock_add_generation, mock_balloons, mock_success):
        """Test successful generation result display"""
        validation_data = {
            'file_info': {'name': 'test.jpg', 'size_mb': 1.0, 'type': 'image/jpeg'},
            'text_stats': {'length': 50, 'words': 10, 'estimated_duration': '6.0s'}
        }
        
        self.component._render_generation_success(validation_data)
        
        # Verify success feedback
        mock_success.assert_called_with("🎉 Your talking video has been generated successfully!")
        mock_balloons.assert_called_once()
        mock_add_generation.assert_called_once()
    
    @patch.object(SessionManager, 'start_processing')
    @patch.object(SessionManager, 'use_credit', return_value=True)
    @patch.object(SessionManager, 'stop_processing')
    @patch.object(FormValidator, 'validate_creation_form')
    def test_video_generation_workflow(self, mock_validate, mock_stop, mock_use_credit, mock_start):
        """Test complete video generation workflow"""
        # Setup valid form data
        st.session_state.uploaded_photo = Mock()
        st.session_state.video_text_input = "Valid text for generation"
        
        # Mock successful validation
        mock_validate.return_value = (True, "", {
            'file_info': {'name': 'test.jpg'},
            'text_stats': {'words': 10}
        })
        
        with patch.object(self.component, '_render_generation_progress'):
            self.component._handle_video_generation()
        
        # Verify workflow steps
        mock_start.assert_called_once()
        mock_use_credit.assert_called_once()
        mock_stop.assert_called_once()


class TestUIResponsiveness:
    """Test suite for responsive UI behavior"""
    
    @patch('streamlit.columns')
    def test_responsive_layout_columns(self, mock_columns):
        """Test responsive column layouts"""
        # Mock column objects
        mock_col1, mock_col2 = Mock(), Mock()
        mock_columns.return_value = [mock_col1, mock_col2]
        
        component = CreateVideoComponent()
        component._render_upload_interface()
        
        # Verify columns are created for responsive layout
        mock_columns.assert_called()
        call_args = mock_columns.call_args[0] if mock_columns.call_args else []
        # Should have two equal columns
        assert call_args == [1, 1] or call_args == [1, 1]
    
    def test_mobile_upload_configuration(self):
        """Test mobile-optimized file upload configuration"""
        component = CreateVideoComponent()
        
        # Verify mobile-friendly upload limits
        assert component.upload_config['max_file_size'] <= 200 * 1024 * 1024  # 200MB max
        assert component.upload_config['min_text_length'] >= 10  # Reasonable minimum
        assert component.upload_config['max_text_length'] <= 1000  # Manageable on mobile


class TestErrorHandlingUI:
    """Test suite for error handling and user feedback"""
    
    @patch('streamlit.error')
    @patch.object(SessionManager, 'add_credits')
    @patch.object(SessionManager, 'set_error')
    def test_generation_error_handling(self, mock_set_error, mock_add_credits, mock_error):
        """Test error handling during generation process"""
        component = CreateVideoComponent()
        
        # Setup valid form data
        st.session_state.uploaded_photo = Mock()
        st.session_state.video_text_input = "Valid text"
        
        # Mock an exception during validation
        with patch.object(FormValidator, 'validate_creation_form', side_effect=Exception("Test error")):
            with patch.object(SessionManager, 'start_processing'):
                with patch.object(SessionManager, 'stop_processing'):
                    component._handle_video_generation()
        
        # Verify error handling
        mock_error.assert_called()
        mock_add_credits.assert_called_with(1)  # Credit refund
        mock_set_error.assert_called()
    
    @patch('streamlit.error')
    def test_validation_error_display(self, mock_error):
        """Test validation error display to users"""
        component = CreateVideoComponent()
        
        # Setup invalid form data
        st.session_state.uploaded_photo = Mock()
        st.session_state.video_text_input = "Short"  # Too short
        
        with patch.object(FormValidator, 'validate_creation_form', return_value=(False, "Text too short", {})):
            with patch.object(SessionManager, 'start_processing'):
                with patch.object(SessionManager, 'stop_processing'):
                    with patch.object(SessionManager, 'add_credits'):
                        component._handle_video_generation()
        
        # Verify validation error is displayed
        mock_error.assert_called()
        call_args = mock_error.call_args[0][0]
        assert "validation failed" in call_args.lower()


class TestSessionStateManagement:
    """Test suite for Streamlit session state handling"""
    
    def test_session_state_photo_storage(self):
        """Test photo storage in session state"""
        component = CreateVideoComponent()
        
        # Mock file upload
        mock_file = Mock()
        mock_file.name = 'test.jpg'
        
        with patch('streamlit.file_uploader', return_value=mock_file):
            with patch.object(FileValidator, 'validate_file', return_value=(True, "Valid")):
                with patch.object(FileValidator, 'get_file_info', return_value={'size_mb': 1.0}):
                    with patch('streamlit.image'):
                        with patch('streamlit.success'):
                            component._render_photo_upload()
        
        # Verify session state is updated
        assert hasattr(st.session_state, 'uploaded_photo')
        assert st.session_state.uploaded_photo == mock_file
    
    def test_session_state_cleanup(self):
        """Test session state cleanup for new generation"""
        # Setup session state with existing data
        st.session_state.uploaded_photo = Mock()
        st.session_state.video_text_input = "Test text"
        st.session_state.video_text_valid = True
        
        component = CreateVideoComponent()
        
        # Mock the "Create Another" button action
        with patch('streamlit.rerun'):
            # Simulate clearing session state keys
            for key in ['uploaded_photo', 'video_text_input', 'video_text_valid']:
                if key in st.session_state:
                    del st.session_state[key]
        
        # Verify session state is cleared
        assert not hasattr(st.session_state, 'uploaded_photo')
        assert not hasattr(st.session_state, 'video_text_input')


# Pytest configuration for Streamlit testing
@pytest.fixture(autouse=True)
def mock_streamlit_components():
    """Auto-mock Streamlit components for testing"""
    with patch('streamlit.set_page_config'):
        with patch('streamlit.markdown'):
            with patch('streamlit.columns'):
                with patch('streamlit.container'):
                    yield


@pytest.fixture
def sample_uploaded_file():
    """Create a sample uploaded file for testing"""
    mock_file = Mock()
    mock_file.name = 'test_image.jpg'
    mock_file.type = 'image/jpeg'
    mock_file.size = 1024000  # 1MB
    mock_file.getvalue.return_value = b'fake_image_data'
    return mock_file


@pytest.fixture
def valid_text_input():
    """Create valid text input for testing"""
    return "This is a valid text input for video generation that meets all length requirements and contains no harmful content."


if __name__ == "__main__":
    pytest.main([__file__])