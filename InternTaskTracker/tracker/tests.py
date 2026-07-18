from datetime import date, time, timedelta
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from tracker.invites import create_invitation
from tracker.models import Conversation, Department, Invitation, Message, Task, TaskReview, User
from tracker.permissions import (
    can_delete_task,
    can_edit_task,
    can_message,
    can_review_task,
    can_submit_task,
    visible_tasks_for,
)


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

    def test_overnight_duration(self):
        task = Task.objects.create(
            intern=self.intern, title="Night shift", date=date(2026, 7, 17),
            start_time=time(22, 0), end_time=time(2, 0),
        )
        self.assertEqual(task.duration, timedelta(hours=4))


class InviteTests(TestCase):
    def setUp(self):
        self.it = Department.objects.create(name="IT")
        self.head = User.objects.create_user(
            username="head", password="pass12345", role=User.Roles.HEAD,
            department=self.it, email="head@test.com", email_verified=True)
        self.supervisor = User.objects.create_user(
            username="sup", password="pass12345", role=User.Roles.SUPERVISOR,
            department=self.it, email="sup@test.com", email_verified=True)

    def test_accept_invite_sets_password_and_verifies(self):
        invitee = User.objects.create(
            username="newsup", email="newsup@test.com",
            role=User.Roles.SUPERVISOR, department=self.it,
            must_set_password=True, email_verified=False)
        invitee.set_unusable_password()
        invitee.save()
        invitation = create_invitation(invitee, self.head)
        url = reverse("accept_invite", args=[invitation.token])
        response = self.client.post(url, {
            "new_password1": "StrongPass123!",
            "new_password2": "StrongPass123!",
        })
        self.assertEqual(response.status_code, 302)
        invitee.refresh_from_db()
        invitation.refresh_from_db()
        self.assertTrue(invitee.email_verified)
        self.assertFalse(invitee.must_set_password)
        self.assertTrue(invitee.check_password("StrongPass123!"))
        self.assertIsNotNone(invitation.accepted_at)

    def test_expired_invite_rejected(self):
        invitee = User.objects.create(
            username="late", email="late@test.com",
            role=User.Roles.INTERN, department=self.it,
            supervisor=self.supervisor, must_set_password=True)
        invitee.set_unusable_password()
        invitee.save()
        invitation = create_invitation(invitee, self.head)
        invitation.expires_at = timezone.now() - timedelta(days=1)
        invitation.save(update_fields=["expires_at"])
        response = self.client.get(reverse("accept_invite", args=[invitation.token]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("login"))

    def test_resend_invite_requires_post(self):
        self.client.login(username="head", password="pass12345")
        invitee = User.objects.create(
            username="pending", email="pending@test.com",
            role=User.Roles.INTERN, department=self.it,
            supervisor=self.supervisor, must_set_password=True)
        invitee.set_unusable_password()
        invitee.save()
        create_invitation(invitee, self.head)
        response = self.client.get(reverse("resend_invite", args=[invitee.pk]))
        self.assertEqual(response.status_code, 405)


class ReviewFlowTests(TestCase):
    def setUp(self):
        self.it = Department.objects.create(name="IT")
        self.hr = Department.objects.create(name="HR")
        self.supervisor = User.objects.create_user(
            username="sup", password="pass12345", role=User.Roles.SUPERVISOR,
            department=self.it, email="sup@test.com", email_verified=True)
        self.intern = User.objects.create_user(
            username="intern", password="pass12345", role=User.Roles.INTERN,
            department=self.it, supervisor=self.supervisor,
            email="intern@test.com", email_verified=True)
        self.hr_head = User.objects.create_user(
            username="hrhead", password="pass12345", role=User.Roles.HEAD,
            department=self.hr, email="hrhead@test.com", email_verified=True)
        self.task = Task.objects.create(
            intern=self.intern, title="Report writeup",
            date=date(2026, 7, 17), start_time=time(9, 0), end_time=time(12, 0),
            status=Task.Status.IN_PROGRESS,
        )

    def test_submit_request_changes_resubmit_approve(self):
        self.assertTrue(can_submit_task(self.intern, self.task))
        self.client.login(username="intern", password="pass12345")
        response = self.client.post(reverse("task_submit", args=[self.task.pk]))
        self.assertEqual(response.status_code, 302)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.SUBMITTED)
        self.assertFalse(can_edit_task(self.intern, self.task))
        self.assertTrue(can_review_task(self.supervisor, self.task))

        self.client.login(username="sup", password="pass12345")
        response = self.client.post(reverse("task_review", args=[self.task.pk]), {
            "action": "REQUEST_CHANGES",
            "comment": "Please add more detail.",
        })
        self.assertEqual(response.status_code, 302)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.CHANGES_REQUESTED)
        self.assertEqual(self.task.reviews.count(), 1)

        self.assertTrue(can_edit_task(self.intern, self.task))
        self.client.login(username="intern", password="pass12345")
        self.client.post(reverse("task_submit", args=[self.task.pk]))
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.SUBMITTED)

        self.client.login(username="sup", password="pass12345")
        self.client.post(reverse("task_review", args=[self.task.pk]), {
            "action": "APPROVE",
            "comment": "Looks good.",
        })
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.APPROVED)
        self.assertEqual(self.task.reviews.count(), 2)
        self.assertFalse(can_edit_task(self.intern, self.task))
        self.assertFalse(can_delete_task(self.intern, self.task))

    def test_cross_department_reviewer_blocked(self):
        self.task.status = Task.Status.SUBMITTED
        self.task.save(update_fields=["status"])
        self.assertFalse(can_review_task(self.hr_head, self.task))
        self.client.login(username="hrhead", password="pass12345")
        response = self.client.post(reverse("task_review", args=[self.task.pk]), {
            "action": "APPROVE", "comment": "",
        })
        self.assertEqual(response.status_code, 302)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.SUBMITTED)


class AttachmentAccessTests(TestCase):
    def setUp(self):
        self.it = Department.objects.create(name="IT")
        self.hr = Department.objects.create(name="HR")
        self.supervisor = User.objects.create_user(
            username="sup", password="pass12345", role=User.Roles.SUPERVISOR,
            department=self.it, email="sup@test.com", email_verified=True)
        self.intern = User.objects.create_user(
            username="intern", password="pass12345", role=User.Roles.INTERN,
            department=self.it, supervisor=self.supervisor,
            email="intern@test.com", email_verified=True)
        self.outsider = User.objects.create_user(
            username="outsider", password="pass12345", role=User.Roles.INTERN,
            department=self.hr, email="out@test.com", email_verified=True)
        upload = SimpleUploadedFile("notes.txt", b"secret notes", content_type="text/plain")
        self.task = Task.objects.create(
            intern=self.intern, title="With file",
            date=date(2026, 7, 17), start_time=time(9, 0), end_time=time(10, 0),
            attachment=upload,
        )

    def test_owner_can_download(self):
        self.client.login(username="intern", password="pass12345")
        response = self.client.get(reverse("task_attachment", args=[self.task.pk]))
        self.assertEqual(response.status_code, 200)

    def test_outsider_forbidden(self):
        self.client.login(username="outsider", password="pass12345")
        response = self.client.get(reverse("task_attachment", args=[self.task.pk]))
        self.assertEqual(response.status_code, 403)


class NotificationAndChatPollTests(TestCase):
    def setUp(self):
        self.it = Department.objects.create(name="IT")
        self.supervisor = User.objects.create_user(
            username="sup", password="pass12345", role=User.Roles.SUPERVISOR,
            department=self.it, email="sup@test.com", email_verified=True)
        self.intern = User.objects.create_user(
            username="intern", password="pass12345", role=User.Roles.INTERN,
            department=self.it, supervisor=self.supervisor,
            email="intern@test.com", email_verified=True)

    def test_notifications_list_does_not_mark_all_read(self):
        from tracker.models import Notification
        n1 = Notification.objects.create(
            user=self.intern, title="One", message="a", link="/dashboard/")
        n2 = Notification.objects.create(
            user=self.intern, title="Two", message="b", link="/tasks/")
        self.client.login(username="intern", password="pass12345")
        response = self.client.get(reverse("notifications"))
        self.assertEqual(response.status_code, 200)
        n1.refresh_from_db()
        n2.refresh_from_db()
        self.assertFalse(n1.is_read)
        self.assertFalse(n2.is_read)

    def test_notification_open_marks_one_read(self):
        from tracker.models import Notification
        item = Notification.objects.create(
            user=self.intern, title="Review", message="changes", link="/dashboard/")
        self.client.login(username="intern", password="pass12345")
        response = self.client.get(reverse("notification_open", args=[item.pk]))
        self.assertEqual(response.status_code, 302)
        item.refresh_from_db()
        self.assertTrue(item.is_read)

    def test_chat_poll_returns_new_messages(self):
        conv, _ = Conversation.between(self.intern, self.supervisor)
        first = Message.objects.create(conversation=conv, sender=self.intern, body="Hi")
        self.client.login(username="supervisor", password="pass12345")
        # supervisor username is "sup"
        self.client.logout()
        self.client.login(username="sup", password="pass12345")
        response = self.client.get(
            reverse("chat_poll", args=[conv.pk]),
            {"after": 0},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["messages"]), 1)
        self.assertEqual(data["messages"][0]["id"], first.pk)
        self.assertFalse(data["messages"][0]["mine"])

        Message.objects.create(conversation=conv, sender=self.intern, body="Again")
        response = self.client.get(
            reverse("chat_poll", args=[conv.pk]),
            {"after": first.pk},
        )
        self.assertEqual(len(response.json()["messages"]), 1)
        self.assertEqual(response.json()["messages"][0]["body"], "Again")
