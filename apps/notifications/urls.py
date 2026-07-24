from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    path("notifications/", views.notifications_dropdown, name="notifications_dropdown"),
    path("notifications/read/<int:notification_id>/", views.mark_notification_read, name="mark_notification_read"),
    path("notifications/unread-count/", views.unread_count, name="unread_count"),
]
