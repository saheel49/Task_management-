from django.contrib import admin

from .models import Notification, TaskUpdate


class TaskUpdateInline(admin.TabularInline):
    model = TaskUpdate
    extra = 0
    readonly_fields = ("created_at",)
    fields = ("user", "old_status", "new_status", "completion_note", "attachment", "created_at")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "actor",
        "verb",
        "related_task",
        "read",
        "created_at",
    )
    list_filter = ("read", "created_at", "verb")
    search_fields = (
        "user__email",
        "actor__email",
        "verb",
        "description",
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)


@admin.register(TaskUpdate)
class TaskUpdateAdmin(admin.ModelAdmin):
    list_display = (
        "task",
        "user",
        "old_status",
        "new_status",
        "created_at",
    )
    list_filter = ("new_status", "created_at")
    search_fields = (
        "task__title",
        "user__email",
        "completion_note",
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)
