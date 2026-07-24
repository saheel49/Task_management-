from django.urls import path

from . import project_views, views

app_name = "tasks"

urlpatterns = [
    path("", views.task_list, name="task_list"),
    path("create/", views.create_task, name="create_task"),
    path("<int:id>/", views.task_detail, name="task_detail"),
    path("<int:id>/update/", views.update_task, name="update_task"),
    path("<int:id>/delete/", views.delete_task, name="delete_task"),
    path("updates/", views.task_updates, name="task_updates"),
    path("projects/", project_views.project_list, name="project_list"),
    path("projects/<int:id>/", project_views.project_detail, name="project_detail"),
    path("projects/create/", project_views.project_create, name="project_create"),
    path("projects/<int:id>/update/", project_views.project_update, name="project_update"),
    path("projects/<int:id>/delete/", project_views.project_delete, name="project_delete"),
]
