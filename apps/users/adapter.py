from allauth.account import app_settings
from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.utils import user_email, user_field
from django.utils.translation import gettext_lazy as _


class EmailAsUsernameAdapter(DefaultAccountAdapter):
    """
    Adapter that keeps the username field in sync with the email address
    and prevents allauth from overwriting the email with a generated
    username when USERNAME_FIELD is set to email.
    """

    def __init__(self, request=None):
        super().__init__(request)
        self.error_messages["email_taken"] = _("There was an issue creating the account. Please contact support.")

    def populate_username(self, request, user):
        if app_settings.USER_MODEL_USERNAME_FIELD == "email":
            user.username = user_email(user)
        else:
            user_field(user, app_settings.USER_MODEL_USERNAME_FIELD, user_email(user))


class NoNewUsersAccountAdapter(DefaultAccountAdapter):
    """
    Adapter that can be used to disable public sign-ups for your app.
    """

    def is_open_for_signup(self, request):
        # see https://stackoverflow.com/a/29799664/8207
        return False
