from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.users.models import CustomUser
from apps.utils.permissions import is_manager_or_superuser
from tasks.models import Project, Task

TEST_STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


@override_settings(STORAGES=TEST_STORAGES)
class RoleBasedTaskPermissionTests(TestCase):
    """Tests enforcing role-based task assignment and editing rules."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = Client()

        cls.manager = CustomUser.objects.create_user(
            email="manager@example.com",
            password="ManagerPass123!",
            user_type="manager",
        )
        cls.employee = CustomUser.objects.create_user(
            email="employee@example.com",
            password="EmployeePass123!",
            user_type="employee",
        )
        cls.other_employee = CustomUser.objects.create_user(
            email="other@example.com",
            password="OtherPass123!",
            user_type="employee",
        )

        cls.project = Project.objects.create(
            name="Test Project",
            description="A test project",
            manager=cls.manager,
        )

    def test_is_manager_or_superuser_helper(self):
        self.assertTrue(is_manager_or_superuser(self.manager))
        self.assertFalse(is_manager_or_superuser(self.employee))
        self.assertFalse(is_manager_or_superuser(self.other_employee))

    def test_manager_can_assign_task_to_self(self):
        self.client.login(email="manager@example.com", password="ManagerPass123!")
        response = self.client.post(
            reverse("tasks:create_task"),
            {
                "title": "Manager Self-Assigned Task",
                "description": "Testing self-assignment",
                "project": self.project.id,
                "priority": "medium",
                "status": "todo",
                "assigned_to": self.manager.id,
            },
        )
        self.assertEqual(response.status_code, 302)
        task = Task.objects.get(title="Manager Self-Assigned Task")
        self.assertEqual(task.assigned_to, self.manager)
        task.delete()

    def test_manager_can_assign_task_to_employee(self):
        self.client.login(email="manager@example.com", password="ManagerPass123!")
        response = self.client.post(
            reverse("tasks:create_task"),
            {
                "title": "Manager Assigned to Employee",
                "description": "Testing assignment to employee",
                "project": self.project.id,
                "priority": "medium",
                "status": "todo",
                "assigned_to": self.employee.id,
            },
        )
        self.assertEqual(response.status_code, 302)
        task = Task.objects.get(title="Manager Assigned to Employee")
        self.assertEqual(task.assigned_to, self.employee)
        task.delete()

    def test_employee_cannot_assign_task(self):
        self.client.login(email="employee@example.com", password="EmployeePass123!")
        response = self.client.post(
            reverse("tasks:create_task"),
            {
                "title": "Employee Trying to Assign",
                "description": "Should fail assignment",
                "project": self.project.id,
                "priority": "medium",
                "status": "todo",
                "assigned_to": self.other_employee.id,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard:dashboard"))
        task = Task.objects.filter(title="Employee Trying to Assign").first()
        self.assertIsNone(task)

    def test_employee_cannot_access_create_task_page(self):
        self.client.login(email="employee@example.com", password="EmployeePass123!")
        response = self.client.get(reverse("tasks:create_task"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard:dashboard"))

    def test_employee_is_auto_assigned_to_self(self):
        self.client.login(email="employee@example.com", password="EmployeePass123!")
        response = self.client.post(
            reverse("tasks:create_task"),
            {
                "title": "Employee Self-Created Task",
                "description": "Should be auto-assigned",
                "project": self.project.id,
                "priority": "medium",
                "status": "todo",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard:dashboard"))
        task = Task.objects.filter(title="Employee Self-Created Task").first()
        self.assertIsNone(task)

    def test_employee_sees_only_own_tasks(self):
        task = Task.objects.create(
            title="Employee Task",
            description="Owned by employee",
            project=self.project,
            assigned_to=self.employee,
            status="todo",
            priority="medium",
        )
        Task.objects.create(
            title="Other Employee Task",
            description="Owned by other employee",
            project=self.project,
            assigned_to=self.other_employee,
            status="todo",
            priority="medium",
        )

        self.client.login(email="employee@example.com", password="EmployeePass123!")
        response = self.client.get(reverse("tasks:task_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Employee Task")
        self.assertNotContains(response, "Other Employee Task")
        task.delete()

    def test_manager_sees_all_tasks(self):
        task1 = Task.objects.create(
            title="Task 1",
            description="For employee",
            project=self.project,
            assigned_to=self.employee,
            status="todo",
            priority="medium",
        )
        task2 = Task.objects.create(
            title="Task 2",
            description="For other employee",
            project=self.project,
            assigned_to=self.other_employee,
            status="todo",
            priority="medium",
        )

        self.client.login(email="manager@example.com", password="ManagerPass123!")
        response = self.client.get(reverse("tasks:task_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Task 1")
        self.assertContains(response, "Task 2")
        task1.delete()
        task2.delete()

    def test_employee_cannot_edit_assignee(self):
        task = Task.objects.create(
            title="Task for assignee edit",
            description="Testing assignee lock",
            project=self.project,
            assigned_to=self.employee,
            status="todo",
            priority="medium",
        )

        self.client.login(email="employee@example.com", password="EmployeePass123!")
        response = self.client.get(reverse("tasks:update_task", args=[task.id]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Assigned To")

        response = self.client.post(
            reverse("tasks:update_task", args=[task.id]),
            {
                "assigned_to": self.other_employee.id,
                "status": "progress",
            },
        )
        task.refresh_from_db()
        self.assertEqual(task.assigned_to, self.employee)
        task.delete()

    def test_employee_can_update_only_status(self):
        task = Task.objects.create(
            title="Task for status update",
            description="Testing status update",
            project=self.project,
            assigned_to=self.employee,
            status="todo",
            priority="medium",
        )

        self.client.login(email="employee@example.com", password="EmployeePass123!")
        response = self.client.post(
            reverse("tasks:update_task", args=[task.id]),
            {"status": "progress"},
        )
        self.assertEqual(response.status_code, 302)
        task.refresh_from_db()
        self.assertEqual(task.status, "progress")
        task.delete()

    def test_employee_cannot_update_other_fields(self):
        task = Task.objects.create(
            title="Original Title",
            description="Original desc",
            project=self.project,
            assigned_to=self.employee,
            status="todo",
            priority="low",
        )

        self.client.login(email="employee@example.com", password="EmployeePass123!")
        self.client.post(
            reverse("tasks:update_task", args=[task.id]),
            {
                "status": "progress",
                "title": "Hacked Title",
                "description": "Hacked desc",
                "priority": "high",
            },
        )
        task.refresh_from_db()
        self.assertEqual(task.title, "Original Title")
        self.assertEqual(task.description, "Original desc")
        self.assertEqual(task.priority, "low")
        task.delete()

    def test_employee_cannot_delete_task(self):
        task = Task.objects.create(
            title="Task for delete test",
            description="Testing delete restriction",
            project=self.project,
            assigned_to=self.employee,
            status="todo",
            priority="medium",
        )

        self.client.login(email="employee@example.com", password="EmployeePass123!")
        response = self.client.post(reverse("tasks:delete_task", args=[task.id]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Task.objects.filter(id=task.id).exists())
        task.delete()

    def test_manager_can_delete_any_task(self):
        task = Task.objects.create(
            title="Task for manager delete",
            description="Testing manager delete",
            project=self.project,
            assigned_to=self.employee,
            status="todo",
            priority="medium",
        )

        self.client.login(email="manager@example.com", password="ManagerPass123!")
        response = self.client.post(reverse("tasks:delete_task", args=[task.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Task.objects.filter(id=task.id).exists())

    def test_manager_can_update_any_task(self):
        task = Task.objects.create(
            title="Task for manager update",
            description="Original desc",
            project=self.project,
            assigned_to=self.employee,
            status="todo",
            priority="low",
        )

        self.client.login(email="manager@example.com", password="ManagerPass123!")
        response = self.client.post(
            reverse("tasks:update_task", args=[task.id]),
            {
                "title": "Updated Title",
                "description": "Updated desc",
                "project": self.project.id,
                "priority": "high",
                "status": "progress",
                "due_date": "",
                "assigned_to": self.employee.id,
            },
        )
        self.assertEqual(response.status_code, 302)
        task.refresh_from_db()
        self.assertEqual(task.title, "Updated Title")
        self.assertEqual(task.status, "progress")
        task.delete()

    def test_employee_get_update_page_shows_only_status(self):
        task = Task.objects.create(
            title="Task for status-only form",
            description="Original desc",
            project=self.project,
            assigned_to=self.employee,
            status="todo",
            priority="low",
        )

        self.client.login(email="employee@example.com", password="EmployeePass123!")
        response = self.client.get(reverse("tasks:update_task", args=[task.id]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Title")
        self.assertNotContains(response, "Description")
        self.assertNotContains(response, "Priority")
        self.assertNotContains(response, "Due Date")
        self.assertNotContains(response, "Project")
        self.assertContains(response, "Status")
        task.delete()

    def test_manager_get_update_page_shows_all_fields(self):
        task = Task.objects.create(
            title="Task for full form",
            description="Original desc",
            project=self.project,
            assigned_to=self.employee,
            status="todo",
            priority="low",
        )

        self.client.login(email="manager@example.com", password="ManagerPass123!")
        response = self.client.get(reverse("tasks:update_task", args=[task.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Title")
        self.assertContains(response, "Description")
        self.assertContains(response, "Assign To")
        self.assertContains(response, "Priority")
        self.assertContains(response, "Status")
        self.assertContains(response, "Due Date")
        self.assertContains(response, "Project")
        task.delete()
