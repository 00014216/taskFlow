"""
Tests for CloudBlog.

Tests are automated checks that verify our code works correctly.
Run them with: docker compose exec web pytest

Why tests matter for CI/CD:
- Every time you push code, GitHub Actions runs these tests automatically
- If tests fail, the code is NOT deployed to the live server
- This prevents broken code from reaching your users
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.cache import cache

from .models import Category, Post, Comment


class CategoryModelTest(TestCase):
    """Tests for the Category model."""

    def test_category_str_method(self):
        """Test that Category.__str__ returns the category name."""
        category = Category.objects.create(name='Technology', slug='technology')
        self.assertEqual(str(category), 'Technology')

    def test_category_slug_auto_generated(self):
        """Test that the slug is automatically created from the name."""
        category = Category.objects.create(name='World News')
        self.assertEqual(category.slug, 'world-news')


class PostModelTest(TestCase):
    """Tests for the Post model."""

    def setUp(self):
        """
        setUp runs before EACH test method.
        We create a user and category that we need for most tests.
        """
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Technology',
            slug='technology'
        )

    def test_post_str_method(self):
        """Test that Post.__str__ returns the post title."""
        post = Post.objects.create(
            title='My First Post',
            author=self.user,
            body='Some content here',
            published=True
        )
        self.assertEqual(str(post), 'My First Post')

    def test_post_slug_auto_generated(self):
        """Test that the slug is automatically generated from the title."""
        post = Post.objects.create(
            title='Hello World Post',
            author=self.user,
            body='Content'
        )
        self.assertEqual(post.slug, 'hello-world-post')

    def test_post_comment_count(self):
        """Test the get_comment_count method."""
        post = Post.objects.create(
            title='Post with Comments',
            author=self.user,
            body='Content',
            published=True
        )
        # No comments yet
        self.assertEqual(post.get_comment_count(), 0)

        # Add a comment
        Comment.objects.create(post=post, author=self.user, body='Nice post!')
        self.assertEqual(post.get_comment_count(), 1)


class HomepageTest(TestCase):
    """Tests for the homepage (post list view)."""

    def setUp(self):
        cache.clear()  # Clear Redis cache before each test
        self.client = Client()
        self.user = User.objects.create_user(
            username='author',
            password='pass123'
        )

    def test_homepage_returns_200(self):
        """The homepage should return HTTP 200 (OK)."""
        response = self.client.get(reverse('post_list'))
        self.assertEqual(response.status_code, 200)

    def test_homepage_shows_published_posts_only(self):
        """Only published posts should appear on the homepage."""
        # Create one published and one unpublished post
        Post.objects.create(
            title='Published Post',
            author=self.user,
            body='Content',
            published=True
        )
        Post.objects.create(
            title='Draft Post',
            author=self.user,
            body='Content',
            published=False  # This should NOT show on homepage
        )

        response = self.client.get(reverse('post_list'))
        self.assertContains(response, 'Published Post')
        self.assertNotContains(response, 'Draft Post')

    def test_homepage_uses_correct_template(self):
        """Homepage should render the post_list.html template."""
        response = self.client.get(reverse('post_list'))
        self.assertTemplateUsed(response, 'blog/post_list.html')


class PostDetailTest(TestCase):
    """Tests for the post detail view."""

    def setUp(self):
        cache.clear()
        self.client = Client()
        self.user = User.objects.create_user(
            username='author',
            password='pass123'
        )
        self.post = Post.objects.create(
            title='Test Article',
            author=self.user,
            body='This is the article content.',
            published=True
        )

    def test_post_detail_returns_200(self):
        """Visiting a valid post URL should return HTTP 200."""
        url = reverse('post_detail', kwargs={'slug': self.post.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_post_detail_shows_content(self):
        """The post body should be visible on the detail page."""
        url = reverse('post_detail', kwargs={'slug': self.post.slug})
        response = self.client.get(url)
        self.assertContains(response, 'This is the article content.')

    def test_unpublished_post_returns_404(self):
        """Trying to access an unpublished post should return HTTP 404 (Not Found)."""
        draft_post = Post.objects.create(
            title='Draft',
            author=self.user,
            body='Not ready yet',
            published=False
        )
        url = reverse('post_detail', kwargs={'slug': draft_post.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class PostCreateTest(TestCase):
    """Tests for creating a new post."""

    def setUp(self):
        cache.clear()
        self.client = Client()
        self.user = User.objects.create_user(
            username='author',
            password='pass123'
        )

    def test_unauthenticated_user_redirected_to_login(self):
        """
        If you're not logged in and try to create a post,
        you should be redirected to the login page.
        """
        response = self.client.get(reverse('post_create'))
        self.assertRedirects(response, '/login/?next=/posts/create/')

    def test_authenticated_user_can_access_create_form(self):
        """A logged-in user should see the post creation form."""
        self.client.login(username='author', password='pass123')
        response = self.client.get(reverse('post_create'))
        self.assertEqual(response.status_code, 200)

    def test_authenticated_user_can_create_post(self):
        """A logged-in user should be able to create a post."""
        self.client.login(username='author', password='pass123')
        response = self.client.post(reverse('post_create'), {
            'title': 'My New Article',
            'body': 'This is the article body content.',
            'published': True,
        })
        # Should redirect after successful creation
        self.assertEqual(response.status_code, 302)
        # Post should now exist in database
        self.assertTrue(Post.objects.filter(title='My New Article').exists())


class HealthCheckTest(TestCase):
    """Tests for the /health/ endpoint."""

    def test_health_check_returns_200(self):
        """Health check should return HTTP 200 when everything is working."""
        response = self.client.get(reverse('health_check'))
        self.assertEqual(response.status_code, 200)

    def test_health_check_returns_json(self):
        """Health check should return JSON format."""
        response = self.client.get(reverse('health_check'))
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_health_check_shows_healthy_status(self):
        """Health check JSON should contain status: healthy."""
        response = self.client.get(reverse('health_check'))
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('database', data)
        self.assertIn('cache', data)
        self.assertIn('timestamp', data)


class APITest(TestCase):
    """Tests for the REST API endpoint."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='apiuser',
            password='pass123'
        )
        Post.objects.create(
            title='API Test Post',
            author=self.user,
            body='Content for API testing',
            published=True
        )

    def test_api_posts_returns_200(self):
        """API endpoint should return HTTP 200."""
        response = self.client.get(reverse('api_posts'))
        self.assertEqual(response.status_code, 200)

    def test_api_posts_returns_json(self):
        """API endpoint should return JSON content type."""
        response = self.client.get(reverse('api_posts'))
        self.assertIn('application/json', response['Content-Type'])

    def test_api_posts_contains_post_data(self):
        """API should return the published post data."""
        response = self.client.get(reverse('api_posts'))
        data = response.json()
        self.assertIn('results', data)
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['title'], 'API Test Post')


class RegistrationTest(TestCase):
    """Tests for user registration."""

    def test_registration_page_returns_200(self):
        """Registration page should be accessible."""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)

    def test_user_can_register(self):
        """A new user should be able to register."""
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        })
        # Should redirect after successful registration
        self.assertEqual(response.status_code, 302)
        # User should now exist
        self.assertTrue(User.objects.filter(username='newuser').exists())
