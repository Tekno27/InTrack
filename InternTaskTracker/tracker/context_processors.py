from .models import Message


def notifications(request):
    if request.user.is_authenticated:
        count = request.user.notifications.filter(is_read=False).count()
        unread_messages = Message.objects.filter(
            conversation__participants=request.user,
            is_read=False,
        ).exclude(sender=request.user).count()
    else:
        count = 0
        unread_messages = 0
    return {
        "unread_notifications": count,
        "unread_messages": unread_messages,
    }
