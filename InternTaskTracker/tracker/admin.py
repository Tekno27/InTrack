from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    Category,
    Conversation,
    Department,
    Invitation,
    Message,
    Notification,
    Profile,
    Task,
    User,
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "created_at")
    search_fields = ("name",)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "username", "email", "first_name", "last_name",
        "role", "department", "supervisor", "email_verified", "is_active",
    )
    list_filter = ("role", "department", "email_verified", "is_active")
    search_fields = ("username", "email", "first_name", "last_name")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Organization", {
            "fields": ("role", "department", "supervisor",
                       "must_set_password", "email_verified"),
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Organization", {
            "fields": ("role", "department", "supervisor", "email"),
        }),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone")
    search_fields = ("user__username", "user__first_name", "user__last_name")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "department", "description")
    list_filter = ("department",)
    search_fields = ("name",)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "title", "intern", "assigned_by", "category", "date",
        "duration_display", "priority", "status",
    )
    list_filter = ("status", "priority", "category", "date")
    search_fields = ("title", "description", "intern__username",
                     "intern__first_name", "intern__last_name")
    date_hierarchy = "date"


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ("user", "invited_by", "created_at", "expires_at", "accepted_at")
    list_filter = ("accepted_at",)
    search_fields = ("user__email", "user__username")


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ("sender", "body", "is_read", "created_at")


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "updated_at")
    filter_horizontal = ("participants",)
    inlines = [MessageInline]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "is_read", "created_at")
    list_filter = ("is_read",)
