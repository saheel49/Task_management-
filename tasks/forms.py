from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from apps.utils.permissions import is_manager_or_superuser

from .models import Project, Task, TaskAttachment

User = get_user_model()


class TaskAttachmentForm(forms.ModelForm):
    file = forms.FileField(
        label=_("Attachment"),
        required=False,
        help_text=_("You can upload multiple files."),
    )

    class Meta:
        model = TaskAttachment
        fields = ["file"]


class TaskForm(forms.ModelForm):
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        label="Assign To",
        widget=forms.Select(attrs={"class": "select select-bordered w-full"}),
    )

    class Meta:
        model = Task
        fields = ["title", "description", "project", "priority", "status", "due_date", "assigned_to", "completion_note"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "input input-bordered w-full", "required": True}),
            "description": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 4}),
            "project": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "priority": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "status": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "due_date": forms.DateInput(attrs={"class": "input input-bordered w-full", "type": "date"}),
            "completion_note": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        status_only = kwargs.pop("status_only", False)
        super().__init__(*args, **kwargs)
        if user:
            if status_only:
                allowed_fields = ["status", "completion_note"]
                for field_name in list(self.fields.keys()):
                    if field_name not in allowed_fields:
                        self.fields.pop(field_name)
            elif is_manager_or_superuser(user):
                self.fields["project"].queryset = Project.objects.all()
                self.fields["assigned_to"].queryset = User.objects.filter(is_active=True).order_by("email")
                self.fields["assigned_to"].required = True
            else:
                self.fields["project"].queryset = Project.objects.filter(manager=user)
                self.fields["assigned_to"].widget = forms.HiddenInput()
                self.fields["assigned_to"].initial = user
                self.fields["assigned_to"].required = False

    def clean_title(self):
        title = self.cleaned_data.get("title", "").strip()
        if not title:
            raise forms.ValidationError(_("Task title is required."))
        return title

    def clean_due_date(self):
        due_date = self.cleaned_data.get("due_date")
        if due_date:
            from datetime import date

            if due_date < date.today():
                raise forms.ValidationError(_("Due date cannot be in the past."))
        return due_date


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "description", "status"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input input-bordered w-full", "required": True}),
            "description": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 4}),
            "status": forms.Select(attrs={"class": "select select-bordered w-full"}),
        }

    def clean_name(self):
        name = self.cleaned_data.get("name", "").strip()
        if not name:
            raise forms.ValidationError(_("Project name is required."))
        return name
