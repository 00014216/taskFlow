"""
Forms for TaskFlow.

Forms handle user input and validate it before saving to the database.
We use ModelForm which auto-generates fields from our model definitions.
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Project, Task, Label


class ProjectForm(forms.ModelForm):
    """Form for creating or editing a project."""
    class Meta:
        model = Project
        fields = ['name', 'description', 'status']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Cloud Deployment Project',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'What is this project about?',
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class TaskForm(forms.ModelForm):
    """
    Form for creating or editing a task.

    The 'labels' field is a Many-to-Many field — it renders as a
    multi-select box where users pick one or more labels.
    This visibly demonstrates the M2M relationship.
    """
    class Meta:
        model = Task
        fields = ['title', 'description', 'status', 'priority', 'labels', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Set up Docker container',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe the task in detail...',
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            # CheckboxSelectMultiple shows all labels as checkboxes — clear M2M UI
            'labels': forms.CheckboxSelectMultiple(attrs={'class': 'label-checkboxes'}),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
        }


class LabelForm(forms.ModelForm):
    """Form for creating a new label."""
    class Meta:
        model = Label
        fields = ['name', 'color']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Bug',
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control form-control-color',
                'type': 'color',
            }),
        }


class RegisterForm(UserCreationForm):
    """Registration form — extends Django's built-in form to add email."""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your@email.com',
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].widget.attrs['class'] = 'form-control'
