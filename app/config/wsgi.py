"""
WSGI config for CloudBlog.

WSGI stands for "Web Server Gateway Interface". It's the connection point
between the web server (Nginx) and the Django application.
Gunicorn uses this file to run our Django app in production.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

application = get_wsgi_application()
