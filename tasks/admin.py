from django.contrib import admin

from apps.notifications.admin import TaskUpdateInline

from .models import Project, Task


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "manager",
        "status",
        "created_at",
    )
    list_filter = (
        "status",
        "created_at",
    )
    search_fields = (
        "name",
        "description",
        "manager__email",
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "project",
        "assigned_to",
        "priority",
        "status",
        "due_date",
        "created_at",
    )
    list_filter = (
        "priority",
        "status",
        "due_date",
        "created_at",
    )
    search_fields = (
        "title",
        "description",
        "project__name",
        "assigned_to__email",
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)
    inlines = [TaskUpdateInline]
