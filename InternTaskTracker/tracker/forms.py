from django import forms
from django.contrib.auth.forms import SetPasswordForm

from .models import Category, Profile, Task, User
from .permissions import assignable_interns_for, categories_for


class InviteUserForm(forms.ModelForm):
    """Used by department heads to create supervisors or interns."""

    ROLE_CHOICES = (
        (User.Roles.SUPERVISOR, "Supervisor"),
        (User.Roles.INTERN, "Intern"),
    )

    role = forms.ChoiceField(choices=ROLE_CHOICES)
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    username = forms.CharField(max_length=150)
    supervisor = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        help_text="Required when inviting an intern.",
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "role", "supervisor")

    def __init__(self, *args, head=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.head = head
        if head and head.department_id:
            self.fields["supervisor"].queryset = User.objects.filter(
                role=User.Roles.SUPERVISOR,
                department=head.department,
                is_active=True,
            )

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean(self):
        cleaned = super().clean()
        role = cleaned.get("role")
        supervisor = cleaned.get("supervisor")
        if role == User.Roles.INTERN and not supervisor:
            self.add_error("supervisor", "Assign a supervisor when inviting an intern.")
        if role == User.Roles.SUPERVISOR:
            cleaned["supervisor"] = None
        if (
            supervisor
            and self.head
            and supervisor.department_id != self.head.department_id
        ):
            self.add_error("supervisor", "Supervisor must belong to your department.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.department = self.head.department if self.head else None
        user.must_set_password = True
        user.email_verified = False
        user.set_unusable_password()
        if commit:
            user.save()
        return user


class AssignInternForm(forms.Form):
    intern = forms.ModelChoiceField(queryset=User.objects.none())
    supervisor = forms.ModelChoiceField(queryset=User.objects.none())

    def __init__(self, *args, head=None, **kwargs):
        super().__init__(*args, **kwargs)
        if head and head.department_id:
            dept = head.department
            self.fields["intern"].queryset = User.objects.filter(
                role=User.Roles.INTERN, department=dept)
            self.fields["supervisor"].queryset = User.objects.filter(
                role=User.Roles.SUPERVISOR, department=dept, is_active=True)


class AcceptInviteForm(SetPasswordForm):
    """Verify email by setting a password via invite token."""

    def save(self, commit=True):
        user = super().save(commit=False)
        user.must_set_password = False
        user.email_verified = True
        user.is_active = True
        if commit:
            user.save()
        return user


class InternTaskForm(forms.ModelForm):
    """Self-logged work entry by an intern."""

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

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields["category"].queryset = categories_for(user)
        self.fields["status"].choices = [
            (s, label) for s, label in Task.Status.choices
            if s in {
                Task.Status.PENDING,
                Task.Status.IN_PROGRESS,
                Task.Status.CHANGES_REQUESTED,
            }
        ]

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get("start_time"), cleaned.get("end_time")
        if not start or not end:
            raise forms.ValidationError(
                "Start and end times are required for logged work.")
        return cleaned

    def clean_attachment(self):
        attachment = self.cleaned_data.get("attachment")
        if attachment and attachment.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Attachment must be 5 MB or smaller.")
        return attachment


class AssignTaskForm(forms.ModelForm):
    """Supervisor/head assigns a task to an intern."""

    class Meta:
        model = Task
        fields = ("intern", "title", "description", "category", "priority",
                  "status", "date", "attachment", "notes")
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user:
            self.fields["intern"].queryset = assignable_interns_for(user)
            self.fields["category"].queryset = categories_for(user)
        self.fields["status"].choices = [
            (s, label) for s, label in Task.Status.choices
            if s in {Task.Status.PENDING, Task.Status.IN_PROGRESS}
        ]


class TaskUpdateForm(forms.ModelForm):
    """Intern updates progress / logs time on a task."""

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

    def __init__(self, *args, user=None, assigned=False, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields["category"].queryset = categories_for(user)
        if user and user.is_intern:
            self.fields["status"].choices = [
                (s, label) for s, label in Task.Status.choices
                if s in {
                    Task.Status.PENDING,
                    Task.Status.IN_PROGRESS,
                    Task.Status.CHANGES_REQUESTED,
                }
            ]
        if assigned and user and user.is_intern:
            for field in ("title", "description", "category", "priority"):
                self.fields[field].disabled = True


class TaskReviewForm(forms.Form):
    ACTION_CHOICES = (
        ("APPROVE", "Approve"),
        ("REQUEST_CHANGES", "Request changes"),
    )
    action = forms.ChoiceField(choices=ACTION_CHOICES, widget=forms.RadioSelect)
    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "rows": 3,
            "placeholder": "Feedback for the intern (required when requesting changes)...",
            "class": "form-control",
        }),
    )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("action") == "REQUEST_CHANGES" and not (
                cleaned.get("comment") or "").strip():
            self.add_error("comment", "Please explain what needs to be changed.")
        return cleaned


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("phone", "profile_picture")
        widgets = {
            "profile_picture": forms.ClearableFileInput(attrs={"class": "form-control", "accept": "image/*"}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        uploaded = self.cleaned_data.get("profile_picture")
        if "profile_picture" in self.changed_data and uploaded:
            from io import BytesIO

            from django.core.files.base import ContentFile
            from PIL import Image

            uploaded.seek(0)
            img = Image.open(uploaded)
            img = img.convert("RGB")
            width, height = img.size
            side = min(width, height)
            left = (width - side) // 2
            top = (height - side) // 2
            img = img.crop((left, top, left + side, top + side))
            img = img.resize((400, 400), Image.Resampling.LANCZOS)
            buffer = BytesIO()
            img.save(buffer, format="JPEG", quality=90)
            name = getattr(uploaded, "name", "avatar.jpg")
            stem = name.rsplit(".", 1)[0] if "." in name else name
            stem = stem.rsplit("/", 1)[-1]
            instance.profile_picture.save(
                f"{stem}.jpg",
                ContentFile(buffer.getvalue()),
                save=False,
            )
        if commit:
            instance.save()
        return instance


class MessageForm(forms.Form):
    body = forms.CharField(
        widget=forms.Textarea(attrs={
            "rows": 2,
            "placeholder": "Type a message...",
            "class": "form-control",
        }),
        max_length=2000,
        label="",
    )


class StartChatForm(forms.Form):
    recipient = forms.ModelChoiceField(queryset=User.objects.none(), label="Chat with")

    def __init__(self, *args, queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        if queryset is not None:
            self.fields["recipient"].queryset = queryset


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ("name", "description")
        widgets = {"description": forms.Textarea(attrs={"rows": 2})}
