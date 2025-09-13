"""
TalkingPhoto AI MVP - User Management Unit Tests
Comprehensive tests for user registration, authentication, and profile management
"""

import pytest
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch
from werkzeug.security import check_password_hash

from models.user import User, SubscriptionTier
from models.subscription import Subscription
from core.session import SessionManager
from utils.security import SecurityUtils
from utils.validators import UserValidator


class TestUserModel:
    """Test User model functionality"""
    
    def test_user_creation(self, db_session):
        """Test user creation with valid data"""
        user = User(
            email='test@example.com',
            password='SecurePassword123!',
            first_name='Test',
            last_name='User',
            subscription_tier=SubscriptionTier.FREE
        )
        
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.email == 'test@example.com'
        assert user.first_name == 'Test'
        assert user.last_name == 'User'
        assert user.subscription_tier == SubscriptionTier.FREE
        assert user.credits_remaining == 1  # Free tier default
        assert user.email_verified is False
        assert user.created_at is not None
    
    def test_password_hashing(self, db_session):
        """Test password hashing and verification"""
        password = 'TestPassword123!'
        user = User(
            email='hash_test@example.com',
            password=password,
            first_name='Hash',
            last_name='Test'
        )
        
        # Password should be hashed, not stored as plain text
        assert user.password_hash != password
        assert len(user.password_hash) > 50  # Bcrypt hashes are long
        
        # Should be able to verify password
        assert user.check_password(password) is True
        assert user.check_password('wrong_password') is False
    
    def test_email_normalization(self, db_session):
        """Test email normalization to lowercase"""
        user = User(
            email='Test.User+tag@EXAMPLE.COM',
            password='TestPassword123!',
            first_name='Test',
            last_name='User'
        )
        
        db_session.add(user)
        db_session.commit()
        
        # Email should be normalized to lowercase
        assert user.email == 'test.user+tag@example.com'
    
    def test_unique_email_constraint(self, db_session):
        """Test that email addresses must be unique"""
        # Create first user
        user1 = User(
            email='unique@example.com',
            password='Password123!',
            first_name='First',
            last_name='User'
        )
        db_session.add(user1)
        db_session.commit()
        
        # Attempt to create second user with same email
        user2 = User(
            email='unique@example.com',
            password='Password123!',
            first_name='Second',
            last_name='User'
        )
        db_session.add(user2)
        
        # Should raise integrity error
        with pytest.raises(Exception):  # SQLAlchemy IntegrityError
            db_session.commit()
    
    def test_subscription_tier_defaults(self, db_session):
        """Test subscription tier defaults and credits"""
        # Free tier user
        free_user = User(
            email='free@example.com',
            password='Password123!',
            subscription_tier=SubscriptionTier.FREE
        )
        db_session.add(free_user)
        db_session.commit()
        
        assert free_user.subscription_tier == SubscriptionTier.FREE
        assert free_user.credits_remaining == 1
        
        # Pro tier user
        pro_user = User(
            email='pro@example.com',
            password='Password123!',
            subscription_tier=SubscriptionTier.PRO
        )
        db_session.add(pro_user)
        db_session.commit()
        
        assert pro_user.subscription_tier == SubscriptionTier.PRO
        assert pro_user.credits_remaining == 15  # Pro tier default
    
    def test_credit_management(self, db_session):
        """Test credit addition and deduction"""
        user = User(
            email='credits@example.com',
            password='Password123!',
            credits_remaining=5
        )
        db_session.add(user)
        db_session.commit()
        
        # Test adding credits
        user.add_credits(10)
        assert user.credits_remaining == 15
        
        # Test deducting credits
        result = user.deduct_credits(3)
        assert result is True
        assert user.credits_remaining == 12
        
        # Test insufficient credits
        result = user.deduct_credits(20)
        assert result is False
        assert user.credits_remaining == 12  # Should remain unchanged
    
    def test_email_verification_workflow(self, db_session):
        """Test email verification token generation and validation"""
        user = User(
            email='verify@example.com',
            password='Password123!',
            first_name='Verify',
            last_name='Test'
        )
        db_session.add(user)
        db_session.commit()
        
        # Generate verification token
        token = user.generate_email_verification_token()
        assert token is not None
        assert len(token) > 20  # Should be a substantial token
        assert user.email_verification_token == token
        assert user.email_verified is False
        
        # Verify email with token
        result = user.verify_email(token)
        assert result is True
        assert user.email_verified is True
        assert user.email_verification_token is None
        
        # Verify with wrong token should fail
        user.email_verified = False
        user.generate_email_verification_token()
        result = user.verify_email('wrong_token')
        assert result is False
        assert user.email_verified is False
    
    def test_password_reset_workflow(self, db_session):
        """Test password reset token generation and validation"""
        user = User(
            email='reset@example.com',
            password='OriginalPassword123!',
            first_name='Reset',
            last_name='Test'
        )
        db_session.add(user)
        db_session.commit()
        
        original_password_hash = user.password_hash
        
        # Generate reset token
        token = user.generate_password_reset_token()
        assert token is not None
        assert user.password_reset_token == token
        assert user.password_reset_expires is not None
        assert user.password_reset_expires > datetime.now(timezone.utc)
        
        # Reset password with valid token
        new_password = 'NewPassword123!'
        result = user.reset_password(token, new_password)
        assert result is True
        assert user.password_hash != original_password_hash
        assert user.check_password(new_password) is True
        assert user.password_reset_token is None
        assert user.password_reset_expires is None
        
        # Reset with expired token should fail
        user.generate_password_reset_token()
        user.password_reset_expires = datetime.now(timezone.utc) - timedelta(hours=1)
        db_session.commit()
        
        result = user.reset_password(user.password_reset_token, 'AnotherPassword123!')
        assert result is False
    
    def test_user_activity_tracking(self, db_session):
        """Test user activity and login tracking"""
        user = User(
            email='activity@example.com',
            password='Password123!',
            first_name='Activity',
            last_name='Test'
        )
        db_session.add(user)
        db_session.commit()
        
        # Initially no last login
        assert user.last_login is None
        
        # Update last login
        user.update_last_login()
        assert user.last_login is not None
        assert user.last_login <= datetime.now(timezone.utc)
        
        # Track last activity
        user.update_last_activity()
        assert user.last_activity is not None
        assert user.last_activity <= datetime.now(timezone.utc)


class TestUserValidator:
    """Test user input validation"""
    
    def test_email_validation(self):
        """Test email format validation"""
        valid_emails = [
            'user@example.com',
            'test.email+tag@domain.co.uk',
            'user123@test-domain.com',
            'valid.email@sub.domain.org'
        ]
        
        for email in valid_emails:
            result = UserValidator.validate_email(email)
            assert result['valid'] is True
        
        invalid_emails = [
            'invalid-email',
            '@example.com',
            'user@',
            'user.example.com',
            'user@.com',
            'user@domain.',
            ''
        ]
        
        for email in invalid_emails:
            result = UserValidator.validate_email(email)
            assert result['valid'] is False
            assert 'error' in result
    
    def test_password_validation(self):
        """Test password strength validation"""
        # Valid passwords
        valid_passwords = [
            'SecurePassword123!',
            'Another@Pass1',
            'Complex$Pass123',
            'Valid&Password1'
        ]
        
        for password in valid_passwords:
            result = UserValidator.validate_password(password)
            assert result['valid'] is True
        
        # Invalid passwords
        invalid_cases = [
            ('short1!', 'too short'),
            ('nouppercase123!', 'uppercase'),
            ('NOLOWERCASE123!', 'lowercase'), 
            ('NoNumbers!', 'digit'),
            ('NoSpecialChars123', 'special'),
            ('password123!', 'common'),
            ('', 'empty')
        ]
        
        for password, expected_error_type in invalid_cases:
            result = UserValidator.validate_password(password)
            assert result['valid'] is False
            assert 'error' in result
    
    def test_name_validation(self):
        """Test name field validation"""
        valid_names = [
            'John',
            'Mary-Jane',
            "O'Connor",
            'José',
            'Anne Marie'
        ]
        
        for name in valid_names:
            result = UserValidator.validate_name(name)
            assert result['valid'] is True
        
        invalid_names = [
            '',           # Empty
            'J',          # Too short
            'A' * 51,     # Too long
            'John123',    # Contains numbers
            'John@Doe',   # Contains symbols
            '   ',        # Only whitespace
        ]
        
        for name in invalid_names:
            result = UserValidator.validate_name(name)
            assert result['valid'] is False
    
    def test_registration_data_validation(self):
        """Test complete registration data validation"""
        valid_data = {
            'email': 'newuser@example.com',
            'password': 'SecurePassword123!',
            'first_name': 'New',
            'last_name': 'User',
            'gdpr_consent': True
        }
        
        result = UserValidator.validate_registration_data(valid_data)
        assert result['valid'] is True
        
        # Test missing required fields
        incomplete_data = {
            'email': 'test@example.com',
            'password': 'Password123!',
            # Missing names and consent
        }
        
        result = UserValidator.validate_registration_data(incomplete_data)
        assert result['valid'] is False
        assert 'required' in result['error'].lower()
        
        # Test invalid GDPR consent
        no_consent_data = valid_data.copy()
        no_consent_data['gdpr_consent'] = False
        
        result = UserValidator.validate_registration_data(no_consent_data)
        assert result['valid'] is False
        assert 'gdpr' in result['error'].lower()


class TestSessionManager:
    """Test session management functionality"""
    
    @pytest.fixture
    def session_manager(self):
        with patch('core.session.current_app') as mock_app:
            mock_app.config.get.side_effect = lambda key: {
                'SECRET_KEY': 'test_secret_key_for_jwt',
                'JWT_ACCESS_TOKEN_EXPIRES': 3600,
                'JWT_REFRESH_TOKEN_EXPIRES': 86400 * 7
            }.get(key)
            return SessionManager()
    
    @pytest.fixture
    def test_user_data(self):
        return {
            'user_id': 'test_user_123',
            'email': 'session@example.com',
            'subscription_tier': 'pro'
        }
    
    def test_generate_access_token(self, session_manager, test_user_data):
        """Test access token generation"""
        token = session_manager.generate_access_token(test_user_data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are substantial
        
        # Verify token can be decoded
        decoded = session_manager.decode_token(token)
        assert decoded is not None
        assert decoded['user_id'] == test_user_data['user_id']
        assert decoded['email'] == test_user_data['email']
    
    def test_generate_refresh_token(self, session_manager, test_user_data):
        """Test refresh token generation"""
        token = session_manager.generate_refresh_token(test_user_data)
        
        assert token is not None
        assert isinstance(token, str)
        
        # Refresh token should have longer expiration
        decoded = session_manager.decode_token(token)
        assert decoded is not None
        assert decoded['token_type'] == 'refresh'
    
    def test_token_expiration(self, session_manager, test_user_data):
        """Test token expiration handling"""
        # Create token with very short expiration
        with patch.object(session_manager, 'access_token_expires', 1):  # 1 second
            token = session_manager.generate_access_token(test_user_data)
            
            # Should decode immediately
            decoded = session_manager.decode_token(token)
            assert decoded is not None
            
            # Wait for expiration
            time.sleep(2)
            
            # Should fail to decode expired token
            decoded = session_manager.decode_token(token)
            assert decoded is None
    
    def test_invalid_token_handling(self, session_manager):
        """Test handling of invalid tokens"""
        invalid_tokens = [
            'invalid.token.here',
            'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid.signature',
            '',
            None,
            'completely_wrong_format'
        ]
        
        for token in invalid_tokens:
            decoded = session_manager.decode_token(token)
            assert decoded is None
    
    def test_refresh_token_workflow(self, session_manager, test_user_data):
        """Test refresh token usage to get new access token"""
        # Generate refresh token
        refresh_token = session_manager.generate_refresh_token(test_user_data)
        
        # Use refresh token to get new access token
        new_access_token = session_manager.refresh_access_token(refresh_token)
        
        assert new_access_token is not None
        
        # New access token should be valid
        decoded = session_manager.decode_token(new_access_token)
        assert decoded is not None
        assert decoded['user_id'] == test_user_data['user_id']
        assert decoded['token_type'] == 'access'
    
    def test_session_creation_and_validation(self, session_manager, test_user_data):
        """Test complete session creation and validation"""
        # Create session
        session_data = session_manager.create_session(test_user_data)
        
        assert 'access_token' in session_data
        assert 'refresh_token' in session_data
        assert 'expires_in' in session_data
        
        # Validate session
        access_token = session_data['access_token']
        is_valid = session_manager.validate_session(access_token)
        assert is_valid is True
        
        # Get user data from session
        user_data = session_manager.get_session_user(access_token)
        assert user_data is not None
        assert user_data['user_id'] == test_user_data['user_id']


class TestSecurityUtils:
    """Test security utility functions"""
    
    def test_generate_secure_token(self):
        """Test secure token generation"""
        token = SecurityUtils.generate_secure_token()
        
        assert token is not None
        assert len(token) >= 32  # Should be substantial
        assert isinstance(token, str)
        
        # Multiple calls should generate different tokens
        token2 = SecurityUtils.generate_secure_token()
        assert token != token2
    
    def test_generate_secure_token_custom_length(self):
        """Test secure token generation with custom length"""
        lengths = [16, 32, 64, 128]
        
        for length in lengths:
            token = SecurityUtils.generate_secure_token(length)
            assert len(token) == length * 2  # Hex encoding doubles length
    
    def test_hash_password(self):
        """Test password hashing"""
        password = 'TestPassword123!'
        hashed = SecurityUtils.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 50  # Bcrypt hashes are long
        assert hashed.startswith('$2b$')  # Bcrypt format
        
        # Same password should produce different hashes (due to salt)
        hashed2 = SecurityUtils.hash_password(password)
        assert hashed != hashed2
    
    def test_verify_password(self):
        """Test password verification"""
        password = 'TestPassword123!'
        hashed = SecurityUtils.hash_password(password)
        
        # Correct password should verify
        assert SecurityUtils.verify_password(password, hashed) is True
        
        # Wrong password should not verify
        assert SecurityUtils.verify_password('WrongPassword', hashed) is False
    
    def test_sanitize_input(self):
        """Test input sanitization"""
        test_cases = [
            ('normal text', 'normal text'),
            ('<script>alert("xss")</script>', 'alert("xss")'),
            ('user@example.com', 'user@example.com'),
            ('text with\nnewlines\r\n', 'text with newlines '),
            ('  trim  whitespace  ', 'trim whitespace'),
        ]
        
        for input_text, expected in test_cases:
            result = SecurityUtils.sanitize_input(input_text)
            assert result == expected
    
    def test_generate_otp(self):
        """Test OTP generation"""
        otp = SecurityUtils.generate_otp()
        
        assert otp is not None
        assert len(otp) == 6  # Standard OTP length
        assert otp.isdigit()  # Should be all digits
        
        # Multiple calls should generate different OTPs
        otp2 = SecurityUtils.generate_otp()
        assert otp != otp2  # Very unlikely to be same
    
    def test_validate_otp_format(self):
        """Test OTP format validation"""
        valid_otps = ['123456', '000000', '999999']
        
        for otp in valid_otps:
            assert SecurityUtils.validate_otp_format(otp) is True
        
        invalid_otps = ['12345', '1234567', 'abc123', '', '12 34 56']
        
        for otp in invalid_otps:
            assert SecurityUtils.validate_otp_format(otp) is False


@pytest.mark.integration
class TestUserManagementIntegration:
    """Integration tests for user management components"""
    
    def test_complete_user_registration_flow(self, db_session):
        """Test complete user registration workflow"""
        # Step 1: Validate registration data
        registration_data = {
            'email': 'integration@example.com',
            'password': 'SecurePassword123!',
            'first_name': 'Integration',
            'last_name': 'Test',
            'gdpr_consent': True
        }
        
        validation_result = UserValidator.validate_registration_data(registration_data)
        assert validation_result['valid'] is True
        
        # Step 2: Create user
        user = User(
            email=registration_data['email'],
            password=registration_data['password'],
            first_name=registration_data['first_name'],
            last_name=registration_data['last_name']
        )
        
        db_session.add(user)
        db_session.commit()
        
        # Step 3: Generate email verification
        verification_token = user.generate_email_verification_token()
        assert verification_token is not None
        
        # Step 4: Verify email
        verify_result = user.verify_email(verification_token)
        assert verify_result is True
        assert user.email_verified is True
        
        # Step 5: Create session
        session_manager = SessionManager()
        user_data = {
            'user_id': user.id,
            'email': user.email,
            'subscription_tier': user.subscription_tier.value
        }
        
        session_data = session_manager.create_session(user_data)
        assert 'access_token' in session_data
        
        # Step 6: Validate session works
        is_valid = session_manager.validate_session(session_data['access_token'])
        assert is_valid is True
    
    def test_complete_password_reset_flow(self, db_session):
        """Test complete password reset workflow"""
        # Create user
        user = User(
            email='password_reset@example.com',
            password='OriginalPassword123!',
            first_name='Reset',
            last_name='Test'
        )
        user.mark_email_verified()  # Email must be verified for password reset
        
        db_session.add(user)
        db_session.commit()
        
        original_password_hash = user.password_hash
        
        # Step 1: Request password reset
        reset_token = user.generate_password_reset_token()
        assert reset_token is not None
        
        # Step 2: Validate reset token format
        assert len(reset_token) > 20
        
        # Step 3: Reset password
        new_password = 'NewSecurePassword123!'
        reset_result = user.reset_password(reset_token, new_password)
        assert reset_result is True
        
        # Step 4: Verify password changed
        assert user.password_hash != original_password_hash
        assert user.check_password(new_password) is True
        assert user.check_password('OriginalPassword123!') is False
        
        # Step 5: Verify can login with new password
        assert user.check_password(new_password) is True