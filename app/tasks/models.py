"""
Database models for TaskFlow.

We have THREE models demonstrating all required relationships:

  Label   ←──────────── Many-to-Many ──────────────→  Task
  (tags like "Bug", "Feature")              (linked via task.labels)

  User ──────── One-to-Many ──────→  Project ──── One-to-Many ──→  Task
  (one user has many projects)      (one project has many tasks)

Database relationships demonstrated:
  - Many-to-One (ForeignKey): Task → Project, Project → User
  - Many-to-Many: Task ↔ Label
"""

from django.db import models
from django.contrib.auth.models import User


class Label(models.Model):
    """
    A coloured tag that can be applied to any task.
    Examples: "Bug", "Feature", "Urgent", "In Review"

    Used in a Many-to-Many relationship with Task.
    One task can have multiple labels; one label can be on many tasks.
    """
    name = models.CharField(max_length=50, unique=True)
    # Hex colour code for the badge, e.g. "#dc3545" = red
    color = models.CharField(max_length=7, default='#6c757d')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Project(models.Model):
    """
    A project groups related tasks together.
    Each project belongs to one user (owner).

    Relationship: User → Project (Many-to-One / ForeignKey)
    """
    STATUS_ACTIVE = 'active'
    STATUS_ARCHIVED = 'archived'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_ARCHIVED, 'Archived'),
    ]

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,   # Delete projects when user is deleted
        related_name='projects'     # user.projects.all() returns all projects
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def task_count(self):
        return self.tasks.count()

    def done_count(self):
        return self.tasks.filter(status=Task.STATUS_DONE).count()

    def completion_percent(self):
        total = self.task_count()
        if total == 0:
            return 0
        return int((self.done_count() / total) * 100)


class Task(models.Model):
    """
    A single task (work item) within a project.

    Relationships:
      - Task → Project: Many-to-One (ForeignKey)
      - Task → User: Many-to-One (who created it)
      - Task ↔ Label: Many-to-Many (a task can have multiple labels)

    The Many-to-Many with Label is the key relationship CW requires.
    Django creates a hidden join table automatically for this.
    """
    # ── Status Choices ─────────────────────────────────────
    STATUS_TODO = 'todo'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_DONE = 'done'
    STATUS_CHOICES = [
        (STATUS_TODO, 'To Do'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_DONE, 'Done'),
    ]

    # ── Priority Choices ────────────────────────────────────
    PRIORITY_LOW = 'low'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_HIGH = 'high'
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Low'),
        (PRIORITY_MEDIUM, 'Medium'),
        (PRIORITY_HIGH, 'High'),
    ]

    # ── Fields ─────────────────────────────────────────────
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='tasks'        # project.tasks.all() returns all tasks
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_TODO
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default=PRIORITY_MEDIUM
    )
    # ── MANY-TO-MANY RELATIONSHIP ───────────────────────────
    # A task can have zero or more labels
    # A label can be applied to zero or more tasks
    # Django creates a join table: tasks_task_labels (task_id, label_id)
    labels = models.ManyToManyField(
        Label,
        blank=True,
        related_name='tasks'
    )
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def status_badge_color(self):
        """Return Bootstrap color class for this task's status."""
        return {
            self.STATUS_TODO: 'secondary',
            self.STATUS_IN_PROGRESS: 'primary',
            self.STATUS_DONE: 'success',
        }.get(self.status, 'secondary')

    def priority_badge_color(self):
        """Return Bootstrap color class for this task's priority."""
        return {
            self.PRIORITY_LOW: 'success',
            self.PRIORITY_MEDIUM: 'warning',
            self.PRIORITY_HIGH: 'danger',
        }.get(self.priority, 'secondary')
