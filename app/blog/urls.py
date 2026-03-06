"""
URL patterns for the Blog app.

Each line says: "when someone visits THIS URL, run THIS view function."

Examples:
  '' (empty) = homepage at http://localhost:8000/
  'posts/<slug>/' = post detail at http://localhost:8000/posts/my-article/
"""
from django.urls import path
from . import views

urlpatterns = [
    # Homepage - list of all published posts
    path('', views.post_list, name='post_list'),

    # Create a new post (login required)
    path('posts/create/', views.post_create, name='post_create'),

    # Individual post page
    path('posts/<slug:slug>/', views.post_detail, name='post_detail'),

    # Edit an existing post (login required, must be author)
    path('posts/<slug:slug>/edit/', views.post_edit, name='post_edit'),

    # Add a comment to a post (login required)
    path('posts/<slug:slug>/comment/', views.comment_add, name='comment_add'),

    # User registration
    path('register/', views.register, name='register'),

    # Health check endpoint (used by monitoring services)
    path('health/', views.health_check, name='health_check'),

    # REST API endpoint - returns JSON list of posts
    path('api/posts/', views.PostListAPIView.as_view(), name='api_posts'),
]
