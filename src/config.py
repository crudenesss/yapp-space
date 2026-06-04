"""Application configuration"""

import os
from datetime import timedelta
from core.constants import SESSION_EXPIRY


class Config:
    """Base Flask application configuration"""
    
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
    
    # JWT Configuration
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=SESSION_EXPIRY)
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_CSRF_CHECK_FORM = True
    
    # Content validation
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
