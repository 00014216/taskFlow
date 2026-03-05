"""
URL Configuration for TaskFlow.

This file tells Django which URL patterns map to which views.
Think of it like a menu: when someone visits /admin/, go to the admin panel.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django's built-in admin panel at /admin/
    path('admin/', admin.site.urls),

    # Our tasks app handles all other URLs
    path('', include('tasks.urls')),

    # Django's built-in login/logout views (provides /login/ and /logout/)
    path('', include('django.contrib.auth.urls')),
]

# In development, also serve uploaded media files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
