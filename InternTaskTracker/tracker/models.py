from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class User(AbstractUser):
    class Roles(models.TextChoices):
        HEAD = "HEAD", "Department Head"
        SUPERVISOR = "SUPERVISOR", "Supervisor"
        INTERN = "INTERN", "Intern"

    role = models.CharField(
        max_length=20, choices=Roles.choices, default=Roles.INTERN,
    )
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="members",
    )
    # Interns are assigned to one supervisor within their department.
    supervisor = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_interns", limit_choices_to={"role": Roles.SUPERVISOR},
    )
    must_set_password = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)

    @property
    def is_head(self):
        return self.role == self.Roles.HEAD

    @property
    def is_supervisor(self):
        return self.role == self.Roles.SUPERVISOR

    @property
    def is_intern(self):
        return self.role == self.Roles.INTERN

    @property
    def is_management(self):
        return self.role in {self.Roles.HEAD, self.Roles.SUPERVISOR}

    def __str__(self):
        return self.get_full_name() or self.username


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile",)
    phone = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField( upload_to="profiles/", blank=True, null=True,)

    def __str__(self):
        return f"{self.user} profile"


class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True, related_name="categories", help_text="Leave empty for company-wide categories.",)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]
        unique_together = ("name", "department")

    def __str__(self):
        if self.department:
            return f"{self.name} ({self.department.name})"
        return self.name


class Task(models.Model):
    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        SUBMITTED = "SUBMITTED", "Submitted"
        CHANGES_REQUESTED = "CHANGES_REQUESTED", "Changes Requested"
        APPROVED = "APPROVED", "Approved"

    # Statuses an intern may set themselves (cannot approve their own work).
    INTERN_EDITABLE_STATUSES = (
        Status.PENDING,
        Status.IN_PROGRESS,
        Status.CHANGES_REQUESTED,
    )

    intern = models.ForeignKey( settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tasks", limit_choices_to={"role": User.Roles.INTERN},)
    assigned_by = models.ForeignKey( settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_tasks", help_text="Set when a supervisor/head assigns the task.",)
    category = models.ForeignKey( Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="tasks",)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM,)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING,)
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    duration = models.DurationField(editable=False, null=True, blank=True)
    attachment = models.FileField(upload_to="task_files/", blank=True, null=True,)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    @property
    def is_assigned(self):
        return self.assigned_by_id is not None

    def save(self, *args, **kwargs):
        self.duration = self.calculate_duration()
        super().save(*args, **kwargs)

    def calculate_duration(self):
        if not self.start_time or not self.end_time:
            return None
        start = datetime.combine(self.date, self.start_time)
        end = datetime.combine(self.date, self.end_time)
        if end < start:
            end += timedelta(days=1)
        return end - start

    @property
    def duration_hours(self):
        if not self.duration:
            return 0
        return round(self.duration.total_seconds() / 3600, 2)

    @property
    def duration_display(self):
        if not self.duration:
            return "—"
        total_minutes = int(self.duration.total_seconds() // 60)
        hours, minutes = divmod(total_minutes, 60)
        if hours and minutes:
            return f"{hours}h {minutes}m"
        if hours:
            return f"{hours}h"
        return f"{minutes}m"

    @property
    def can_submit_for_review(self):
        return self.status in {
            self.Status.PENDING,
            self.Status.IN_PROGRESS,
            self.Status.CHANGES_REQUESTED,
        }

    @property
    def awaiting_review(self):
        return self.status == self.Status.SUBMITTED

    def __str__(self):
        return f"{self.title} ({self.date})"


class TaskReview(models.Model):
    class Action(models.TextChoices):
        APPROVE = "APPROVE", "Approved"
        REQUEST_CHANGES = "REQUEST_CHANGES", "Changes Requested"

    task = models.ForeignKey( Task, on_delete=models.CASCADE, related_name="reviews",)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="task_reviews",)
    action = models.CharField(max_length=20, choices=Action.choices)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_action_display()} — {self.task.title}"


class Invitation(models.Model):
    """Tracks invite emails sent when a head creates a supervisor/intern."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="invitation",)
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="sent_invitations",)
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    @property
    def is_accepted(self):
        return self.accepted_at is not None

    def __str__(self):
        return f"Invite for {self.user.email}"


class Conversation(models.Model):
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="conversations",)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def other_participant(self, user):
        return self.participants.exclude(pk=user.pk).first()

    def last_message(self):
        return self.messages.order_by("-created_at").first()

    @classmethod
    def between(cls, user_a, user_b):
        """Return an existing 1:1 conversation or create one."""
        conversation = (
            cls.objects.filter(participants=user_a)
            .filter(participants=user_b)
            .annotate(n=models.Count("participants"))
            .filter(n=2)
            .first()
        )
        if conversation:
            return conversation, False
        conversation = cls.objects.create()
        conversation.participants.add(user_a, user_b)
        return conversation, True

    def __str__(self):
        names = ", ".join(str(u) for u in self.participants.all())
        return f"Conversation ({names})"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages",)
    sender = models.ForeignKey( settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_messages",)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender}: {self.body[:40]}"


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications",)
    title = models.CharField(max_length=150)
    message = models.TextField(blank=True)
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
