import logging

import requests
from allauth.account.forms import SignupForm
from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserChangeForm
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from .helpers import validate_profile_picture
from .models import CustomUser


class TurnstileSignupForm(SignupForm):
    """
    Sign up form that includes a Turnstile captcha.
    """

    turnstile_token = forms.CharField(
        widget=forms.HiddenInput(),
        required=False,
    )

    def clean_turnstile_token(self):
        if not settings.TURNSTILE_SECRET:
            logging.info("No Turnstile secret found, not checking captcha.")
            return

        turnstile_token = self.cleaned_data.get("turnstile_token")

        if not turnstile_token:
            raise forms.ValidationError("Missing captcha. Please try again.")

        turnstile_url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

        payload = {
            "secret": settings.TURNSTILE_SECRET,
            "response": turnstile_token,
        }

        try:
            response = requests.post(
                turnstile_url,
                data=payload,
                timeout=10,
            ).json()

            if not response["success"]:
                raise forms.ValidationError("Invalid captcha. Please try again.")

        except requests.Timeout:
            raise forms.ValidationError("Captcha verification timed out. Please try again.") from None

        return turnstile_token


class CustomUserChangeForm(UserChangeForm):
    email = forms.EmailField(
        label=_("Email"),
        required=True,
    )

    avatar = forms.ImageField(
        label=_("Profile Picture"),
        required=False,
        validators=[validate_profile_picture],
    )

    class Meta:
        model = CustomUser

        fields = (
            "email",
            "first_name",
            "last_name",
            "phone",
            "bio",
            "user_type",
            "avatar",
        )

        widgets = {
            "bio": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Tell us about yourself...",
                }
            ),
            "user_type": forms.Select(
                attrs={
                    "class": "select select-bordered w-full",
                }
            ),
        }


class UploadAvatarForm(forms.Form):
    avatar = forms.FileField(validators=[validate_profile_picture])


class TermsSignupForm(TurnstileSignupForm):
    """
    Custom signup form to add a checkbox
    for accepting the terms.
    """

    terms_agreement = forms.BooleanField(required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["password1"].help_text = ""

        link = ('<a class="link" href="{}" target="_blank">{}</a>').format(
            reverse("web:terms"),
            _("Terms and Conditions"),
        )

        self.fields["terms_agreement"].label = mark_safe(_("I agree to the {terms_link}").format(terms_link=link))
