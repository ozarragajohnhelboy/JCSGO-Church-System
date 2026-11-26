from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from ..models import ActivityLog, GroupLeaveRequest, RegularMember
from ..services.care_group_hierarchy import can_manage_care_group

MIN_REASON_LENGTH = 10
MAX_REASON_LENGTH = 500


def _member_group(user):
    try:
        return RegularMember.objects.select_related('group', 'group__leader').get(user=user).group
    except RegularMember.DoesNotExist:
        return None


@login_required
@require_POST
def group_leave_request(request):
    """Member submits a leave request. The group leader must approve it."""
    user = request.user
    group = _member_group(user)
    if group is None:
        messages.error(request, 'You are not assigned to a group.')
        return redirect('churches:dashboard')

    if group.church_id != user.church_id:
        messages.error(request, 'You cannot leave a group outside your church.')
        return redirect('churches:dashboard')

    if group.leader_id == user.id:
        messages.error(
            request,
            'You lead this group. Assign a new leader before requesting to leave.',
        )
        return redirect('churches:dashboard')

    reason = (request.POST.get('reason') or '').strip()
    if len(reason) < MIN_REASON_LENGTH:
        messages.error(request, 'Please explain why you want to leave (at least 10 characters).')
        return redirect('churches:dashboard')
    if len(reason) > MAX_REASON_LENGTH:
        messages.error(request, 'Keep the leave reason under 500 characters.')
        return redirect('churches:dashboard')

    pending = GroupLeaveRequest.objects.filter(member=user, group=group, status='PENDING').exists()
    if pending:
        messages.warning(request, 'Your leave request is already waiting for your leader to review.')
        return redirect('churches:dashboard')

    GroupLeaveRequest.objects.create(
        member=user,
        group=group,
        church=group.church,
        reason=reason,
    )
    ActivityLog.objects.create(
        user=user,
        church=user.church,
        action='GROUP_LEAVE',
        description=f'Requested to leave {group.name}',
        related_user=group.leader,
    )
    messages.success(request, f'Leave request sent to {group.leader.full_name}. You stay in the group until they approve it.')
    return redirect('churches:dashboard')


@login_required
@require_POST
def group_leave_review(request, request_id):
    """Group leader or admin approves or rejects a pending leave request."""
    user = request.user
    leave_request = get_object_or_404(
        GroupLeaveRequest.objects.select_related('group', 'member', 'church'),
        pk=request_id,
        church=user.church,
    )
    group = leave_request.group

    if not can_manage_care_group(user, group) and group.leader_id != user.id:
        messages.error(request, 'You do not have permission to review this leave request.')
        return _review_redirect(group)

    if leave_request.status != 'PENDING':
        messages.warning(request, 'This leave request was already reviewed.')
        return _review_redirect(group)

    action = request.POST.get('action')
    leave_request.reviewed_by = user
    leave_request.reviewed_at = timezone.now()

    if action == 'approve':
        group.remove_member(leave_request.member)
        leave_request.status = 'APPROVED'
        leave_request.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'updated_at'])
        ActivityLog.objects.create(
            user=leave_request.member,
            church=group.church,
            action='GROUP_LEAVE',
            description=f'Left {group.name} (approved by {user.full_name})',
            related_user=user,
        )
        messages.success(request, f'{leave_request.member.full_name} has been removed from {group.name}.')
    elif action == 'reject':
        leave_request.status = 'REJECTED'
        leave_request.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'updated_at'])
        messages.info(request, f'Leave request from {leave_request.member.full_name} was declined.')
    else:
        messages.error(request, 'Choose approve or reject.')

    return _review_redirect(group)


def _review_redirect(group):
    if group.group_type == 'CARE':
        return redirect('members:care_group_detail', group_id=group.pk)
    return redirect('members:group_detail', pk=group.pk)
