import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.notifications.models import Notification, TaskUpdate
from tasks.models import Task

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Task)
def create_task_assignment_notification(sender, instance, created, **kwargs):
    """Create notification when a new task is assigned."""
    if created and instance.assigned_to:
        Notification.objects.create(
            user=instance.assigned_to,
            actor=instance.project.manager if instance.project else None,
            verb="Task Assigned",
            description=f"You have been assigned a new task: {instance.title}",
            related_task=instance,
        )


@receiver(post_save, sender=TaskUpdate)
def create_task_update_notification(sender, instance, created, **kwargs):
    """Create notification when an employee updates task progress."""
    if created:
        task = instance.task
        # Notify the task manager/assigner
        if task.project and task.project.manager:
            Notification.objects.create(
                user=task.project.manager,
                actor=instance.user,
                verb="Task Updated",
                description=(
                    f"{instance.user.get_display_name()} updated task "
                    f"'{task.title}' from {instance.old_status} to {instance.new_status}"
                ),
                related_task=task,
            )
