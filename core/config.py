"""
TalkingPhoto AI MVP - Configuration Management

Manages application configuration, environment settings, and feature flags.
Pure Python implementation with no external dependencies.
"""

import os
from typing import Dict, Any, Optional
from enum import Enum


class Environment(Enum):
    """Application environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class FeatureFlag(Enum):
    """Feature flags for gradual rollouts"""
    MOCK_MODE = "mock_mode"
    PAYMENT_ENABLED = "payment_enabled"
    ANALYTICS_ENABLED = "analytics_enabled"
    ERROR_REPORTING = "error_reporting"
    ADVANCED_VALIDATION = "advanced_validation"


class Config:
    """Application configuration management"""
    
    # Default configuration values
    DEFAULT_CONFIG = {
        # Environment
        "environment": Environment.DEVELOPMENT.value,
        
        # Application settings
        "app_name": "TalkingPhoto AI",
        "app_version": "2.0",
        "debug_mode": True,
        
        # File upload limits
        "max_file_size_mb": 200,
        "allowed_file_types": ["image/jpeg", "image/jpg", "image/png"],
        "max_text_length": 1000,
        "min_text_length": 10,
        
        # Credit system
        "default_credits": 1,
        "max_session_generations": 10,
        
        # UI settings
        "primary_color": "#ff882e",
        "secondary_color": "#1a365d",
        "enable_animations": True,
        "mobile_responsive": True,
        
        # Feature flags
        "features": {
            FeatureFlag.MOCK_MODE.value: True,
            FeatureFlag.PAYMENT_ENABLED.value: False,
            FeatureFlag.ANALYTICS_ENABLED.value: False,
            FeatureFlag.ERROR_REPORTING.value: True,
            FeatureFlag.ADVANCED_VALIDATION.value: True
        },
        
        # Processing settings
        "default_processing_timeout": 30,
        "progress_update_interval": 0.1,
        
        # Security settings
        "session_timeout_hours": 24,
        "max_concurrent_sessions": 1000,
        "rate_limit_requests_per_minute": 10
    }
    
    def __init__(self):
        """Initialize configuration"""
        self._config = self.DEFAULT_CONFIG.copy()
        self._load_from_environment()
    
    def _load_from_environment(self) -> None:
        """Load configuration from environment variables"""
        
        # Environment detection
        env = os.getenv("ENVIRONMENT", "development").lower()
        if env in [e.value for e in Environment]:
            self._config["environment"] = env
            self._config["debug_mode"] = env != Environment.PRODUCTION.value
        
        # File upload settings
        if os.getenv("MAX_FILE_SIZE_MB"):
            try:
                self._config["max_file_size_mb"] = int(os.getenv("MAX_FILE_SIZE_MB"))
            except ValueError:
                pass
        
        # Feature flags from environment
        for flag in FeatureFlag:
            env_var = f"FEATURE_{flag.value.upper()}"
            if os.getenv(env_var):
                self._config["features"][flag.value] = os.getenv(env_var).lower() == "true"
        
        # Security settings
        if os.getenv("RATE_LIMIT_RPM"):
            try:
                self._config["rate_limit_requests_per_minute"] = int(os.getenv("RATE_LIMIT_RPM"))
            except ValueError:
                pass
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value
        
        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def is_feature_enabled(self, feature: FeatureFlag) -> bool:
        """
        Check if a feature is enabled
        
        Args:
            feature: Feature flag to check
            
        Returns:
            bool: True if feature is enabled
        """
        return self.get(f"features.{feature.value}", False)
    
    def enable_feature(self, feature: FeatureFlag) -> None:
        """
        Enable a feature
        
        Args:
            feature: Feature to enable
        """
        self.set(f"features.{feature.value}", True)
    
    def disable_feature(self, feature: FeatureFlag) -> None:
        """
        Disable a feature
        
        Args:
            feature: Feature to disable
        """
        self.set(f"features.{feature.value}", False)
    
    def get_environment(self) -> Environment:
        """Get current environment"""
        env_str = self.get("environment", Environment.DEVELOPMENT.value)
        return Environment(env_str)
    
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.get_environment() == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.get_environment() == Environment.DEVELOPMENT
    
    def get_file_upload_config(self) -> Dict[str, Any]:
        """Get file upload configuration"""
        return {
            "max_size_bytes": self.get("max_file_size_mb", 50) * 1024 * 1024,
            "max_size_mb": self.get("max_file_size_mb", 50),
            "allowed_types": self.get("allowed_file_types", []),
            "max_text_length": self.get("max_text_length", 1000),
            "min_text_length": self.get("min_text_length", 10)
        }
    
    def get_ui_config(self) -> Dict[str, Any]:
        """Get UI configuration"""
        return {
            "primary_color": self.get("primary_color", "#ff882e"),
            "secondary_color": self.get("secondary_color", "#1a365d"),
            "enable_animations": self.get("enable_animations", True),
            "mobile_responsive": self.get("mobile_responsive", True),
            "app_name": self.get("app_name", "TalkingPhoto AI"),
            "app_version": self.get("app_version", "2.0")
        }
    
    def get_processing_config(self) -> Dict[str, Any]:
        """Get processing configuration"""
        return {
            "timeout_seconds": self.get("default_processing_timeout", 30),
            "progress_interval": self.get("progress_update_interval", 0.1),
            "mock_mode": self.is_feature_enabled(FeatureFlag.MOCK_MODE)
        }
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration"""
        return {
            "session_timeout_hours": self.get("session_timeout_hours", 24),
            "max_concurrent_sessions": self.get("max_concurrent_sessions", 1000),
            "rate_limit_rpm": self.get("rate_limit_requests_per_minute", 10)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as dictionary"""
        return self._config.copy()
    
    def get_debug_info(self) -> Dict[str, Any]:
        """Get debug information about configuration"""
        return {
            "environment": self.get_environment().value,
            "debug_mode": self.get("debug_mode", False),
            "features_enabled": [
                flag.value for flag in FeatureFlag 
                if self.is_feature_enabled(flag)
            ],
            "config_keys": list(self._config.keys())
        }


# Global configuration instance
config = Config()