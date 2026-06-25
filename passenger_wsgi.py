"""
Passenger WSGI entry point for cPanel deployment.

This file is used by cPanel's Passenger application server to run the Django application.
It handles the WSGI application initialization and environment setup for cPanel hosting.

Configuration:
- Requires Python 3.8+ (configured in cPanel)
- Uses production settings by default
- Handles static file serving through cPanel's web server
- Supports file-based caching for cPanel environments
- Automatically creates required directories (cache, logs, media)

Usage:
- cPanel Setup Python App should point to this file as the startup file
- Passenger will automatically restart the application when this file is modified
- To restart: touch passenger_wsgi.py
"""
import os
import sys
from pathlib import Path

# ============================================================================
# PROJECT PATH CONFIGURATION
# ============================================================================
# Add the project directory to the Python path so Django can be imported
project_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(project_dir))

# ============================================================================
# ENVIRONMENT SETUP
# ============================================================================
# Set Django settings module to production by default
# Can be overridden by DJANGO_SETTINGS_MODULE environment variable
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

# ============================================================================
# DJANGO WSGI APPLICATION INITIALIZATION
# ============================================================================
# Import and initialize the Django WSGI application
from django.core.wsgi import get_wsgi_application

# Initialize the WSGI application
# This is the entry point that Passenger will call to handle requests
raw_application = get_wsgi_application()

import urllib.parse

class PassengerPathInfoFix:
    """
    WSGI middleware to fix percent-encoded PATH_INFO passed by Passenger.
    Ensures Django receives PATH_INFO correctly formatted as a Latin-1 string
    representing the original raw UTF-8 bytes of the URL.
    """
    def __init__(self, app):
        self.app = app
        
    def __call__(self, environ, start_response):
        path_info = environ.get('PATH_INFO', '')
        if '%' in path_info:
            try:
                # Encode string to bytes using iso-8859-1
                bytes_path = path_info.encode('iso-8859-1')
                # Unquote percent-encoded bytes
                unquoted_bytes = urllib.parse.unquote_to_bytes(bytes_path)
                # Decode back to iso-8859-1 to get a valid WSGI Latin-1 string
                environ['PATH_INFO'] = unquoted_bytes.decode('iso-8859-1')
            except Exception:
                pass
        return self.app(environ, start_response)

application = PassengerPathInfoFix(raw_application)


# ============================================================================
# DIRECTORY INITIALIZATION
# ============================================================================
# Ensure required directories exist for cPanel deployment
# These directories are needed for:
# - cache: File-based caching
# - logs: Application and error logs
# - media: User-uploaded files
# - staticfiles: Collected static files

try:
    # Create cache directory if it doesn't exist
    cache_dir = project_dir / 'cache'
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Create logs directory if it doesn't exist
    logs_dir = project_dir / 'logs'
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Create media directory if it doesn't exist
    media_dir = project_dir / 'media'
    media_dir.mkdir(parents=True, exist_ok=True)
    
    # Create staticfiles directory if it doesn't exist
    staticfiles_dir = project_dir / 'staticfiles'
    staticfiles_dir.mkdir(parents=True, exist_ok=True)
    
except Exception as e:
    # Log any errors during directory creation
    # This shouldn't prevent the application from starting
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Error creating directories: {e}")

# ============================================================================
# PASSENGER WSGI INTERFACE
# ============================================================================
# Passenger expects the 'application' variable to be available at module level
# The above initialization makes it available for Passenger to use
# Passenger will call application(environ, start_response) for each request

