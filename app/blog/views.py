"""
Views for CloudBlog.

A view is a Python function that:
1. Receives an HTTP request (e.g., someone visits /posts/)
2. Does some work (e.g., loads posts from database)
3. Returns an HTTP response (e.g., shows the HTML page)

This is where Redis caching is used.
"""
import time
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from rest_framework import generics, filters

from .models import Post, Category
from .forms import PostForm, CommentForm, RegisterForm
from .serializers import PostSerializer


# ─────────────────────────────────────────────────────────
# PUBLIC VIEWS (anyone can see these without logging in)
# ─────────────────────────────────────────────────────────

def post_list(request):
    """
    Homepage: shows a paginated list of published posts.

    Redis caching explanation:
    - First visitor: we fetch posts from PostgreSQL and store in Redis for 5 minutes
    - Next 100 visitors: served from Redis (much faster, database not touched)
    - After 5 minutes: cache expires, next request fetches from DB again
    """
    category_slug = request.GET.get('category')
    page_number = request.GET.get('page', 1)

    # Create a unique cache key based on what category and page is being viewed
    cache_key = f'post_list_{category_slug or "all"}_page_{page_number}'

    # Try to get cached data from Redis first
    cached_data = cache.get(cache_key)

    if cached_data:
        # Cache HIT: data was in Redis, no database query needed
        posts = cached_data['posts']
        categories = cached_data['categories']
        current_category = cached_data['current_category']
    else:
        # Cache MISS: data not in Redis, fetch from PostgreSQL database
        categories = Category.objects.all()
        current_category = None

        if category_slug:
            current_category = get_object_or_404(Category, slug=category_slug)
            post_queryset = Post.objects.filter(
                published=True, category=current_category
            ).select_related('author', 'category')
        else:
            post_queryset = Post.objects.filter(
                published=True
            ).select_related('author', 'category')

        # Paginate: show 6 posts per page
        paginator = Paginator(post_queryset, 6)
        posts = paginator.get_page(page_number)

        # Store in Redis for 5 minutes (300 seconds)
        # This means the next 300 seconds of requests won't touch the database
        cache.set(cache_key, {
            'posts': posts,
            'categories': list(categories),
            'current_category': current_category,
        }, timeout=300)

    return render(request, 'blog/post_list.html', {
        'posts': posts,
        'categories': categories,
        'current_category': current_category,
    })


def post_detail(request, slug):
    """
    Shows a single post and its comments.

    Redis is used here to track view counts.
    Instead of updating a database row every time someone views the post,
    we increment a counter in Redis (much faster, no database writes).
    """
    from django.http import Http404
    post = get_object_or_404(Post, slug=slug)

    if not post.published and request.user != post.author:
        raise Http404("No Post matches the given query.")

    comments = post.comments.select_related('author').all()

    # Increment view count in Redis (fast in-memory counter)
    view_count_key = f'post_views_{post.id}'
    view_count = cache.get(view_count_key, 0)
    cache.set(view_count_key, view_count + 1, timeout=None)  # Never expires

    # Comment form for logged-in users
    form = CommentForm()

    return render(request, 'blog/post_detail.html', {
        'post': post,
        'comments': comments,
        'form': form,
        'view_count': view_count + 1,
    })


# ─────────────────────────────────────────────────────────
# AUTHENTICATED VIEWS (must be logged in)
# ─────────────────────────────────────────────────────────

@login_required
def post_create(request):
    """
    Allows a logged-in user to write and publish a new post.
    After saving, we clear the cached post list so the homepage shows the new post.
    """
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user  # The logged-in user is the author
            post.save()

            # Clear cached post lists so the new post appears immediately
            # This is called "cache invalidation"
            # We delete specific known cache keys (avoids needing pattern delete)
            for page in range(1, 20):
                cache.delete(f'post_list_all_page_{page}')
                if post.category:
                    cache.delete(f'post_list_{post.category.slug}_page_{page}')

            messages.success(request, f'Post "{post.title}" created successfully!')
            return redirect('post_detail', slug=post.slug)
    else:
        form = PostForm()

    return render(request, 'blog/post_form.html', {
        'form': form,
        'action': 'Create',
    })


@login_required
def post_edit(request, slug):
    """
    Allows the original author to edit their post.
    """
    post = get_object_or_404(Post, slug=slug, author=request.user)

    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            # Clear cache so updates appear immediately
            for page in range(1, 20):
                cache.delete(f'post_list_all_page_{page}')
                if post.category:
                    cache.delete(f'post_list_{post.category.slug}_page_{page}')
            messages.success(request, f'Post "{post.title}" updated successfully!')
            return redirect('post_detail', slug=post.slug)
    else:
        form = PostForm(instance=post)

    return render(request, 'blog/post_form.html', {
        'form': form,
        'post': post,
        'action': 'Edit',
    })


@login_required
def comment_add(request, slug):
    """
    Adds a comment to a post. Only accepts POST requests.
    """
    post = get_object_or_404(Post, slug=slug, published=True)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            messages.success(request, 'Comment added!')

    return redirect('post_detail', slug=slug)


# ─────────────────────────────────────────────────────────
# USER AUTHENTICATION VIEWS
# ─────────────────────────────────────────────────────────

def register(request):
    """
    User registration page.
    After registering, the user is automatically logged in.
    """
    if request.user.is_authenticated:
        return redirect('post_list')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Automatically log in after registration
            messages.success(request, f'Welcome, {user.username}! Your account was created.')
            return redirect('post_list')
    else:
        form = RegisterForm()

    return render(request, 'registration/register.html', {'form': form})


# ─────────────────────────────────────────────────────────
# HEALTH CHECK ENDPOINT
# ─────────────────────────────────────────────────────────

def health_check(request):
    """
    Health check endpoint at /health/

    This is used by monitoring services to verify the application is running.
    It checks both the database (PostgreSQL) and the cache (Redis).

    Returns JSON like:
    {
        "status": "healthy",
        "database": "connected",
        "cache": "connected",
        "timestamp": 1705312200.0
    }

    If anything is broken, it returns status 503 (Service Unavailable).
    """
    health = {
        'status': 'healthy',
        'database': 'unknown',
        'cache': 'unknown',
        'timestamp': time.time(),
    }

    # Test 1: Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')  # Simplest possible database query
        health['database'] = 'connected'
    except Exception as e:
        health['status'] = 'unhealthy'
        health['database'] = f'error: {str(e)}'

    # Test 2: Check Redis cache connection
    try:
        cache.set('health_check_key', 'ok', timeout=10)
        value = cache.get('health_check_key')
        if value == 'ok':
            health['cache'] = 'connected'
        else:
            health['status'] = 'unhealthy'
            health['cache'] = 'read/write mismatch'
    except Exception as e:
        health['status'] = 'unhealthy'
        health['cache'] = f'error: {str(e)}'

    # Return 200 OK if healthy, 503 Service Unavailable if not
    status_code = 200 if health['status'] == 'healthy' else 503
    return JsonResponse(health, status=status_code)


# ─────────────────────────────────────────────────────────
# REST API VIEWS
# ─────────────────────────────────────────────────────────

class PostListAPIView(generics.ListAPIView):
    """
    REST API endpoint at /api/posts/

    Returns a JSON list of all published posts.
    Supports filtering by category: /api/posts/?search=technology
    This can be used by mobile apps or other services to consume our data.
    """
    serializer_class = PostSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'body', 'author__username']

    def get_queryset(self):
        queryset = Post.objects.filter(published=True).select_related('author', 'category')
        category_slug = self.request.query_params.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        return queryset
