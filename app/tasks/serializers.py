"""
Serializers for the TaskFlow REST API.

Converts Django model objects to JSON so they can be consumed
by other applications or tested via browser/curl.

Visit /api/tasks/ to see the output.
"""
from rest_framework import serializers
from .models import Task, Project, Label


class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = ['id', 'name', 'color']


class ProjectSerializer(serializers.ModelSerializer):
    owner = serializers.CharField(source='owner.username', read_only=True)
    task_count = serializers.IntegerField(source='task_count', read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'status', 'owner', 'task_count', 'created_at']


class TaskSerializer(serializers.ModelSerializer):
    """
    Converts a Task to JSON.
    Includes nested label objects to demonstrate M2M in the API output.
    """
    project = serializers.CharField(source='project.name', read_only=True)
    created_by = serializers.CharField(source='created_by.username', read_only=True)
    # Nested serializer shows all labels for this task — M2M visible in JSON output
    labels = LabelSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'project', 'created_by',
            'status', 'status_display', 'priority', 'priority_display',
            'labels', 'due_date', 'created_at', 'updated_at',
        ]
