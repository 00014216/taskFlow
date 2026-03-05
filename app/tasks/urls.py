"""
URL patterns for TaskFlow.

Maps URLs to view functions.
"""
from django.urls import path
from . import views

urlpatterns = [
    # ── Public ───────────────────────────────────────────────
    path('', views.landing, name='landing'),
    path('health/', views.health_check, name='health_check'),

    # ── Dashboard ─────────────────────────────────────────────
    path('dashboard/', views.dashboard, name='dashboard'),

    # ── Projects (CRUD) ───────────────────────────────────────
    path('projects/', views.project_list, name='project_list'),
    path('projects/create/', views.project_create, name='project_create'),
    path('projects/<int:pk>/', views.project_detail, name='project_detail'),
    path('projects/<int:pk>/edit/', views.project_edit, name='project_edit'),
    path('projects/<int:pk>/delete/', views.project_delete, name='project_delete'),

    # ── Tasks (Full CRUD) ─────────────────────────────────────
    path('projects/<int:project_pk>/tasks/create/', views.task_create, name='task_create'),
    path('tasks/<int:pk>/', views.task_detail, name='task_detail'),
    path('tasks/<int:pk>/edit/', views.task_edit, name='task_edit'),
    path('tasks/<int:pk>/delete/', views.task_delete, name='task_delete'),
    path('tasks/<int:pk>/status/', views.task_update_status, name='task_update_status'),

    # ── Labels (Many-to-Many management) ─────────────────────
    path('labels/', views.label_list, name='label_list'),
    path('labels/<int:pk>/delete/', views.label_delete, name='label_delete'),

    # ── Auth ──────────────────────────────────────────────────
    path('register/', views.register, name='register'),

    # ── REST API ──────────────────────────────────────────────
    path('api/tasks/', views.TaskListAPIView.as_view(), name='api_tasks'),
]
