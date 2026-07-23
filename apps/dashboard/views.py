from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render
from django.urls import reverse

from apps.utils.permissions import is_manager_or_superuser
from tasks.models import Project, Task

User = get_user_model()


@login_required
def dashboard(request):
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    user = request.user
    is_manager = is_manager_or_superuser(user)

    if is_manager:
        base_task_qs = Task.objects.all()
        base_project_qs = Project.objects.all()
    else:
        base_task_qs = Task.objects.filter(assigned_to=user)
        base_project_qs = Project.objects.filter(manager=user)

    total_tasks = base_task_qs.count()
    completed_tasks = base_task_qs.filter(status="completed").count()
    todo_tasks = base_task_qs.filter(status="todo").count()
    in_progress_tasks = base_task_qs.filter(status="progress").count()
    high_priority_tasks = base_task_qs.filter(priority="high").count()
    low_priority_tasks = base_task_qs.filter(priority="low").count()
    total_projects = base_project_qs.count()
    active_projects = base_project_qs.filter(status="active").count()
    recent_tasks = base_task_qs.order_by("-created_at")[:5]
    recent_projects = base_project_qs.order_by("-created_at")[:5]
    overdue_tasks = base_task_qs.filter(
        due_date__lt=today, status__in=["todo", "progress"]
    ).count()
    due_today_tasks = base_task_qs.filter(
        due_date=today, status__in=["todo", "progress"]
    ).count()
    due_this_week_tasks = base_task_qs.filter(
        due_date__gte=week_start, due_date__lte=week_end, status__in=["todo", "progress"]
    ).count()
    upcoming_tasks = base_task_qs.filter(
        due_date__gte=today, status__in=["todo", "progress"]
    ).order_by("due_date")[:5]

    completion_percentage = round((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0

    status_data = {
        "todo": todo_tasks,
        "progress": in_progress_tasks,
        "completed": completed_tasks,
    }

    priority_data = {
        "low": low_priority_tasks,
        "medium": base_task_qs.filter(priority="medium").count(),
        "high": high_priority_tasks,
    }

    chart_data = list(
        base_task_qs.values("created_at__date")
        .annotate(count=Count("id"))
        .order_by("created_at__date")[:14]
    )

    date_counts = {item["created_at__date"]: item["count"] for item in chart_data}
    chart_labels = []
    chart_values = []
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        chart_labels.append(d.strftime("%b %d"))
        chart_values.append(date_counts.get(d, 0))

    context = {
        "page_title": "Dashboard",
        "is_manager": is_manager,
        "total_users": User.objects.count(),
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "todo_tasks": todo_tasks,
        "in_progress_tasks": in_progress_tasks,
        "high_priority_tasks": high_priority_tasks,
        "low_priority_tasks": low_priority_tasks,
        "completion_percentage": completion_percentage,
        "overdue_tasks": overdue_tasks,
        "due_today_tasks": due_today_tasks,
        "due_this_week_tasks": due_this_week_tasks,
        "total_projects": total_projects,
        "active_projects": active_projects,
        "recent_tasks": recent_tasks,
        "recent_projects": recent_projects,
        "upcoming_tasks": upcoming_tasks,
        "today": today,
        "status_data": status_data,
        "priority_data": priority_data,
        "tasks_per_day_labels": chart_labels,
        "tasks_per_day_values": chart_values,
        "breadcrumbs": [
            {"label": "Dashboard"},
        ],
    }

    return render(
        request,
        "dashboard/dashboard.html",
        context,
    )
