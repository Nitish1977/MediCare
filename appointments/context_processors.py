from .models import Notification


def notifications(request):
    """Context processor to provide notifications for authenticated users."""
    if request.user.is_authenticated:
        qs = Notification.objects.filter(user=request.user)
        unread_count = qs.filter(is_read=False).count()
        return {
            'notifications': qs[:10],
            'unread_notifications_count': unread_count,
        }
    return {
        'notifications': [],
        'unread_notifications_count': 0,
    }
