"""Leadership hierarchy rules for care groups and care group reports.

Hierarchy: Vine Servant Leader -> Cluster Servant Leader -> Care Leader -> Care Member.

A leader's downline is every user who is a member of a care group the leader
leads, plus the members of care groups led by those users, at any depth.
Visibility only flows downward: a leader never gains access to the reports of
anyone above them.
"""
from ..models import CustomUser

REPORT_ROLES = ('VSL', 'CSL', 'CL', 'ADMIN')


def _role_name(user):
    return user.role.name if getattr(user, 'role', None) else None


def get_downline_user_ids(user):
    """Return the IDs of every user under `user`, excluding `user` itself."""
    visited = {user.id}
    frontier = {user.id}
    downline = set()

    while frontier:
        member_ids = set(
            CustomUser.objects.filter(
                regular_member_profile__group__group_type='CARE',
                regular_member_profile__group__leader_id__in=frontier,
            ).values_list('id', flat=True)
        )
        frontier = member_ids - visited
        visited |= frontier
        downline |= frontier

    return downline


def get_scope_user_ids(user):
    """Return the IDs of `user` plus everyone under them."""
    return get_downline_user_ids(user) | {user.id}


def filter_visible_care_groups(user, care_groups):
    """Limit a Group queryset to care groups led by `user` or their downline."""
    if _role_name(user) == 'ADMIN':
        return care_groups
    return care_groups.filter(leader_id__in=get_scope_user_ids(user))


def filter_visible_reports(user, reports):
    """Limit a CareGroupReport queryset to reports made by `user` or their downline."""
    if _role_name(user) == 'ADMIN':
        return reports
    return reports.filter(created_by_id__in=get_scope_user_ids(user))


def can_access_report(user, report):
    """Whether `user` may view a report made by themselves or their downline."""
    role_name = _role_name(user)
    if role_name not in REPORT_ROLES:
        return False
    if role_name == 'ADMIN':
        return report.church_id == user.church_id
    return report.created_by_id in get_scope_user_ids(user)


def can_manage_care_group(user, care_group):
    """Whether `user` leads this care group or sits above its leader."""
    role_name = _role_name(user)
    if role_name == 'ADMIN':
        return care_group.church_id == user.church_id
    if role_name not in REPORT_ROLES:
        return False
    return care_group.leader_id in get_scope_user_ids(user)
