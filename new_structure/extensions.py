"""
Flask extensions for the Hillview School Management System.
This file initializes Flask extensions used throughout the application.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize extensions
db = SQLAlchemy()
csrf = CSRFProtect()
limiter = Limiter(
	key_func=get_remote_address,
	storage_uri=None  # Will default to in-memory; create_app will override via app.config['RATELIMIT_STORAGE_URL'] if set
)