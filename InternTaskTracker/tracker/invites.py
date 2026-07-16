import secrets
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone

from .models import Invitation


INVITE_EXPIRY_DAYS = 7


def create_invitation(user, invited_by):
    token = secrets.token_urlsafe(32)
    invitation, _ = Invitation.objects.update_or_create(
        user=user,
        defaults={
            "invited_by": invited_by,
            "token": token,
            "accepted_at": None,
            "expires_at": timezone.now() + timedelta(days=INVITE_EXPIRY_DAYS),
        },
    )
    return invitation


def invitation_absolute_url(request, invitation):
    path = reverse("accept_invite", kwargs={"token": invitation.token})
    return request.build_absolute_uri(path)


def send_invitation_email(request, invitation):
    user = invitation.user
    link = invitation_absolute_url(request, invitation)
    role = user.get_role_display()
    department = user.department.name if user.department else "your department"
    subject = "You're invited to InTrack — verify your email & set a password"
    message = (
        f"Hello {user.get_full_name() or user.username},\n\n"
        f"You have been added to InTrack as a {role} in {department}.\n\n"
        f"Please verify your email and set your password using this link:\n"
        f"{link}\n\n"
        f"This link expires in {INVITE_EXPIRY_DAYS} days.\n\n"
        f"If you were not expecting this invitation, you can ignore this email.\n\n"
        f"— InTrack"
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
    return link
