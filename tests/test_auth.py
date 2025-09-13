"""
TalkingPhoto AI MVP - Authentication Tests
Test user registration, login, and authentication flows
"""

import pytest
from models.user import User


class TestUserRegistration:
    """Test user registration functionality"""
    
    def test_successful_registration(self, client, db_session):
        """Test successful user registration"""
        user_data = {
            'email': 'newuser@example.com',
            'password': 'StrongPassword123!',
            'first_name': 'New',
            'last_name': 'User',
            'gdpr_consent': True
        }
        
        response = client.post('/api/auth/register', json=user_data)
        
        assert response.status_code == 201
        assert 'user' in response.json
        assert response.json['user']['email'] == user_data['email']
        assert response.json['user']['email_verified'] == False
        
        # Verify user was created in database
        user = User.query.filter_by(email=user_data['email']).first()
        assert user is not None
        assert user.first_name == user_data['first_name']
    
    def test_registration_without_gdpr_consent(self, client):
        """Test registration fails without GDPR consent"""
        user_data = {
            'email': 'nogdpr@example.com',
            'password': 'StrongPassword123!',
            'gdpr_consent': False
        }
        
        response = client.post('/api/auth/register', json=user_data)
        
        assert response.status_code == 400
        assert 'GDPR consent is required' in response.json['message']
    
    def test_registration_with_weak_password(self, client):
        """Test registration fails with weak password"""
        user_data = {
            'email': 'weakpass@example.com',
            'password': 'weak',
            'gdpr_consent': True
        }
        
        response = client.post('/api/auth/register', json=user_data)
        
        assert response.status_code == 400
        assert 'Validation failed' in response.json['error']
    
    def test_registration_with_duplicate_email(self, client, test_user):
        """Test registration fails with duplicate email"""
        user_data = {
            'email': test_user.email,
            'password': 'StrongPassword123!',
            'gdpr_consent': True
        }
        
        response = client.post('/api/auth/register', json=user_data)
        
        assert response.status_code == 409
        assert 'User already exists' in response.json['error']


class TestUserLogin:
    """Test user login functionality"""
    
    def test_successful_login(self, client, test_user):
        """Test successful user login"""
        login_data = {
            'email': test_user.email,
            'password': 'TestPassword123!'
        }
        
        response = client.post('/api/auth/login', json=login_data)
        
        assert response.status_code == 200
        assert 'tokens' in response.json
        assert 'access_token' in response.json['tokens']
        assert 'refresh_token' in response.json['tokens']
        assert 'user' in response.json
    
    def test_login_with_invalid_credentials(self, client, test_user):
        """Test login fails with invalid credentials"""
        login_data = {
            'email': test_user.email,
            'password': 'WrongPassword123!'
        }
        
        response = client.post('/api/auth/login', json=login_data)
        
        assert response.status_code == 401
        assert 'Invalid credentials' in response.json['error']
    
    def test_login_with_nonexistent_user(self, client):
        """Test login fails with non-existent user"""
        login_data = {
            'email': 'nonexistent@example.com',
            'password': 'SomePassword123!'
        }
        
        response = client.post('/api/auth/login', json=login_data)
        
        assert response.status_code == 401
        assert 'Invalid credentials' in response.json['error']
    
    def test_login_with_invalid_email_format(self, client):
        """Test login fails with invalid email format"""
        login_data = {
            'email': 'invalid-email-format',
            'password': 'SomePassword123!'
        }
        
        response = client.post('/api/auth/login', json=login_data)
        
        assert response.status_code == 400
        assert 'Validation failed' in response.json['error']


class TestTokenRefresh:
    """Test token refresh functionality"""
    
    def test_successful_token_refresh(self, client, test_user):
        """Test successful token refresh"""
        # First login to get tokens
        login_data = {
            'email': test_user.email,
            'password': 'TestPassword123!'
        }
        
        login_response = client.post('/api/auth/login', json=login_data)
        refresh_token = login_response.json['tokens']['refresh_token']
        
        # Use refresh token to get new access token
        headers = {'Authorization': f'Bearer {refresh_token}'}
        response = client.post('/api/auth/refresh', headers=headers)
        
        assert response.status_code == 200
        assert 'tokens' in response.json
        assert 'access_token' in response.json['tokens']
    
    def test_token_refresh_without_token(self, client):
        """Test token refresh fails without token"""
        response = client.post('/api/auth/refresh')
        
        assert response.status_code == 401


class TestUserLogout:
    """Test user logout functionality"""
    
    def test_successful_logout(self, client, test_user):
        """Test successful user logout"""
        # First login
        login_data = {
            'email': test_user.email,
            'password': 'TestPassword123!'
        }
        
        login_response = client.post('/api/auth/login', json=login_data)
        access_token = login_response.json['tokens']['access_token']
        
        # Then logout
        headers = {'Authorization': f'Bearer {access_token}'}
        response = client.post('/api/auth/logout', headers=headers)
        
        assert response.status_code == 200
        assert 'Logout successful' in response.json['message']
    
    def test_logout_without_token(self, client):
        """Test logout fails without token"""
        response = client.post('/api/auth/logout')
        
        assert response.status_code == 401


class TestEmailVerification:
    """Test email verification functionality"""
    
    def test_email_verification_with_valid_token(self, client, db_session):
        """Test email verification with valid token"""
        # Create user with verification token
        user = User(
            email='verify@example.com',
            password='TestPassword123!',
            email_verification_token='valid_token_123'
        )
        db_session.add(user)
        db_session.commit()
        
        verification_data = {
            'token': 'valid_token_123'
        }
        
        response = client.post('/api/auth/verify-email', json=verification_data)
        
        assert response.status_code == 200
        assert 'Email verified successfully' in response.json['message']
        
        # Check user is verified in database
        user = User.query.filter_by(email='verify@example.com').first()
        assert user.email_verified == True
        assert user.email_verification_token is None
    
    def test_email_verification_with_invalid_token(self, client):
        """Test email verification fails with invalid token"""
        verification_data = {
            'token': 'invalid_token_123'
        }
        
        response = client.post('/api/auth/verify-email', json=verification_data)
        
        assert response.status_code == 400
        assert 'Invalid token' in response.json['error']


class TestPasswordReset:
    """Test password reset functionality"""
    
    def test_password_reset_request(self, client, test_user):
        """Test password reset request"""
        reset_data = {
            'email': test_user.email
        }
        
        response = client.post('/api/auth/request-password-reset', json=reset_data)
        
        assert response.status_code == 200
        # Should always return success to prevent email enumeration
        assert 'password reset link has been sent' in response.json['message']
    
    def test_password_reset_request_nonexistent_email(self, client):
        """Test password reset request with non-existent email"""
        reset_data = {
            'email': 'nonexistent@example.com'
        }
        
        response = client.post('/api/auth/request-password-reset', json=reset_data)
        
        # Should still return success to prevent email enumeration
        assert response.status_code == 200
        assert 'password reset link has been sent' in response.json['message']
    
    def test_password_reset_with_valid_token(self, client, db_session):
        """Test password reset with valid token"""
        # Create user with reset token
        user = User(
            email='reset@example.com',
            password='OldPassword123!',
            password_reset_token='valid_reset_token_123'
        )
        # Set expiration to future
        from datetime import datetime, timezone, timedelta
        user.password_reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        
        db_session.add(user)
        db_session.commit()
        
        reset_data = {
            'token': 'valid_reset_token_123',
            'new_password': 'NewPassword123!'
        }
        
        response = client.post('/api/auth/reset-password', json=reset_data)
        
        assert response.status_code == 200
        assert 'Password reset successful' in response.json['message']
        
        # Verify password was changed
        user = User.query.filter_by(email='reset@example.com').first()
        assert user.check_password('NewPassword123!')
        assert user.password_reset_token is None
    
    def test_password_reset_with_invalid_token(self, client):
        """Test password reset fails with invalid token"""
        reset_data = {
            'token': 'invalid_token_123',
            'new_password': 'NewPassword123!'
        }
        
        response = client.post('/api/auth/reset-password', json=reset_data)
        
        assert response.status_code == 400
        assert 'Invalid or expired token' in response.json['error']