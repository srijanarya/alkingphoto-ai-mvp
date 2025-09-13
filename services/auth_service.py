"""
TalkingPhoto AI MVP - Authentication Service
Streamlit-compatible user authentication and session management
"""

import streamlit as st
import hashlib
import hmac
import secrets
import sqlite3
import jwt
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import bcrypt
from config import Config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AuthService:
    """
    Authentication service for TalkingPhoto MVP
    Handles user registration, login, session management, and password security
    """
    
    def __init__(self):
        self.db_path = "data/users.db"
        self.secret_key = Config.SECRET_KEY
        self.jwt_secret = Config.JWT_SECRET_KEY
        self.init_database()
    
    def init_database(self):
        """Initialize user authentication database"""
        import os
        os.makedirs("data", exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Users table with authentication fields
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auth_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    name TEXT,
                    phone TEXT,
                    is_verified INTEGER DEFAULT 0,
                    verification_token TEXT,
                    reset_token TEXT,
                    reset_token_expires TIMESTAMP,
                    last_login TIMESTAMP,
                    login_attempts INTEGER DEFAULT 0,
                    locked_until TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    session_token TEXT UNIQUE,
                    device_info TEXT,
                    ip_address TEXT,
                    expires_at TIMESTAMP,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES auth_users (id)
                )
            """)
            
            # Login history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS login_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    ip_address TEXT,
                    user_agent TEXT,
                    success INTEGER,
                    failure_reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES auth_users (id)
                )
            """)
            
            conn.commit()
    
    def hash_password(self, password: str) -> Tuple[str, str]:
        """Hash password with salt using bcrypt"""
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        return password_hash.decode('utf-8'), salt.decode('utf-8')
    
    def verify_password(self, password: str, hashed_password: str, salt: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate secure random token"""
        return secrets.token_urlsafe(length)
    
    def create_jwt_token(self, user_id: int, email: str, expires_hours: int = 24) -> str:
        """Create JWT token for user"""
        payload = {
            'user_id': user_id,
            'email': email,
            'exp': datetime.utcnow() + timedelta(hours=expires_hours),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')
    
    def verify_jwt_token(self, token: str) -> Optional[Dict]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid JWT token")
            return None
    
    def register_user(self, email: str, password: str, name: str = None, phone: str = None) -> Dict:
        """Register new user account"""
        try:
            # Validate email format
            if not self.validate_email(email):
                return {"success": False, "message": "Invalid email format"}
            
            # Validate password strength
            password_validation = self.validate_password(password)
            if not password_validation["valid"]:
                return {"success": False, "message": password_validation["message"]}
            
            # Check if user already exists
            if self.get_user_by_email(email):
                return {"success": False, "message": "User already exists"}
            
            # Hash password
            password_hash, salt = self.hash_password(password)
            
            # Generate verification token
            verification_token = self.generate_secure_token()
            
            # Insert user into database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO auth_users 
                    (email, password_hash, salt, name, phone, verification_token)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (email, password_hash, salt, name, phone, verification_token))
                
                user_id = cursor.lastrowid
                conn.commit()
            
            # Log registration
            self.log_login_attempt(user_id, "127.0.0.1", "registration", True)
            
            logger.info(f"User registered: {email}")
            return {
                "success": True, 
                "message": "Registration successful",
                "user_id": user_id,
                "verification_token": verification_token
            }
        
        except Exception as e:
            logger.error(f"Registration failed: {str(e)}")
            return {"success": False, "message": "Registration failed"}
    
    def login_user(self, email: str, password: str, ip_address: str = "127.0.0.1") -> Dict:
        """Authenticate user login"""
        try:
            user = self.get_user_by_email(email)
            
            if not user:
                self.log_login_attempt(None, ip_address, "login", False, "User not found")
                return {"success": False, "message": "Invalid credentials"}
            
            # Check if account is locked
            if self.is_account_locked(user['id']):
                return {"success": False, "message": "Account temporarily locked due to failed attempts"}
            
            # Verify password
            if not self.verify_password(password, user['password_hash'], user['salt']):
                self.increment_login_attempts(user['id'])
                self.log_login_attempt(user['id'], ip_address, "login", False, "Invalid password")
                return {"success": False, "message": "Invalid credentials"}
            
            # Check if email is verified
            if not user['is_verified']:
                return {"success": False, "message": "Please verify your email address"}
            
            # Reset login attempts on successful login
            self.reset_login_attempts(user['id'])
            
            # Update last login
            self.update_last_login(user['id'])
            
            # Create session
            session_token = self.create_session(user['id'], ip_address)
            
            # Create JWT token
            jwt_token = self.create_jwt_token(user['id'], email)
            
            # Log successful login
            self.log_login_attempt(user['id'], ip_address, "login", True)
            
            logger.info(f"User logged in: {email}")
            return {
                "success": True,
                "message": "Login successful",
                "user": {
                    "id": user['id'],
                    "email": user['email'],
                    "name": user['name']
                },
                "session_token": session_token,
                "jwt_token": jwt_token
            }
        
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return {"success": False, "message": "Login failed"}
    
    def logout_user(self, session_token: str) -> bool:
        """Logout user and invalidate session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE user_sessions 
                    SET is_active = 0 
                    WHERE session_token = ?
                """, (session_token,))
                conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"Logout failed: {str(e)}")
            return False
    
    def verify_session(self, session_token: str) -> Optional[Dict]:
        """Verify user session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT s.user_id, s.expires_at, u.email, u.name
                    FROM user_sessions s
                    JOIN auth_users u ON s.user_id = u.id
                    WHERE s.session_token = ? AND s.is_active = 1
                """, (session_token,))
                
                result = cursor.fetchone()
                
                if result:
                    user_id, expires_at, email, name = result
                    
                    # Check if session is expired
                    if datetime.fromisoformat(expires_at) > datetime.utcnow():
                        return {
                            "user_id": user_id,
                            "email": email,
                            "name": name
                        }
                    else:
                        # Session expired, deactivate it
                        self.logout_user(session_token)
                
                return None
        
        except Exception as e:
            logger.error(f"Session verification failed: {str(e)}")
            return None
    
    def create_session(self, user_id: int, ip_address: str, expires_hours: int = 24) -> str:
        """Create new user session"""
        session_token = self.generate_secure_token()
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_sessions 
                (user_id, session_token, ip_address, expires_at)
                VALUES (?, ?, ?, ?)
            """, (user_id, session_token, ip_address, expires_at))
            conn.commit()
        
        return session_token
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email address"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, email, password_hash, salt, name, phone, is_verified, 
                       login_attempts, locked_until, last_login, created_at
                FROM auth_users 
                WHERE email = ?
            """, (email,))
            
            result = cursor.fetchone()
            
            if result:
                return {
                    "id": result[0],
                    "email": result[1],
                    "password_hash": result[2],
                    "salt": result[3],
                    "name": result[4],
                    "phone": result[5],
                    "is_verified": result[6],
                    "login_attempts": result[7],
                    "locked_until": result[8],
                    "last_login": result[9],
                    "created_at": result[10]
                }
            
            return None
    
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_password(self, password: str) -> Dict:
        """Validate password strength"""
        if len(password) < 8:
            return {"valid": False, "message": "Password must be at least 8 characters long"}
        
        if not any(c.isupper() for c in password):
            return {"valid": False, "message": "Password must contain at least one uppercase letter"}
        
        if not any(c.islower() for c in password):
            return {"valid": False, "message": "Password must contain at least one lowercase letter"}
        
        if not any(c.isdigit() for c in password):
            return {"valid": False, "message": "Password must contain at least one number"}
        
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            return {"valid": False, "message": "Password must contain at least one special character"}
        
        return {"valid": True, "message": "Password is strong"}
    
    def is_account_locked(self, user_id: int) -> bool:
        """Check if account is locked due to failed attempts"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT login_attempts, locked_until 
                FROM auth_users 
                WHERE id = ?
            """, (user_id,))
            
            result = cursor.fetchone()
            
            if result:
                login_attempts, locked_until = result
                
                # Check if account is locked
                if locked_until and datetime.fromisoformat(locked_until) > datetime.utcnow():
                    return True
                
                # Lock account if too many attempts
                if login_attempts >= 5:
                    lock_until = datetime.utcnow() + timedelta(minutes=15)
                    cursor.execute("""
                        UPDATE auth_users 
                        SET locked_until = ? 
                        WHERE id = ?
                    """, (lock_until, user_id))
                    conn.commit()
                    return True
            
            return False
    
    def increment_login_attempts(self, user_id: int):
        """Increment failed login attempts"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE auth_users 
                SET login_attempts = login_attempts + 1 
                WHERE id = ?
            """, (user_id,))
            conn.commit()
    
    def reset_login_attempts(self, user_id: int):
        """Reset login attempts after successful login"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE auth_users 
                SET login_attempts = 0, locked_until = NULL 
                WHERE id = ?
            """, (user_id,))
            conn.commit()
    
    def update_last_login(self, user_id: int):
        """Update last login timestamp"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE auth_users 
                SET last_login = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (user_id,))
            conn.commit()
    
    def log_login_attempt(self, user_id: Optional[int], ip_address: str, 
                         user_agent: str, success: bool, failure_reason: str = None):
        """Log login attempt for security monitoring"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO login_history 
                (user_id, ip_address, user_agent, success, failure_reason)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, ip_address, user_agent, success, failure_reason))
            conn.commit()
    
    def initiate_password_reset(self, email: str) -> Dict:
        """Initiate password reset process"""
        user = self.get_user_by_email(email)
        
        if not user:
            # Don't reveal if email exists
            return {"success": True, "message": "Reset instructions sent if email exists"}
        
        reset_token = self.generate_secure_token()
        expires_at = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE auth_users 
                SET reset_token = ?, reset_token_expires = ? 
                WHERE id = ?
            """, (reset_token, expires_at, user['id']))
            conn.commit()
        
        logger.info(f"Password reset initiated for: {email}")
        return {
            "success": True, 
            "message": "Reset instructions sent",
            "reset_token": reset_token  # In production, send via email
        }
    
    def verify_email(self, verification_token: str) -> bool:
        """Verify user email address"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE auth_users 
                    SET is_verified = 1, verification_token = NULL 
                    WHERE verification_token = ?
                """, (verification_token,))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"Email verified for token: {verification_token}")
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Email verification failed: {str(e)}")
            return False


# Streamlit Authentication Helper
class StreamlitAuth:
    """Streamlit-specific authentication helpers"""
    
    def __init__(self):
        self.auth_service = AuthService()
    
    def initialize_session_state(self):
        """Initialize authentication session state"""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'user' not in st.session_state:
            st.session_state.user = None
        if 'session_token' not in st.session_state:
            st.session_state.session_token = None
    
    def render_login_form(self):
        """Render login form in Streamlit"""
        st.markdown("""
        <div style='margin: 2rem 0; text-align: center;'>
            <h2 style='color: #ece7e2;'>Sign In to Your Account</h2>
            <p style='color: #7b756a;'>Access your TalkingPhoto dashboard</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            email = st.text_input("Email Address", placeholder="your@email.com")
            password = st.text_input("Password", type="password")
            
            col1, col2 = st.columns(2)
            with col1:
                login_button = st.form_submit_button("Sign In", use_container_width=True)
            with col2:
                forgot_password = st.form_submit_button("Forgot Password?", use_container_width=True)
            
            if login_button and email and password:
                result = self.auth_service.login_user(email, password)
                
                if result["success"]:
                    st.session_state.authenticated = True
                    st.session_state.user = result["user"]
                    st.session_state.session_token = result["session_token"]
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error(result["message"])
            
            if forgot_password and email:
                result = self.auth_service.initiate_password_reset(email)
                st.info(result["message"])
    
    def render_registration_form(self):
        """Render registration form in Streamlit"""
        st.markdown("""
        <div style='margin: 2rem 0; text-align: center;'>
            <h2 style='color: #ece7e2;'>Create Your Account</h2>
            <p style='color: #7b756a;'>Join thousands of creators using TalkingPhoto</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("registration_form"):
            name = st.text_input("Full Name", placeholder="John Doe")
            email = st.text_input("Email Address", placeholder="your@email.com")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            agree_terms = st.checkbox("I agree to the Terms of Service and Privacy Policy")
            
            register_button = st.form_submit_button("Create Account", use_container_width=True)
            
            if register_button and all([name, email, password, confirm_password, agree_terms]):
                if password != confirm_password:
                    st.error("Passwords do not match")
                    return
                
                result = self.auth_service.register_user(email, password, name)
                
                if result["success"]:
                    st.success("Registration successful! Please check your email to verify your account.")
                else:
                    st.error(result["message"])
    
    def check_authentication(self) -> bool:
        """Check if user is authenticated"""
        if st.session_state.get('session_token'):
            user = self.auth_service.verify_session(st.session_state.session_token)
            if user:
                st.session_state.authenticated = True
                st.session_state.user = user
                return True
        
        st.session_state.authenticated = False
        st.session_state.user = None
        return False
    
    def logout(self):
        """Logout current user"""
        if st.session_state.get('session_token'):
            self.auth_service.logout_user(st.session_state.session_token)
        
        st.session_state.authenticated = False
        st.session_state.user = None
        st.session_state.session_token = None
        st.rerun()
    
    def render_user_menu(self):
        """Render user menu in sidebar"""
        if st.session_state.authenticated:
            with st.sidebar:
                st.markdown(f"**Welcome, {st.session_state.user['name']}!**")
                
                if st.button("🚪 Logout"):
                    self.logout()
                
                if st.button("👤 Account Settings"):
                    st.session_state.show_account = True
                
                if st.button("💳 Billing & Credits"):
                    st.session_state.show_billing = True


# Global instances
auth_service = AuthService()
streamlit_auth = StreamlitAuth()