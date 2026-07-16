from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Category, Notification, Profile, Task, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "role", "is_active")
    list_filter = ("role", "is_active")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Role", {"fields": ("role",)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Role", {"fields": ("role",)}),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "department", "phone")
    search_fields = ("user__username", "user__first_name", "user__last_name")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "intern", "category", "date", "start_time", "end_time",
                    "duration_display", "priority", "status")
    list_filter = ("status", "priority", "category", "date")
    search_fields = ("title", "description", "intern__username",
                     "intern__first_name", "intern__last_name")
    date_hierarchy = "date"


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "is_read", "created_at")
    list_filter = ("is_read",)
