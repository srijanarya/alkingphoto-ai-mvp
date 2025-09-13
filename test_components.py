"""
TalkingPhoto AI MVP - Component Tests

Simple test script to validate all components work correctly.
"""

import sys
import traceback

def test_imports():
    """Test all component imports"""
    try:
        from ui.theme import Theme
        from ui.header import Header
        from ui.footer import Footer
        from ui.create_video import CreateVideoComponent
        from ui.validators import FileValidator, TextValidator, FormValidator
        from core.session import SessionManager
        from core.config import config, Environment, FeatureFlag
        from core.credits import CreditManager, CreditTier
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        traceback.print_exc()
        return False

def test_config():
    """Test configuration system"""
    try:
        from core.config import config
        
        # Test basic config access
        app_name = config.get("app_name")
        assert app_name == "TalkingPhoto AI"
        
        # Test nested config
        primary_color = config.get("primary_color")
        assert primary_color == "#ff882e"
        
        # Test feature flags
        from core.config import FeatureFlag
        mock_mode = config.is_feature_enabled(FeatureFlag.MOCK_MODE)
        assert mock_mode == True
        
        # Test file upload config
        upload_config = config.get_file_upload_config()
        assert upload_config['max_size_mb'] == 50
        
        print("✅ Configuration system working")
        return True
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        traceback.print_exc()
        return False

def test_validators():
    """Test validation functions"""
    try:
        from ui.validators import TextValidator, FileValidator
        
        # Test text validation
        valid_text = "This is a valid text for video generation that meets all requirements."
        is_valid, message = TextValidator.validate_text(valid_text)
        assert is_valid == True
        
        # Test invalid text (too short)
        invalid_text = "Short"
        is_valid, message = TextValidator.validate_text(invalid_text)
        assert is_valid == False
        
        # Test text sanitization
        dirty_text = "  <script>alert('test')</script>  Clean text  "
        clean_text = TextValidator.sanitize_text(dirty_text)
        assert "<script>" not in clean_text
        
        # Test text stats
        stats = TextValidator.get_text_stats(valid_text)
        assert 'length' in stats
        assert 'words' in stats
        
        print("✅ Validators working correctly")
        return True
    except Exception as e:
        print(f"❌ Validator test failed: {e}")
        traceback.print_exc()
        return False

def test_credits():
    """Test credit system"""
    try:
        from core.credits import CreditManager, CreditTier
        
        # Test pricing info
        pricing = CreditManager.get_pricing_info()
        assert 'free' in pricing
        assert 'basic' in pricing
        assert 'pro' in pricing
        assert 'premium' in pricing
        
        # Test pricing display
        from core.credits import TransactionManager
        cards = TransactionManager.get_pricing_display()
        assert len(cards) == 4
        
        # Test recommendation
        tier = CreditManager.get_recommended_tier(3)
        assert tier in [CreditTier.BASIC, CreditTier.PRO]
        
        print("✅ Credit system working")
        return True
    except Exception as e:
        print(f"❌ Credit test failed: {e}")
        traceback.print_exc()
        return False

def test_theme():
    """Test theme system"""
    try:
        from ui.theme import Theme
        
        # Test color scheme
        colors = Theme.get_color_scheme()
        assert colors['primary'] == "#ff882e"
        assert colors['secondary'] == "#1a365d"
        
        print("✅ Theme system working")
        return True
    except Exception as e:
        print(f"❌ Theme test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🧪 Testing TalkingPhoto AI MVP Components")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_config,
        test_validators,
        test_credits,
        test_theme
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! Components are working correctly.")
        return True
    else:
        print("❌ Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)