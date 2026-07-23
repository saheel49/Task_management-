import logging
from datetime import date

from allauth.account.models import EmailAddress
from allauth.account.views import PasswordResetView
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from tasks.models import Task

from .forms import CustomUserChangeForm, UploadAvatarForm
from .helpers import require_email_confirmation, user_has_confirmed_email_address
from .models import CustomUser

logger = logging.getLogger(__name__)


class CustomPasswordResetView(PasswordResetView):
    """
    Override allauth's PasswordResetView to catch email delivery exceptions
    and show a friendly error message instead of crashing with a 500.
    """

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except Exception as e:
            logger.error("Password reset email failed: %s", str(e), exc_info=True)
            messages.error(
                self.request, _("Unable to send password reset email. Please contact support if the problem persists.")
            )
            return render(self.request, self.get_template_names(), self.get_context_data(form=form))


@login_required
def profile(request):
    if request.method == "POST":
        form = CustomUserChangeForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            user_before_update = CustomUser.objects.get(pk=user.pk)
            email_changed = user_before_update.email != user.email
            need_to_confirm_email = (
                email_changed
                and require_email_confirmation()
                and not user_has_confirmed_email_address(user, user.email)
            )
            if need_to_confirm_email:
                new_email = user.email
                EmailAddress.objects.add_email(request, user, new_email, confirm=True)
                user.email = user_before_update.email
                form = CustomUserChangeForm(request.POST, request.FILES, instance=user)
            user.save()
            user.refresh_from_db()

            if email_changed and not need_to_confirm_email:
                email_address = EmailAddress.objects.filter(user=user, email__iexact=user.email).first()
                if email_address:
                    email_address.set_as_primary()
            messages.success(request, _("Profile successfully saved."))
    else:
        form = CustomUserChangeForm(instance=request.user)

    total_assigned = Task.objects.filter(assigned_to=request.user).count()
    completed_tasks = Task.objects.filter(assigned_to=request.user, status="completed").count()
    active_tasks = Task.objects.filter(assigned_to=request.user, status__in=["todo", "progress"]).count()
    recent_tasks = Task.objects.filter(assigned_to=request.user).order_by("-created_at")[:5]

    return render(
        request,
        "account/profile.html",
        {
            "form": form,
            "active_tab": "profile",
            "page_title": _("Profile"),
            "total_assigned": total_assigned,
            "completed_tasks": completed_tasks,
            "active_tasks": active_tasks,
            "recent_tasks": recent_tasks,
            "breadcrumbs": [
                {"url": reverse("dashboard:dashboard"), "label": "Dashboard"},
                {"label": "Profile"},
            ],
        },
    )


@login_required
@require_POST
def upload_profile_image(request):
    user = request.user
    form = UploadAvatarForm(request.POST, request.FILES)
    if form.is_valid():
        user.avatar = request.FILES["avatar"]
        user.save()
        return HttpResponse(_("Success!"))
    else:
        readable_errors = ", ".join(str(error) for key, errors in form.errors.items() for error in errors)
        return JsonResponse(status=400, data={"errors": readable_errors})


@login_required
def user_list(request):
    users = CustomUser.objects.filter(is_active=True).order_by("-date_joined")
    return render(
        request,
        "users/user_list.html",
        {
            "users": users,
            "page_title": _("All Users"),
            "breadcrumbs": [
                {"url": reverse("dashboard:dashboard"), "label": "Dashboard"},
                {"label": "Users"},
            ],
        },
    )


@login_required
def user_detail(request, pk):
    user = get_object_or_404(CustomUser, pk=pk, is_active=True)
    from tasks.models import Task

    user_tasks = Task.objects.filter(assigned_to=user).order_by("-created_at")
    return render(
        request,
        "users/user_detail.html",
        {
            "user": user,
            "user_tasks": user_tasks,
            "today": date.today(),
            "page_title": user.get_display_name,
            "breadcrumbs": [
                {"url": reverse("dashboard:dashboard"), "label": "Dashboard"},
                {"url": reverse("users:user_list"), "label": "Users"},
                {"label": user.get_display_name},
            ],
        },
    )
