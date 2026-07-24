from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.utils.permissions import is_manager_or_superuser

from .forms import TaskAttachmentForm, TaskForm
from .models import Project, Task, TaskAttachment


@login_required
def task_list(request):
    user = request.user
    tasks = Task.objects.all() if is_manager_or_superuser(user) else Task.objects.filter(assigned_to=user)

    search_query = request.GET.get("search", "").strip()
    status_filter = request.GET.get("status", "").strip()
    priority_filter = request.GET.get("priority", "").strip()
    project_filter = request.GET.get("project", "").strip()
    sort_by = request.GET.get("sort", "-created_at").strip()
    allowed_sorts = {
        "due_date": "due_date",
        "-due_date": "-due_date",
        "created_at": "created_at",
        "-created_at": "-created_at",
        "priority": "priority",
        "-priority": "-priority",
        "status": "status",
        "-status": "-status",
    }
    sort_field = allowed_sorts.get(sort_by, "-created_at")

    if search_query:
        tasks = tasks.filter(
            Q(title__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(project__name__icontains=search_query)
        ).distinct()

    if status_filter:
        tasks = tasks.filter(status=status_filter)

    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)

    if project_filter:
        tasks = tasks.filter(project__id=project_filter)

    tasks = tasks.order_by(sort_field)

    paginator = Paginator(tasks, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "tasks": page_obj,
        "page_obj": page_obj,
        "total_tasks": tasks.count(),
        "completed_tasks": tasks.filter(status="completed").count(),
        "pending_tasks": tasks.filter(status="todo").count(),
        "in_progress_tasks": tasks.filter(status="progress").count(),
        "today": date.today(),
        "search_query": search_query,
        "status_filter": status_filter,
        "priority_filter": priority_filter,
        "project_filter": project_filter,
        "sort_by": sort_by,
        "projects": Project.objects.all(),
        "breadcrumbs": [
            {"url": reverse("dashboard:dashboard"), "label": "Dashboard"},
            {"label": "Tasks"},
        ],
    }

    return render(
        request,
        "tasks/task_list.html",
        context,
    )


@login_required
def create_task(request):
    if not is_manager_or_superuser(request.user):
        messages.error(request, "Only managers can create tasks.")
        return redirect("dashboard:dashboard")

    if request.method == "POST":
        form = TaskForm(request.POST, user=request.user)
        attachment_form = TaskAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            task = form.save(commit=False)
            if not form.cleaned_data.get("assigned_to"):
                task.assigned_to = request.user
            task.save()
            form.save_m2m()

            if attachment_form.is_valid() and request.FILES.get("file"):
                TaskAttachment.objects.create(
                    task=task,
                    file=request.FILES["file"],
                    uploaded_by=request.user,
                )
            messages.success(request, "Task created successfully!")
            return redirect("tasks:task_list")
    else:
        form = TaskForm(user=request.user)
        attachment_form = TaskAttachmentForm()

    return render(
        request,
        "tasks/create_task.html",
        {
            "form": form,
            "attachment_form": attachment_form,
            "breadcrumbs": [
                {"url": reverse("dashboard:dashboard"), "label": "Dashboard"},
                {"url": reverse("tasks:task_list"), "label": "Tasks"},
                {"label": "Create Task"},
            ],
        },
    )


@login_required
def task_detail(request, id):
    if is_manager_or_superuser(request.user):
        task = get_object_or_404(Task, id=id)
    else:
        task = get_object_or_404(Task, id=id, assigned_to=request.user)
    return render(
        request,
        "tasks/task_detail.html",
        {
            "task": task,
            "breadcrumbs": [
                {"url": reverse("dashboard:dashboard"), "label": "Dashboard"},
                {"url": reverse("tasks:task_list"), "label": "Tasks"},
                {"label": task.title},
            ],
        },
    )


@login_required
def update_task(request, id):
    if is_manager_or_superuser(request.user):
        task = get_object_or_404(Task, id=id)
    else:
        task = get_object_or_404(Task, id=id, assigned_to=request.user)

    if request.method == "POST":
        if is_manager_or_superuser(request.user):
            form = TaskForm(request.POST, instance=task, user=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, "Task updated successfully!")
                return redirect("tasks:task_list")
        else:
            form = TaskForm(request.POST, instance=task, user=request.user, status_only=True)
            attachment_form = TaskAttachmentForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                if attachment_form.is_valid() and request.FILES.get("file"):
                    TaskAttachment.objects.create(
                        task=task,
                        file=request.FILES["file"],
                        uploaded_by=request.user,
                    )
                messages.success(request, "Task updated successfully!")
                return redirect("tasks:task_list")
    else:
        form = TaskForm(instance=task, user=request.user, status_only=not is_manager_or_superuser(request.user))
        attachment_form = TaskAttachmentForm()

    return render(
        request,
        "tasks/update_task.html",
        {
            "task": task,
            "form": form,
            "attachment_form": attachment_form,
            "breadcrumbs": [
                {"url": reverse("dashboard:dashboard"), "label": "Dashboard"},
                {"url": reverse("tasks:task_list"), "label": "Tasks"},
                {"label": "Edit Task"},
            ],
        },
    )


@login_required
def delete_task(request, id):
    if not is_manager_or_superuser(request.user):
        return HttpResponseForbidden("Permission denied.")

    task = get_object_or_404(Task, id=id)

    if request.method == "POST":
        task.delete()
        messages.success(request, "Task deleted successfully!")
        return redirect("tasks:task_list")

    return render(
        request,
        "tasks/delete_task.html",
        {
            "task": task,
            "breadcrumbs": [
                {"url": reverse("dashboard:dashboard"), "label": "Dashboard"},
                {"url": reverse("tasks:task_list"), "label": "Tasks"},
                {"url": reverse("tasks:task_detail", kwargs={"id": task.id}), "label": task.title},
                {"label": "Delete"},
            ],
        },
    )
