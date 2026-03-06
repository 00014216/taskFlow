"""
Database models for CloudBlog.

A model is a Python class that represents a database table.
Each attribute of the class becomes a column in the table.

We have three models:
1. Category - organises posts into topics (e.g. "Technology", "Sports")
2. Post - a single news/blog article
3. Comment - a reader's reply to a post
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class Category(models.Model):
    """
    A category groups related posts together.
    Example: "Technology", "Sports", "World News"
    """
    name = models.CharField(max_length=100)
    # A slug is a URL-friendly version of the name: "World News" -> "world-news"
    slug = models.SlugField(unique=True, max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        # This controls how the category appears in the Django admin panel
        return self.name

    def save(self, *args, **kwargs):
        # Automatically create a slug from the name if not provided
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Post(models.Model):
    """
    A single blog/news article.
    Links to a Category and to the User who wrote it.
    """
    title = models.CharField(max_length=200)
    # Slug makes the URL clean: /posts/my-article/ instead of /posts/1/
    slug = models.SlugField(unique=True, max_length=200)
    # ForeignKey means "each post belongs to one category"
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,  # If category deleted, keep the post (set category to null)
        null=True,
        blank=True,
        related_name='posts'
    )
    # ForeignKey to User: each post has one author
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,  # If user deleted, delete their posts too
        related_name='posts'
    )
    # The main body of the article
    body = models.TextField()
    # auto_now_add=True automatically sets this to "now" when the post is created
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Only published posts appear on the homepage
    published = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']  # Newest posts first

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Automatically create a slug from the title
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_comment_count(self):
        """Return the number of comments on this post."""
        return self.comments.count()


class Comment(models.Model):
    """
    A reader's comment on a post.
    Each comment belongs to one post and one user.
    """
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,  # If post deleted, delete all its comments
        related_name='comments'    # Lets us write: post.comments.all()
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']  # Oldest comment first (like a conversation)

    def __str__(self):
        return f'Comment by {self.author.username} on "{self.post.title}"'
