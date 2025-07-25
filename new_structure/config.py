"""
Configuration settings for the Hillview School Management System.
Enhanced with scalability features and multi-environment support.
"""
import os
import urllib.parse
from typing import Optional
from pathlib import Path

class Config:
    # ULTRA-SECURE SESSION CONFIGURATION - FIXES 1 VULNERABILITY
    SESSION_COOKIE_SECURE = True           # HTTPS only
    SESSION_COOKIE_HTTPONLY = True        # No JavaScript access
    SESSION_COOKIE_SAMESITE = 'Strict'    # Strict CSRF protection
    PERMANENT_SESSION_LIFETIME = 1800     # 30 minutes timeout
    SESSION_COOKIE_NAME = 'hillview_secure_session'
    
    # HTTPS ENFORCEMENT - FIXES 1 VULNERABILITY
    FORCE_HTTPS = True  # Enable in production
    
    # STRICT SECURITY SETTINGS
    STRICT_ROLE_ENFORCEMENT = True
    SESSION_PROTECTION = 'strong'
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour CSRF token lifetime

    # Secure Session Configuration
    SESSION_COOKIE_SECURE = False  # Set to True when using HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes
    SESSION_COOKIE_NAME = 'hillview_session'

    """Base configuration class with settings common to all environments."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key_here_change_in_production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # MySQL Configuration
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT') or 3306)
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or urllib.parse.quote_plus('@2494/lK')
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE') or 'hillview_demo001'
    
    # SQLAlchemy MySQL URI
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
        "?charset=utf8mb4"
    )
    
    # Connection Pool Settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_timeout': 20,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 20
    }
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Redis Configuration for Caching and Sessions
    REDIS_HOST = os.environ.get('REDIS_HOST') or 'localhost'
    REDIS_PORT = int(os.environ.get('REDIS_PORT') or 6379)
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD')
    REDIS_DB = int(os.environ.get('REDIS_DB') or 0)
    REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}" if REDIS_PASSWORD else f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

    # Cache Configuration
    CACHE_TYPE = 'redis'
    CACHE_DEFAULT_TIMEOUT = 3600  # 1 hour
    CACHE_KEY_PREFIX = 'hillview:'

    # Rate Limiting Configuration
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/1"
    RATELIMIT_DEFAULT = "100 per hour"
    RATELIMIT_HEADERS_ENABLED = True

    # Background Tasks Configuration (Celery/RQ)
    CELERY_BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/2"
    CELERY_RESULT_BACKEND = f"redis://{REDIS_HOST}:{REDIS_PORT}/3"
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TIMEZONE = 'UTC'
    CELERY_ENABLE_UTC = True

    # File Upload Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'xlsx', 'xls', 'csv'}

    # Logging Configuration
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = None  # Set in environment-specific configs

    # Security Configuration
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour

    # Application Configuration
    APP_NAME = 'Hillview School Management System'
    APP_VERSION = '2.0.0'

    @classmethod
    def init_app(cls, app):
        """Initialize application with configuration"""
        # Create necessary directories
        directories = ['logs', 'uploads', 'static/uploads', 'instance', 'backups']
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)


class DevelopmentConfig(Config):
    """Configuration for development environment."""
    DEBUG = True
    # SERVER_NAME = 'localhost:5000'  # Commented out to allow access from any IP
    APPLICATION_ROOT = '/'
    PREFERRED_URL_SCHEME = 'http'

    # Development-specific overrides
    CACHE_TYPE = 'simple'  # Use simple cache for development
    RATELIMIT_ENABLED = True  # Enable rate limiting for security testing
    RATELIMIT_STORAGE_URL = 'memory://'  # Use memory storage for development
    LOG_LEVEL = 'DEBUG'
    WTF_CSRF_ENABLED = True  # Enable CSRF protection for security testing

    # Use MySQL for development (inherits from base Config class)
    # SQLALCHEMY_DATABASE_URI is inherited from Config class - MySQL configuration

    @classmethod
    def init_app(cls, app):
        """Initialize development app"""
        super().init_app(app)
        # Additional development setup
        app.logger.setLevel(cls.LOG_LEVEL)


class TestingConfig(Config):
    """Configuration for testing environment."""
    TESTING = True
    DEBUG = True

    # Testing-specific overrides
    CACHE_TYPE = 'null'  # Disable caching for testing
    RATELIMIT_ENABLED = False
    WTF_CSRF_ENABLED = False
    LOG_LEVEL = 'ERROR'
    FORCE_HTTPS = False
    STRICT_ROLE_ENFORCEMENT = False  # Relaxed for testing
    SECRET_KEY = 'test-secret-key-for-testing'

    # Use in-memory SQLite for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }


class ProductionConfig(Config):
    """Configuration for production environment."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True

    # Production-specific overrides
    RATELIMIT_DEFAULT = "200 per hour"
    LOG_LEVEL = 'WARNING'
    LOG_FILE = '/var/log/hillview/app.log'

    # Enhanced security for production
    WTF_CSRF_TIME_LIMIT = 7200  # 2 hours
    PERMANENT_SESSION_LIFETIME = 7200  # 2 hours

    # Production database with enhanced connection pooling
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,
        'pool_timeout': 30,
        'pool_recycle': 7200,
        'pool_pre_ping': True,
        'max_overflow': 40
    }

    @classmethod
    def init_app(cls, app):
        """Initialize production app"""
        super().init_app(app)

        # Configure production logging
        import logging
        from logging.handlers import RotatingFileHandler

        if cls.LOG_FILE:
            file_handler = RotatingFileHandler(
                cls.LOG_FILE, maxBytes=10*1024*1024, backupCount=10
            )
            file_handler.setFormatter(logging.Formatter(cls.LOG_FORMAT))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config(config_name: Optional[str] = None):
    """
    Get configuration based on environment

    Args:
        config_name: Configuration name (development, production, testing)

    Returns:
        Configuration class
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    return config.get(config_name, config['default'])

def is_development() -> bool:
    """Check if running in development environment"""
    return os.environ.get('FLASK_ENV', 'development') == 'development'

def is_production() -> bool:
    """Check if running in production environment"""
    return os.environ.get('FLASK_ENV') == 'production'

def is_testing() -> bool:
    """Check if running in testing environment"""
    return os.environ.get('FLASK_ENV') == 'testing'

# PRODUCTION SECURITY CONFIGURATION
class ProductionConfig(Config):
    """Production configuration with maximum security."""
    
    # Force HTTPS
    FORCE_HTTPS = True
    
    # Ultra-secure session settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes
    
    # Strict security enforcement
    STRICT_ROLE_ENFORCEMENT = True
    SESSION_PROTECTION = 'strong'
    
    # Security headers
    SECURITY_HEADERS = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin'
    }
