"""Current church announcements for dashboards and the inbox context processor."""

from django.db.models import Q
from django.utils import timezone

from churches.models import ChurchAnnouncement


def current_announcements_for(user, limit=5):
    if not user or not getattr(user, 'church_id', None):
        return ChurchAnnouncement.objects.none()

    today = timezone.localdate()
    return ChurchAnnouncement.objects.filter(
        church_id=user.church_id,
        is_active=True,
    ).filter(
        Q(end_date__isnull=True) | Q(end_date__date__gte=today)
    ).order_by('-created_at')[:limit]
