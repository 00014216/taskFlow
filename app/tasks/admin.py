"""
Django Admin configuration for TaskFlow.
Visit /admin/ after creating a superuser to manage all data.
"""
from django.contrib import admin
from .models import Label, Project, Task


@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'task_count']
    search_fields = ['name']

    def task_count(self, obj):
        return obj.tasks.count()
    task_count.short_description = 'Tasks using this label'


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'status', 'task_count', 'completion_percent', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'owner__username']
    raw_id_fields = ['owner']

    def task_count(self, obj):
        return obj.task_count()
    task_count.short_description = 'Tasks'

    def completion_percent(self, obj):
        return f'{obj.completion_percent()}%'
    completion_percent.short_description = 'Done'


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'created_by', 'status', 'priority', 'label_list', 'due_date']
    list_filter = ['status', 'priority', 'created_at']
    search_fields = ['title', 'description', 'project__name']
    filter_horizontal = ['labels']   # Nice widget for Many-to-Many in admin
    list_editable = ['status', 'priority']
    raw_id_fields = ['project', 'created_by']

    def label_list(self, obj):
        return ', '.join(lbl.name for lbl in obj.labels.all())
    label_list.short_description = 'Labels'


admin.site.site_header = 'TaskFlow Administration'
admin.site.site_title = 'TaskFlow Admin'
admin.site.index_title = 'Manage Your TaskFlow Application'
