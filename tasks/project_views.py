from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.utils.permissions import is_manager_or_superuser

from .models import Project, Task


@login_required
def project_list(request):
    projects = Project.objects.all()

    search_query = request.GET.get("search", "").strip()
    if search_query:
        projects = projects.filter(Q(name__icontains=search_query) | Q(description__icontains=search_query)).distinct()

    projects = projects.order_by("-created_at")

    context = {
        "projects": projects,
        "search_query": search_query,
        "page_title": "Projects",
        "breadcrumbs": [
            {"url": reverse("dashboard:dashboard"), "label": "Dashboard"},
            {"label": "Projects"},
        ],
    }

    return render(
        request,
        "tasks/project_list.html",
        context,
    )


@login_required
def project_detail(request, id):
    project = get_object_or_404(Project, pk=id)

    tasks = Task.objects.filter(project=project)
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(status="completed").count()
    completion_percentage = round((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0

    context = {
        "project": project,
        "tasks": tasks,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "completion_percentage": completion_percentage,
        "page_title": project.name,
        "breadcrumbs": [
            {"url": reverse("dashboard:dashboard"), "label": "Dashboard"},
            {"url": reverse("tasks:project_list"), "label": "Projects"},
            {"label": project.name},
        ],
    }

    return render(
        request,
        "tasks/project_detail.html",
        context,
    )


@login_required
@user_passes_test(is_manager_or_superuser)
def project_create(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        status = request.POST.get("status", "active")

        if not name:
            messages.error(request, "Project name is required.")
        else:
            Project.objects.create(
                name=name,
                description=description,
                status=status,
                manager=request.user,
            )
            messages.success(request, "Project created successfully!")
            return redirect("tasks:project_list")

    return render(
        request,
        "tasks/project_form.html",
        {
            "page_title": "Create Project",
            "status_choices": Project.STATUS_CHOICES,
            "breadcrumbs": [
                {"url": reverse("dashboard:dashboard"), "label": "Dashboard"},
                {"url": reverse("tasks:project_list"), "label": "Projects"},
                {"label": "Create Project"},
            ],
        },
    )


@login_required
@user_passes_test(is_manager_or_superuser)
def project_update(request, id):
    project = get_object_or_404(Project, pk=id)

    if request.method == "POST":
        project.name = request.POST.get("name", "").strip()
        project.description = request.POST.get("description", "").strip()
        project.status = request.POST.get("status", "active")

        if not project.name:
            messages.error(request, "Project name is required.")
        else:
            project.save()
            messages.success(request, "Project updated successfully!")
            return redirect("tasks:project_detail", id=project.id)

    return render(
        request,
        "tasks/project_form.html",
        {
            "project": project,
            "page_title": "Update Project",
            "status_choices": Project.STATUS_CHOICES,
            "breadcrumbs": [
                {"url": reverse("dashboard:dashboard"), "label": "Dashboard"},
                {"url": reverse("tasks:project_list"), "label": "Projects"},
                {"url": reverse("tasks:project_detail", kwargs={"id": project.id}), "label": project.name},
                {"label": "Edit Project"},
            ],
        },
    )


@login_required
@user_passes_test(is_manager_or_superuser)
def project_delete(request, id):
    project = get_object_or_404(Project, pk=id)

    if request.method == "POST":
        project.delete()
        messages.success(request, "Project deleted successfully!")
        return redirect("tasks:project_list")

    return render(request, "tasks/project_confirm_delete.html", {
        "project": project,
        "breadcrumbs": [
            {"url": reverse("dashboard:dashboard"), "label": "Dashboard"},
            {"url": reverse("tasks:project_list"), "label": "Projects"},
            {"url": reverse("tasks:project_detail", kwargs={"id": project.id}), "label": project.name},
            {"label": "Delete"},
        ],
    })
