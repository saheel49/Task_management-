from django.core.management.base import BaseCommand

from apps.users.models import CustomUser


class Command(BaseCommand):
    help = "Create or update a superuser from environment variables for production deployment."

    def add_arguments(self, parser):
        parser.add_argument("--email", type=str, help="Admin email (defaults to ADMIN_EMAIL env var)")
        parser.add_argument("--password", type=str, help="Admin password (defaults to ADMIN_PASSWORD env var)")
        parser.add_argument("--first-name", type=str, default="Admin", help="Admin first name")
        parser.add_argument("--last-name", type=str, default="User", help="Admin last name")

    def handle(self, *args, **options):
        import os

        email = options["email"] or os.environ.get("ADMIN_EMAIL", "admin@example.com")
        password = options["password"] or os.environ.get("ADMIN_PASSWORD", "admin")
        first_name = options["first_name"] or os.environ.get("ADMIN_FIRST_NAME", "Admin")
        last_name = options["last_name"] or os.environ.get("ADMIN_LAST_NAME", "User")

        user, created = CustomUser.objects.get_or_create(
            email=email,
            defaults={
                "username": email,
                "first_name": first_name,
                "last_name": last_name,
                "is_staff": True,
                "is_superuser": True,
            },
        )

        if not created:
            self.stdout.write(f"Superuser '{email}' already exists. Updating password.")
            user.is_staff = True
            user.is_superuser = True
            user.first_name = first_name
            user.last_name = last_name
            user.save()
        else:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Created superuser '{email}'"))

        self.stdout.write(self.style.SUCCESS("Superuser is ready for production login."))
