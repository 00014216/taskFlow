"""
Development settings - used when running locally on your computer.
DEBUG=True shows helpful error pages. Never use this in production!
"""
from .base import *  # noqa: F401, F403

DEBUG = True

# In development, allow connections from your own computer
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Show emails in the console during development (not sent for real)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Overrides for local run without docker (SQLite + Local memory cache limit)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',  # noqa: F405
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Override session engine back to Database default since we disabled Redis session caching
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Use simple static files storage in development/tests (no manifest required)
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
