from files.models import Notification


def notification_context(request):
    if not request.user.is_authenticated:
        return {
            'unread_notification_count': 0,
            'recent_notifications': [],
        }

    recent_notifications = Notification.objects.filter(user=request.user)[:5]
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    return {
        'unread_notification_count': unread_count,
        'recent_notifications': recent_notifications,
    }
