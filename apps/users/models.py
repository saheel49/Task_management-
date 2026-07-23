import hashlib
import uuid
from functools import cached_property

from allauth.account.models import EmailAddress
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

from apps.users.helpers import validate_profile_picture


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        extra_fields.setdefault("username", email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("username", email)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


def _get_avatar_filename(instance, filename):
    """Use random filename to prevent overwriting existing files & fix caching issues."""
    extension = filename.split(".")[-1]
    return f"profile-pictures/{uuid.uuid4()}.{extension}"


class CustomUser(AbstractUser):
    """
    Custom user model for the TaskFlow application.
    """

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    email = models.EmailField(
        max_length=254,
        verbose_name="email address",
        unique=True,
    )

    objects = CustomUserManager()

    USER_TYPES = (
        ("manager", "Manager"),
        ("employee", "Employee"),
    )

    avatar = models.FileField(
        upload_to=_get_avatar_filename,
        blank=True,
        validators=[validate_profile_picture],
    )

    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPES,
        default="employee",
        blank=True,
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
    )

    bio = models.TextField(
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.get_full_name()} <{self.email or self.username}>"

    def get_display_name(self) -> str:
        if self.get_full_name().strip():
            return self.get_full_name()
        return self.email or self.username

    @property
    def avatar_url(self) -> str:
        if self.avatar:
            return self.avatar.url
        return "/static/images/default-avatar.png"

    @property
    def gravatar_id(self) -> str:
        return hashlib.md5(self.email.lower().strip().encode("utf-8")).hexdigest()

    @cached_property
    def has_verified_email(self):
        return EmailAddress.objects.filter(
            user=self,
            verified=True,
        ).exists()
