from datetime import date, time

from django.test import TestCase
from django.urls import reverse

from tracker.models import Conversation, Department, Message, Task, User
from tracker.permissions import can_message, visible_tasks_for


class RBACAndChatTests(TestCase):
    def setUp(self):
        self.it = Department.objects.create(name="IT")
        self.hr = Department.objects.create(name="HR")

        self.head = User.objects.create_user(
            username="head", password="pass12345", role=User.Roles.HEAD,
            department=self.it, email="head@test.com", email_verified=True)
        self.supervisor = User.objects.create_user(
            username="sup", password="pass12345", role=User.Roles.SUPERVISOR,
            department=self.it, email="sup@test.com", email_verified=True)
        self.intern = User.objects.create_user(
            username="intern", password="pass12345", role=User.Roles.INTERN,
            department=self.it, supervisor=self.supervisor,
            email="intern@test.com", email_verified=True)
        self.other_intern = User.objects.create_user(
            username="intern2", password="pass12345", role=User.Roles.INTERN,
            department=self.it, supervisor=self.supervisor,
            email="intern2@test.com", email_verified=True)
        self.hr_intern = User.objects.create_user(
            username="hrintern", password="pass12345", role=User.Roles.INTERN,
            department=self.hr, email="hrintern@test.com", email_verified=True)
        self.hr_head = User.objects.create_user(
            username="hrhead", password="pass12345", role=User.Roles.HEAD,
            department=self.hr, email="hrhead@test.com", email_verified=True)

        self.task = Task.objects.create(
            intern=self.intern,
            title="Build feature",
            date=date(2026, 7, 17),
            start_time=time(9, 0),
            end_time=time(11, 0),
        )

    def test_supervisor_sees_only_assigned_intern_tasks(self):
        qs = visible_tasks_for(self.supervisor)
        self.assertIn(self.task, qs)

        outsider = User.objects.create_user(
            username="sup2", password="pass12345", role=User.Roles.SUPERVISOR,
            department=self.it, email="sup2@test.com", email_verified=True)
        self.assertNotIn(self.task, visible_tasks_for(outsider))

    def test_head_sees_department_tasks_only(self):
        self.assertIn(self.task, visible_tasks_for(self.head))
        self.assertNotIn(self.task, visible_tasks_for(self.hr_head))

    def test_chat_rules(self):
        self.assertTrue(can_message(self.intern, self.other_intern))
        self.assertFalse(can_message(self.intern, self.hr_intern))
        self.assertTrue(can_message(self.intern, self.supervisor))
        self.assertTrue(can_message(self.intern, self.head))
        self.assertTrue(can_message(self.supervisor, self.hr_head))
        self.assertFalse(can_message(self.intern, self.hr_head))

    def test_chat_thread_access(self):
        conv, _ = Conversation.between(self.intern, self.supervisor)
        Message.objects.create(conversation=conv, sender=self.intern, body="Hello")

        self.client.login(username="intern", password="pass12345")
        response = self.client.get(reverse("chat_thread", args=[conv.pk]))
        self.assertEqual(response.status_code, 200)

        self.client.login(username="hrintern", password="pass12345")
        response = self.client.get(reverse("chat_thread", args=[conv.pk]))
        self.assertEqual(response.status_code, 403)

    def test_login_page_loads(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
