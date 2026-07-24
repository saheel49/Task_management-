import sys

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Reset a user's password by email address. Useful for admin password resets when email delivery fails."

    def add_arguments(self, parser):
        parser.add_argument("email", type=str, help="User email address")
        parser.add_argument("new_password", type=str, help="New password to set")

    def handle(self, *args, **options):
        email = options["email"]
        new_password = options["new_password"]

        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Successfully reset password for {email}"))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User with email {email} does not exist."))
            sys.exit(1)
