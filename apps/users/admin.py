from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "email",
        "username",
        "first_name",
        "last_name",
        "user_type",
        "is_staff",
        "is_superuser",
        "is_active",
        "date_joined",
    )

    list_filter = (
        "user_type",
        "is_staff",
        "is_superuser",
        "is_active",
        "groups",
        "date_joined",
    )

    search_fields = (
        "email",
        "username",
        "first_name",
        "last_name",
        "phone",
    )

    ordering = ("-date_joined",)

    readonly_fields = ("date_joined",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
        (
            "Profile Information",
            {
                "fields": (
                    "avatar",
                    "user_type",
                    "phone",
                    "bio",
                )
            },
        ),
    )

    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),
        (
            "Profile Information",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "user_type",
                    "phone",
                    "bio",
                    "avatar",
                )
            },
        ),
    )
