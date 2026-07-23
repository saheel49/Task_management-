from django.contrib.auth.decorators import user_passes_test


def is_manager_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.user_type == "manager")


manager_required = user_passes_test(is_manager_or_superuser)
