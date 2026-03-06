"""
Production settings - used when the app runs on the cloud server.
DEBUG=False hides error details from the public for security.
"""
from .base import *  # noqa: F401, F403
from decouple import config, Csv

DEBUG = False

# Only allow connections from your domain and server IP
ALLOWED_HOSTS = config('DJANGO_ALLOWED_HOSTS', cast=Csv())

# CSRF trusted origins - required for Django 4.x when using a reverse proxy
# Set to your server IP or domain in .env
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='', cast=Csv())

# Cookie security - set to False when running on plain HTTP (no SSL)
# Set to True in .env once HTTPS is configured
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=False, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=False, cast=bool)

# Security headers
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = False  # Nginx handles SSL redirect
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
