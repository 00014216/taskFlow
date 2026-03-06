"""
Django Admin configuration for CloudBlog.

The Django admin panel is a built-in feature that lets you manage
your database through a web interface, without writing any code.

Visit http://localhost:8000/admin/ after creating a superuser.
"""
from django.contrib import admin
from .models import Category, Post, Comment


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Configuration for the Category admin panel."""
    # Columns shown in the list view
    list_display = ['name', 'slug', 'post_count']
    # Make the slug auto-populate from the name
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']

    def post_count(self, obj):
        """Custom column showing how many posts are in this category."""
        return obj.posts.count()
    post_count.short_description = 'Posts'


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Configuration for the Post admin panel."""
    list_display = ['title', 'author', 'category', 'published', 'created_at']
    list_filter = ['published', 'category', 'created_at']
    search_fields = ['title', 'body', 'author__username']
    # Make the slug auto-populate from the title
    prepopulated_fields = {'slug': ('title',)}
    # Quick toggle: click "published" directly in the list
    list_editable = ['published']
    # Group fields in the edit form
    fieldsets = (
        ('Content', {
            'fields': ('title', 'slug', 'category', 'body')
        }),
        ('Publishing', {
            'fields': ('author', 'published')
        }),
    )
    raw_id_fields = ['author']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Configuration for the Comment admin panel."""
    list_display = ['author', 'post', 'created_at']
    list_filter = ['created_at']
    search_fields = ['body', 'author__username', 'post__title']


# Customize the admin panel header
admin.site.site_header = 'CloudBlog Administration'
admin.site.site_title = 'CloudBlog Admin'
admin.site.index_title = 'Welcome to CloudBlog Admin Panel'
