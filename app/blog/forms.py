"""
Forms for CloudBlog.

A Django form handles user input (text boxes, dropdowns, etc.)
and validates that the data is correct before saving to the database.
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Post, Comment


class PostForm(forms.ModelForm):
    """
    Form for creating or editing a blog post.
    ModelForm automatically creates fields from the Post model.
    """
    class Meta:
        model = Post
        fields = ['title', 'category', 'body', 'published']
        widgets = {
            # Use Bootstrap-styled text inputs
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter post title...'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'body': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 12,
                'placeholder': 'Write your article here...'
            }),
            'published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CommentForm(forms.ModelForm):
    """
    Simple form for readers to leave a comment.
    """
    class Meta:
        model = Comment
        fields = ['body']
        widgets = {
            'body': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Write your comment here...'
            }),
        }
        labels = {
            'body': 'Your comment',
        }


class RegisterForm(UserCreationForm):
    """
    Registration form for new users.
    Extends Django's built-in UserCreationForm to add an email field.
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your@email.com'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap styling to all fields
        for field_name in self.fields:
            self.fields[field_name].widget.attrs['class'] = 'form-control'
