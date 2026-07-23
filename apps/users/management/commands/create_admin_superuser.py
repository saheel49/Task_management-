import os

from allauth.account.models import EmailAddress
from django.core.management.base import BaseCommand

from apps.users.models import CustomUser


def ensure_user(email, password, first_name="", last_name="", is_staff=False, is_superuser=False):
    user, created = CustomUser.objects.get_or_create(
        email=email,
        defaults={
            "username": email,
            "first_name": first_name,
            "last_name": last_name,
            "is_staff": is_staff,
            "is_superuser": is_superuser,
            "user_type": "manager" if is_superuser else "employee",
            "is_active": True,
        },
    )

    if created:
        user.set_password(password)
        user.save()
    else:
        changed = False
        if user.username != email:
            user.username = email
            changed = True
        if user.first_name != first_name:
            user.first_name = first_name
            changed = True
        if user.last_name != last_name:
            user.last_name = last_name
            changed = True
        if user.is_staff != is_staff:
            user.is_staff = is_staff
            changed = True
        if user.is_superuser != is_superuser:
            user.is_superuser = is_superuser
            changed = True
        if user.user_type != ("manager" if is_superuser else "employee"):
            user.user_type = "manager" if is_superuser else "employee"
            changed = True
        if not user.is_active:
            user.is_active = True
            changed = True
        if changed:
            user.save()

    EmailAddress.objects.get_or_create(
        user=user,
        email=email,
        defaults={
            "verified": True,
            "primary": True,
        },
    )

    return user, created


class Command(BaseCommand):
    help = "Create or update default users from environment variables for production deployment."

    def handle(self, *args, **options):
        results = []

        admin_email = os.environ.get("ADMIN_EMAIL", "admin@example.com")
        admin_password = os.environ.get("ADMIN_PASSWORD", "admin")
        admin_first_name = os.environ.get("ADMIN_FIRST_NAME", "Admin")
        admin_last_name = os.environ.get("ADMIN_LAST_NAME", "User")

        user, created = ensure_user(
            email=admin_email,
            password=admin_password,
            first_name=admin_first_name,
            last_name=admin_last_name,
            is_staff=True,
            is_superuser=True,
        )
        results.append((admin_email, created))

        employee_email = os.environ.get("EMPLOYEE_EMAIL")
        employee_password = os.environ.get("EMPLOYEE_PASSWORD")
        employee_first_name = os.environ.get("EMPLOYEE_FIRST_NAME", "Employee")
        employee_last_name = os.environ.get("EMPLOYEE_LAST_NAME", "User")

        if employee_email and employee_password:
            user, created = ensure_user(
                email=employee_email,
                password=employee_password,
                first_name=employee_first_name,
                last_name=employee_last_name,
                is_staff=False,
                is_superuser=False,
            )
            results.append((employee_email, created))

        for email, created in results:
            status = "created" if created else "updated/verified"
            self.stdout.write(self.style.SUCCESS(f"User '{email}' {status}."))

        self.stdout.write(self.style.SUCCESS("Default users are ready for production login."))
