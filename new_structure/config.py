"""
Configuration settings for the Hillview School Management System.
Updated for MySQL database.
"""
import os

class Config:
    """Base configuration class with settings common to all environments."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key_here_change_in_production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # MySQL Configuration
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT') or 3306)
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'hillview_demo001_user'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or 'hillview_demo_pass_2024'
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


class DevelopmentConfig(Config):
    """Configuration for development environment."""
    DEBUG = True
    SERVER_NAME = 'localhost:5000'
    APPLICATION_ROOT = '/'
    PREFERRED_URL_SCHEME = 'http'


class TestingConfig(Config):
    """Configuration for testing environment."""
    TESTING = True


class ProductionConfig(Config):
    """Configuration for production environment."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
