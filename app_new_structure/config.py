"""
Configuration settings for the Hillview School Management System.
This file defines different configuration classes for various environments.
"""
import os

class Config:
    """Base configuration class with settings common to all environments."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key_here'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Use the same database file path as the original application
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'kirima_primary.db')


class DevelopmentConfig(Config):
    """Configuration for development environment."""
    DEBUG = True


class TestingConfig(Config):
    """Configuration for testing environment."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


class ProductionConfig(Config):
    """Configuration for production environment."""
    DEBUG = False
    # In production, you might want to use a different database
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')


# Configuration dictionary to easily select environment
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
