from django.core.management.base import BaseCommand, CommandError

from apps.users.models import CustomUser


class Command(BaseCommand):
    help = "Promotes the given user to a superuser and provides admin access."

    def add_arguments(self, parser):
        parser.add_argument("identifier", type=str)

    def handle(self, identifier, **options):
        try:
            user = CustomUser.objects.get(**{CustomUser.USERNAME_FIELD: identifier})
        except CustomUser.DoesNotExist:
            raise CommandError(f"No user with username/email {identifier} found!") from None
        user.is_superuser = True
        user.is_staff = True
        user.save()
        print(f"{identifier} successfully promoted to superuser and can now access the admin site")
