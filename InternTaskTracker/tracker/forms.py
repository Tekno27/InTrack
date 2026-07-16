from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Category, Profile, Task, User


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email",
                  "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Roles.INTERN  # self-registration is for interns only
        if commit:
            user.save()
        return user


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ("title", "description", "category", "priority", "status",
                  "date", "start_time", "end_time", "attachment", "notes")
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
            "description": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def clean_attachment(self):
        attachment = self.cleaned_data.get("attachment")
        if attachment and attachment.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Attachment must be 5 MB or smaller.")
        return attachment


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("phone", "department", "profile_picture")


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ("name", "description")
        widgets = {"description": forms.Textarea(attrs={"rows": 2})}
