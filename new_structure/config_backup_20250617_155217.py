"""
Configuration settings for the Hillview School Management System.
"""
import os

class Config:
    """Base configuration class with settings common to all environments."""
    SECRET_KEY = 'your_secret_key_here'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Use the kirima_primary.db database file in the project root
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'kirima_primary.db')

    # Session configuration for better persistence
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours in seconds
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'


class DevelopmentConfig(Config):
    """Configuration for development environment."""
    DEBUG = True
    SERVER_NAME = 'localhost:5000'
    APPLICATION_ROOT = '/'
    PREFERRED_URL_SCHEME = 'http'


class TestingConfig(Config):
    """Configuration for testing environment."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


class ProductionConfig(Config):
    """Configuration for production environment."""
    DEBUG = False


# Configuration dictionary to easily select environment
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}