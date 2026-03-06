"""
Serializers for the CloudBlog REST API.

A serializer converts a Django model object (Python) into JSON format
so it can be sent to other applications or read by JavaScript.

Example output:
{
    "id": 1,
    "title": "My First Post",
    "author": "john",
    "category": "Technology",
    "created_at": "2024-01-15T10:30:00Z",
    "published": true
}
"""
from rest_framework import serializers
from .models import Post, Category, Comment


class CategorySerializer(serializers.ModelSerializer):
    """Converts a Category object to/from JSON."""
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']


class CommentSerializer(serializers.ModelSerializer):
    """Converts a Comment object to/from JSON."""
    # Show the username instead of just the user ID number
    author = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'author', 'body', 'created_at']


class PostSerializer(serializers.ModelSerializer):
    """
    Converts a Post object to/from JSON.
    This is what the /api/posts/ endpoint returns.
    """
    # Show username and category name as readable text
    author = serializers.CharField(source='author.username', read_only=True)
    category = CategorySerializer(read_only=True)
    # Include the comments on this post
    comments = CommentSerializer(many=True, read_only=True)
    comment_count = serializers.IntegerField(source='get_comment_count', read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'author', 'category',
            'body', 'created_at', 'published', 'comment_count', 'comments'
        ]
