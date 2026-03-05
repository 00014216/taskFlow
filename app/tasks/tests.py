"""
Tests for TaskFlow.

Run with: docker compose exec web pytest
All tests must pass before GitHub Actions deploys to production.

We test:
- Models (str methods, relationships)
- Views (status codes, redirects, permissions)
- CRUD operations (create, read, update, delete)
- Health check (database + Redis)
- REST API
- Authentication (login required redirects)
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.cache import cache

from .models import Label, Project, Task


class LabelModelTest(TestCase):
    def test_label_str(self):
        label = Label.objects.create(name='Bug', color='#dc3545')
        self.assertEqual(str(label), 'Bug')

    def test_label_default_color(self):
        label = Label.objects.create(name='Feature')
        self.assertEqual(label.color, '#6c757d')


class ProjectModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', password='pass123')

    def test_project_str(self):
        project = Project.objects.create(owner=self.user, name='My Project')
        self.assertEqual(str(project), 'My Project')

    def test_project_completion_percent_empty(self):
        project = Project.objects.create(owner=self.user, name='Empty Project')
        self.assertEqual(project.completion_percent(), 0)

    def test_project_completion_percent_with_tasks(self):
        project = Project.objects.create(owner=self.user, name='Active Project')
        Task.objects.create(
            project=project, created_by=self.user,
            title='Done Task', status=Task.STATUS_DONE
        )
        Task.objects.create(
            project=project, created_by=self.user,
            title='Todo Task', status=Task.STATUS_TODO
        )
        self.assertEqual(project.completion_percent(), 50)


class TaskModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', password='pass123')
        self.project = Project.objects.create(owner=self.user, name='Test Project')

    def test_task_str(self):
        task = Task.objects.create(
            project=self.project, created_by=self.user, title='Fix the bug'
        )
        self.assertEqual(str(task), 'Fix the bug')

    def test_task_many_to_many_labels(self):
        """
        Tests the M2M relationship: one task can have multiple labels,
        and one label can be on multiple tasks.
        """
        bug_label = Label.objects.create(name='Bug', color='#dc3545')
        urgent_label = Label.objects.create(name='Urgent', color='#ffc107')

        task = Task.objects.create(
            project=self.project, created_by=self.user, title='Critical bug'
        )
        task.labels.add(bug_label, urgent_label)

        self.assertEqual(task.labels.count(), 2)
        self.assertIn(bug_label, task.labels.all())
        self.assertIn(urgent_label, task.labels.all())
        # Reverse: label can access all tasks that use it
        self.assertIn(task, bug_label.tasks.all())

    def test_task_status_badge_color(self):
        task = Task.objects.create(
            project=self.project, created_by=self.user,
            title='T', status=Task.STATUS_DONE
        )
        self.assertEqual(task.status_badge_color(), 'success')

    def test_task_priority_badge_color(self):
        task = Task.objects.create(
            project=self.project, created_by=self.user,
            title='T', priority=Task.PRIORITY_HIGH
        )
        self.assertEqual(task.priority_badge_color(), 'danger')


class LandingPageTest(TestCase):
    def test_landing_page_returns_200(self):
        response = self.client.get(reverse('landing'))
        self.assertEqual(response.status_code, 200)

    def test_landing_redirects_authenticated_user(self):
        user = User.objects.create_user('u', password='p')
        self.client.login(username='u', password='p')
        response = self.client.get(reverse('landing'))
        self.assertRedirects(response, reverse('dashboard'))


class AuthenticationTest(TestCase):
    def test_register_page_returns_200(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)

    def test_user_can_register(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@test.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, '/login/?next=/dashboard/')

    def test_project_create_requires_login(self):
        response = self.client.get(reverse('project_create'))
        self.assertEqual(response.status_code, 302)


class ProjectCRUDTest(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.user = User.objects.create_user('owner', password='pass123')
        self.client.login(username='owner', password='pass123')
        self.project = Project.objects.create(owner=self.user, name='Test Project')

    def test_dashboard_returns_200(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_project_detail_returns_200(self):
        response = self.client.get(reverse('project_detail', args=[self.project.pk]))
        self.assertEqual(response.status_code, 200)

    def test_create_project(self):
        response = self.client.post(reverse('project_create'), {
            'name': 'New Project',
            'description': 'A test project',
            'status': 'active',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Project.objects.filter(name='New Project').exists())

    def test_edit_project(self):
        response = self.client.post(
            reverse('project_edit', args=[self.project.pk]),
            {'name': 'Renamed Project', 'description': '', 'status': 'active'}
        )
        self.assertEqual(response.status_code, 302)
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, 'Renamed Project')

    def test_delete_project(self):
        response = self.client.post(reverse('project_delete', args=[self.project.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Project.objects.filter(pk=self.project.pk).exists())

    def test_other_user_cannot_access_project(self):
        other = User.objects.create_user('other', password='pass123')
        self.client.login(username='other', password='pass123')
        response = self.client.get(reverse('project_detail', args=[self.project.pk]))
        self.assertEqual(response.status_code, 404)


class TaskCRUDTest(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.user = User.objects.create_user('owner', password='pass123')
        self.client.login(username='owner', password='pass123')
        self.project = Project.objects.create(owner=self.user, name='Test Project')
        self.label = Label.objects.create(name='Bug', color='#dc3545')
        self.task = Task.objects.create(
            project=self.project, created_by=self.user, title='Test Task'
        )

    def test_task_detail_returns_200(self):
        response = self.client.get(reverse('task_detail', args=[self.task.pk]))
        self.assertEqual(response.status_code, 200)

    def test_create_task_with_labels(self):
        """Tests full task creation including Many-to-Many label assignment."""
        response = self.client.post(
            reverse('task_create', args=[self.project.pk]),
            {
                'title': 'New Task with Labels',
                'description': 'Testing M2M',
                'status': Task.STATUS_TODO,
                'priority': Task.PRIORITY_HIGH,
                'labels': [self.label.pk],  # M2M field
            }
        )
        self.assertEqual(response.status_code, 302)
        task = Task.objects.get(title='New Task with Labels')
        self.assertIn(self.label, task.labels.all())

    def test_edit_task(self):
        response = self.client.post(
            reverse('task_edit', args=[self.task.pk]),
            {
                'title': 'Updated Task',
                'description': '',
                'status': Task.STATUS_DONE,
                'priority': Task.PRIORITY_LOW,
                'labels': [],
            }
        )
        self.assertEqual(response.status_code, 302)
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, 'Updated Task')
        self.assertEqual(self.task.status, Task.STATUS_DONE)

    def test_delete_task(self):
        response = self.client.post(reverse('task_delete', args=[self.task.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Task.objects.filter(pk=self.task.pk).exists())


class HealthCheckTest(TestCase):
    def test_health_check_returns_200(self):
        response = self.client.get(reverse('health_check'))
        self.assertEqual(response.status_code, 200)

    def test_health_check_returns_json(self):
        response = self.client.get(reverse('health_check'))
        data = response.json()
        self.assertIn('status', data)
        self.assertIn('database', data)
        self.assertIn('cache', data)
        self.assertIn('timestamp', data)

    def test_health_check_is_healthy(self):
        response = self.client.get(reverse('health_check'))
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['database'], 'connected')


class APITest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('apiuser', password='pass123')
        self.client.login(username='apiuser', password='pass123')
        project = Project.objects.create(owner=self.user, name='API Project')
        Task.objects.create(
            project=project, created_by=self.user, title='API Task'
        )

    def test_api_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse('api_tasks'))
        self.assertEqual(response.status_code, 403)

    def test_api_returns_200_when_authenticated(self):
        response = self.client.get(reverse('api_tasks'))
        self.assertEqual(response.status_code, 200)

    def test_api_returns_json(self):
        response = self.client.get(reverse('api_tasks'))
        data = response.json()
        self.assertIn('results', data)
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['title'], 'API Task')
