from churches.services.announcements import current_announcements_for
from members.services.leave_alerts import own_pending_leave_exists, pending_leave_count


def church_inbox(request):
    """Leave-request counts and current announcements on every authenticated page."""
    user = getattr(request, 'user', None)
    empty = {
        'pending_leave_count': 0,
        'own_pending_leave': False,
        'current_announcements': [],
    }
    if not user or not user.is_authenticated or user.is_superuser:
        return empty
    if not getattr(user, 'church_id', None):
        return empty

    return {
        'pending_leave_count': pending_leave_count(user),
        'own_pending_leave': own_pending_leave_exists(user),
        'current_announcements': current_announcements_for(user),
    }
