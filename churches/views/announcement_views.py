from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from churches.announcement_forms import ChurchAnnouncementForm
from churches.models import ChurchAnnouncement
from churches.services.announcements import current_announcements_for


BOARD_ROLES = ('ADMIN', 'VSL', 'CSL', 'CL', 'CM')


def _role_name(user):
    return user.role.name if getattr(user, 'role', None) else None


def _require_church_admin(request):
    if _role_name(request.user) != 'ADMIN' or not request.user.church_id:
        messages.error(request, 'You do not have permission to manage announcements.')
        return redirect('churches:dashboard')
    return None


def _require_church_reader(request):
    if not request.user.church_id or _role_name(request.user) not in BOARD_ROLES:
        messages.error(request, 'You do not have permission to view announcements.')
        return redirect('churches:dashboard')
    return None


@login_required
def announcement_board(request):
    denied = _require_church_reader(request)
    if denied:
        return denied

    announcements = list(current_announcements_for(request.user, limit=50))
    return render(request, 'churches/announcements/board.html', {
        'announcements': announcements,
        'can_manage_announcements': _role_name(request.user) == 'ADMIN',
    })


@login_required
def announcement_list(request):
    denied = _require_church_admin(request)
    if denied:
        return denied

    announcements = ChurchAnnouncement.objects.filter(
        church_id=request.user.church_id,
    ).select_related('created_by').order_by('-created_at')

    return render(request, 'churches/announcements/list.html', {
        'announcements': announcements,
    })


@login_required
def announcement_create(request):
    denied = _require_church_admin(request)
    if denied:
        return denied

    if request.method == 'POST':
        form = ChurchAnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.church = request.user.church
            announcement.created_by = request.user
            announcement.save()
            messages.success(request, 'Announcement published.')
            return redirect('churches:announcement_list')
    else:
        form = ChurchAnnouncementForm()

    return render(request, 'churches/announcements/form.html', {
        'form': form,
        'is_edit': False,
    })


@login_required
def announcement_edit(request, announcement_id):
    denied = _require_church_admin(request)
    if denied:
        return denied

    announcement = get_object_or_404(
        ChurchAnnouncement,
        pk=announcement_id,
        church_id=request.user.church_id,
    )

    if request.method == 'POST':
        form = ChurchAnnouncementForm(request.POST, instance=announcement)
        if form.is_valid():
            form.save()
            messages.success(request, 'Announcement updated.')
            return redirect('churches:announcement_list')
    else:
        form = ChurchAnnouncementForm(instance=announcement)

    return render(request, 'churches/announcements/form.html', {
        'form': form,
        'announcement': announcement,
        'is_edit': True,
    })


@login_required
@require_POST
def announcement_toggle(request, announcement_id):
    denied = _require_church_admin(request)
    if denied:
        return denied

    announcement = get_object_or_404(
        ChurchAnnouncement,
        pk=announcement_id,
        church_id=request.user.church_id,
    )
    announcement.is_active = not announcement.is_active
    announcement.save(update_fields=['is_active', 'updated_at'])
    if announcement.is_active:
        messages.success(request, 'Announcement is active again.')
    else:
        messages.success(request, 'Announcement deactivated.')
    return redirect('churches:announcement_list')
