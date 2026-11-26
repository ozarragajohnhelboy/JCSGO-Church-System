"""Pending group-leave queries shared by dashboards and the inbox context processor."""

from ..models import GroupLeaveRequest
from .care_group_hierarchy import REPORT_ROLES, get_scope_user_ids


def _role_name(user):
    return user.role.name if getattr(user, 'role', None) else None


def pending_leave_queryset(user):
    """Leave requests the user may review, scoped to their church."""
    empty = GroupLeaveRequest.objects.none()
    if not user or not getattr(user, 'is_authenticated', False):
        return empty
    if not getattr(user, 'church_id', None):
        return empty

    role = _role_name(user)
    qs = GroupLeaveRequest.objects.filter(
        status='PENDING',
        church_id=user.church_id,
    )
    if role == 'ADMIN':
        return qs.select_related('member', 'group')
    if role in REPORT_ROLES:
        return qs.filter(
            group__leader_id__in=get_scope_user_ids(user),
        ).select_related('member', 'group')
    return empty


def pending_leave_count(user):
    return pending_leave_queryset(user).count()


def own_pending_leave_exists(user):
    if not user or not getattr(user, 'church_id', None):
        return False
    return GroupLeaveRequest.objects.filter(
        member=user,
        church_id=user.church_id,
        status='PENDING',
    ).exists()
