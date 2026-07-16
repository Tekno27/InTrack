from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Roles(models.TextChoices):
        INTERN = "INTERN", "Intern"
        SUPERVISOR = "SUPERVISOR", "Supervisor"

    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.INTERN,
    )

    @property
    def is_supervisor(self):
        return self.role == self.Roles.SUPERVISOR

    @property
    def is_intern(self):
        return self.role == self.Roles.INTERN

    def __str__(self):
        return self.get_full_name() or self.username


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    profile_picture = models.ImageField(
        upload_to="profiles/",
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.user} profile"


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Task(models.Model):
    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"

    intern = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tasks",
        limit_choices_to={"role": User.Roles.INTERN},
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration = models.DurationField(editable=False, default=timedelta)
    attachment = models.FileField(
        upload_to="task_files/",
        blank=True,
        null=True,
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-start_time"]

    def save(self, *args, **kwargs):
        self.duration = self.calculate_duration()
        super().save(*args, **kwargs)

    def calculate_duration(self):
        start = datetime.combine(self.date, self.start_time)
        end = datetime.combine(self.date, self.end_time)
        if end < start:
            # Shift that runs past midnight
            end += timedelta(days=1)
        return end - start

    @property
    def duration_hours(self):
        return round(self.duration.total_seconds() / 3600, 2)

    @property
    def duration_display(self):
        total_minutes = int(self.duration.total_seconds() // 60)
        hours, minutes = divmod(total_minutes, 60)
        if hours and minutes:
            return f"{hours}h {minutes}m"
        if hours:
            return f"{hours}h"
        return f"{minutes}m"

    def __str__(self):
        return f"{self.title} ({self.date})"


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    title = models.CharField(max_length=150)
    message = models.TextField(blank=True)
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
