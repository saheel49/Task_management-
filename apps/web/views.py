from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

from tasks.models import Project, Task

User = get_user_model()


def home(request):
    context = {
        "page_title": _("Task Manager"),
    }

    if request.user.is_authenticated:
        user = request.user
        today = _("today")  # placeholder for date context if needed later
        total_tasks = Task.objects.filter(assigned_to=user).count()
        completed_tasks = Task.objects.filter(assigned_to=user, status="completed").count()
        in_progress_tasks = Task.objects.filter(assigned_to=user, status="progress").count()
        pending_tasks = Task.objects.filter(assigned_to=user, status="todo").count()
        recent_tasks = Task.objects.filter(assigned_to=user).order_by("-created_at")[:5]

        context.update({
            "active_tab": "dashboard",
            "page_title": _("Dashboard"),
            "breadcrumbs": [
                {"label": "Dashboard"},
            ],
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "pending_tasks": pending_tasks,
            "recent_tasks": recent_tasks,
            "today": today,
        })
        return render(
            request,
            "web/app_home.html",
            context=context,
        )

    context.update({
        "total_users": User.objects.count(),
        "total_tasks": Task.objects.count(),
        "total_projects": Project.objects.count(),
        "recent_users": User.objects.filter(is_active=True).order_by("-date_joined")[:6],
    })
    return render(request, "web/landing_page.html", context=context)


@user_passes_test(lambda u: u.is_superuser)
def simulate_error(request):
    raise Exception("This is a simulated error.")


def page_not_found(request, exception=None):
    return render(request, "404.html", status=404)


def permission_denied(request, exception=None):
    return render(request, "403.html", status=403)


def server_error(request):
    return render(request, "500.html", status=500)
