from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

from .models import Notification


@login_required
def notifications_dropdown(request):
    notifications = request.user.notifications.filter(read=False)[:20]
    return render(
        request,
        "notifications/dropdown.html",
        {"notifications": notifications},
    )


@login_required
def mark_notification_read(request, notification_id):
    if request.method == "POST":
        try:
            notification = request.user.notifications.get(id=notification_id)
            notification.read = True
            notification.save()
            return JsonResponse({"status": "ok"})
        except Notification.DoesNotExist:
            return JsonResponse({"status": "error"}, status=404)
    return JsonResponse({"status": "error"}, status=400)


@login_required
def unread_count(request):
    count = request.user.notifications.filter(read=False).count()
    return JsonResponse({"count": count})
