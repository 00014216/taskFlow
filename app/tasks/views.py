"""
Views for TaskFlow.

Each view is a function that:
  1. Receives an HTTP request
  2. Does work (database queries, cache reads, etc.)
  3. Returns an HTTP response (HTML page or JSON)

Pages available:
  /                     - Landing page (public)
  /dashboard/           - User dashboard (login required)
  /projects/            - All projects list
  /projects/create/     - Create new project
  /projects/<id>/       - Project detail with tasks
  /projects/<id>/edit/  - Edit project
  /tasks/<id>/          - Task detail
  /tasks/create/<proj_id>/  - Create task in project
  /tasks/<id>/edit/     - Edit task
  /tasks/<id>/delete/   - Delete task (with confirmation)
  /labels/              - Manage labels
  /register/            - User registration
  /health/              - Health check (JSON)
  /api/tasks/           - REST API (JSON)
"""
import json
import time
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_POST
from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated

from .models import Project, Task, Label
from .forms import ProjectForm, TaskForm, LabelForm, RegisterForm
from .serializers import TaskSerializer

# Colour palette offered on the Labels page (hex, friendly name)
LABEL_PALETTE = [
    ('#e74c3c', 'Red'),
    ('#e67e22', 'Orange'),
    ('#f1c40f', 'Yellow'),
    ('#2ecc71', 'Green'),
    ('#1abc9c', 'Teal'),
    ('#3498db', 'Blue'),
    ('#9b59b6', 'Purple'),
    ('#e91e63', 'Pink'),
    ('#607d8b', 'Grey'),
    ('#795548', 'Brown'),
]


# ─────────────────────────────────────────────────────────────
# PUBLIC VIEW
# ─────────────────────────────────────────────────────────────

def landing(request):
    """
    Public landing page — shown to visitors who are not logged in.
    Shows what the app does and prompts them to register or log in.
    Logged-in users are redirected to the dashboard.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'tasks/landing.html')


# ─────────────────────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    """
    User dashboard — overview of all the user's projects.

    Redis caching: stats are cached for 2 minutes so the database
    is not queried on every page load. Cache is cleared when
    a project or task is created/modified.
    """
    cache_key = f'dashboard_stats_{request.user.id}'
    stats = cache.get(cache_key)

    if not stats:
        projects = Project.objects.filter(
            owner=request.user
        ).prefetch_related('tasks').order_by('-created_at')

        total_tasks = sum(p.task_count() for p in projects)
        done_tasks = sum(p.done_count() for p in projects)

        stats = {
            'projects': list(projects),
            'total_projects': len(list(projects)),
            'total_tasks': total_tasks,
            'done_tasks': done_tasks,
            'in_progress_tasks': sum(
                p.tasks.filter(status=Task.STATUS_IN_PROGRESS).count()
                for p in projects
            ),
        }
        cache.set(cache_key, stats, timeout=120)

    return render(request, 'tasks/dashboard.html', stats)


# ─────────────────────────────────────────────────────────────
# PROJECT VIEWS
# ─────────────────────────────────────────────────────────────

@login_required
def project_list(request):
    """Show all projects owned by the current user."""
    projects = Project.objects.filter(
        owner=request.user
    ).prefetch_related('tasks')
    return render(request, 'tasks/project_list.html', {'projects': projects})


@login_required
def project_create(request):
    """Create a new project."""
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            cache.delete(f'dashboard_stats_{request.user.id}')
            messages.success(request, f'Project "{project.name}" created!')
            return redirect('project_detail', pk=project.pk)
    else:
        form = ProjectForm()
    return render(request, 'tasks/project_form.html', {
        'form': form,
        'action': 'Create',
        'title': 'New Project',
    })


@login_required
def project_detail(request, pk):
    """Show a project and all its tasks, grouped by status."""
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    tasks = project.tasks.prefetch_related('labels').select_related('created_by')
    return render(request, 'tasks/project_detail.html', {
        'project': project,
        'tasks': tasks,
        'todo_tasks': tasks.filter(status=Task.STATUS_TODO),
        'in_progress_tasks': tasks.filter(status=Task.STATUS_IN_PROGRESS),
        'done_tasks': tasks.filter(status=Task.STATUS_DONE),
    })


@login_required
def project_edit(request, pk):
    """Edit an existing project."""
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            cache.delete(f'dashboard_stats_{request.user.id}')
            messages.success(request, f'Project "{project.name}" updated!')
            return redirect('project_detail', pk=project.pk)
    else:
        form = ProjectForm(instance=project)
    return render(request, 'tasks/project_form.html', {
        'form': form,
        'project': project,
        'action': 'Edit',
        'title': f'Edit: {project.name}',
    })


@login_required
def project_delete(request, pk):
    """Delete a project (and all its tasks via CASCADE)."""
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    if request.method == 'POST':
        name = project.name
        project.delete()
        cache.delete(f'dashboard_stats_{request.user.id}')
        messages.success(request, f'Project "{name}" deleted.')
        return redirect('dashboard')
    return render(request, 'tasks/confirm_delete.html', {
        'object_type': 'Project',
        'object_name': project.name,
        'extra_warning': f'All {project.task_count()} task(s) inside this project will also be deleted.',
        'cancel_url': reverse('project_detail', args=[pk]),
    })


# ─────────────────────────────────────────────────────────────
# TASK VIEWS  (Full CRUD: Create, Read, Update, Delete)
# ─────────────────────────────────────────────────────────────

@login_required
def task_create(request, project_pk):
    """
    Create a new task inside a project.

    The form includes a 'labels' field which is a Many-to-Many field.
    This is where the M2M relationship is visibly demonstrated:
    the user picks labels using checkboxes, and Django saves them
    to the task_labels join table.
    """
    project = get_object_or_404(Project, pk=project_pk, owner=request.user)
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.created_by = request.user
            task.save()
            form.save_m2m()  # Save the Many-to-Many labels relationship
            cache.delete(f'dashboard_stats_{request.user.id}')
            messages.success(request, f'Task "{task.title}" created!')
            return redirect('project_detail', pk=project.pk)
    else:
        form = TaskForm()
    return render(request, 'tasks/task_form.html', {
        'form': form,
        'project': project,
        'action': 'Create',
        'title': 'New Task',
    })


@login_required
def task_detail(request, pk):
    """View a single task with all its details."""
    task = get_object_or_404(
        Task, pk=pk, project__owner=request.user
    )
    return render(request, 'tasks/task_detail.html', {'task': task})


@login_required
def task_edit(request, pk):
    """Edit a task — including changing its labels (M2M demonstrated here)."""
    task = get_object_or_404(Task, pk=pk, project__owner=request.user)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()  # save() handles M2M automatically when instance is provided
            cache.delete(f'dashboard_stats_{request.user.id}')
            messages.success(request, f'Task "{task.title}" updated!')
            return redirect('task_detail', pk=task.pk)
    else:
        form = TaskForm(instance=task)
    return render(request, 'tasks/task_form.html', {
        'form': form,
        'task': task,
        'project': task.project,
        'action': 'Edit',
        'title': f'Edit: {task.title}',
    })


@login_required
def task_delete(request, pk):
    """Delete a task — shows a confirmation page before deleting."""
    task = get_object_or_404(Task, pk=pk, project__owner=request.user)
    project_pk = task.project.pk
    if request.method == 'POST':
        title = task.title
        task.delete()
        cache.delete(f'dashboard_stats_{request.user.id}')
        messages.success(request, f'Task "{title}" deleted.')
        return redirect('project_detail', pk=project_pk)
    return render(request, 'tasks/confirm_delete.html', {
        'object_type': 'Task',
        'object_name': task.title,
        'cancel_url': reverse('task_detail', args=[pk]),
    })


# ─────────────────────────────────────────────────────────────
# LABEL MANAGEMENT
# ─────────────────────────────────────────────────────────────

@login_required
def label_list(request):
    """
    View and create labels.
    Labels demonstrate the Many-to-Many relationship with Tasks.
    """
    if request.method == 'POST':
        form = LabelForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Label created!')
            return redirect('label_list')
    else:
        form = LabelForm()

    labels = Label.objects.prefetch_related('tasks').all()
    return render(request, 'tasks/label_list.html', {
        'labels': labels,
        'form': form,
        'palette': LABEL_PALETTE,
    })


@login_required
@require_POST
def task_update_status(request, pk):
    """
    AJAX endpoint for Kanban drag-and-drop.

    Accepts a POST request with JSON body: {"status": "todo"|"in_progress"|"done"}
    Updates the task status and clears the dashboard cache.
    Returns JSON: {"ok": true} or {"ok": false, "error": "..."}
    """
    task = get_object_or_404(Task, pk=pk, project__owner=request.user)
    valid_statuses = {Task.STATUS_TODO, Task.STATUS_IN_PROGRESS, Task.STATUS_DONE}
    try:
        data = json.loads(request.body)
        new_status = data.get('status', '')
        if new_status not in valid_statuses:
            return JsonResponse({'ok': False, 'error': 'Invalid status'}, status=400)
        task.status = new_status
        task.save(update_fields=['status'])
        cache.delete(f'dashboard_stats_{request.user.id}')
        return JsonResponse({'ok': True})
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'ok': False, 'error': 'Bad request'}, status=400)


@login_required
def label_delete(request, pk):
    """Delete a label."""
    label = get_object_or_404(Label, pk=pk)
    if request.method == 'POST':
        label.delete()
        messages.success(request, 'Label deleted.')
    return redirect('label_list')


# ─────────────────────────────────────────────────────────────
# AUTHENTICATION
# ─────────────────────────────────────────────────────────────

def register(request):
    """User registration — auto-login after successful registration."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to TaskFlow, {user.username}!')
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})


# ─────────────────────────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────────────────────────

def health_check(request):
    """
    Health check endpoint at /health/

    Returns JSON showing whether the database and Redis cache are working.
    Used by monitoring tools to verify the application is healthy.

    Returns 200 if everything is OK, 503 if something is broken.
    """
    health = {
        'status': 'healthy',
        'database': 'unknown',
        'cache': 'unknown',
        'timestamp': time.time(),
        'version': '2.0.0',
    }

    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        health['database'] = 'connected'
    except Exception as e:
        health['status'] = 'unhealthy'
        health['database'] = f'error: {str(e)}'

    try:
        cache.set('health_ping', 'pong', timeout=10)
        val = cache.get('health_ping')
        health['cache'] = 'connected' if val == 'pong' else 'read/write error'
        if val != 'pong':
            health['status'] = 'unhealthy'
    except Exception as e:
        health['status'] = 'unhealthy'
        health['cache'] = f'error: {str(e)}'

    status_code = 200 if health['status'] == 'healthy' else 503
    return JsonResponse(health, status=status_code)


# ─────────────────────────────────────────────────────────────
# REST API
# ─────────────────────────────────────────────────────────────

class TaskListAPIView(generics.ListAPIView):
    """
    REST API endpoint at /api/tasks/

    Returns a JSON list of the current user's tasks.
    Requires authentication via session.
    Supports search: /api/tasks/?search=docker
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'project__name']
    ordering_fields = ['created_at', 'priority', 'status']

    def get_queryset(self):
        return Task.objects.filter(
            project__owner=self.request.user
        ).select_related('project', 'created_by').prefetch_related('labels')
