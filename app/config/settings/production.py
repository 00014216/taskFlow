"""
Production settings - used when the app runs on the Azure cloud server.
DEBUG=False hides error details from the public for security.
"""
from .base import *  # noqa: F401, F403
from decouple import config, Csv

DEBUG = False

# Only allow connections from your domain and server IP
ALLOWED_HOSTS = config('DJANGO_ALLOWED_HOSTS', cast=Csv())

# Security settings - enforce HTTPS in production
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = False  # Nginx handles the redirect
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
