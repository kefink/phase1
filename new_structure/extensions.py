"""
Flask extensions for the Hillview School Management System.
This file initializes Flask extensions used throughout the application.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

# Initialize extensions
db = SQLAlchemy()
csrf = CSRFProtect()