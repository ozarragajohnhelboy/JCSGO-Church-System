from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from ..models import Group, ActivityLog


@login_required
def group_list(request):
    """List all groups for the user's church"""
    user = request.user
    church = user.church
    
    search = request.GET.get('search', '')
    group_type = request.GET.get('group_type', '')
    
    groups = Group.objects.filter(
        church=church,
        is_active=True
    ).select_related('leader').prefetch_related('members')
    
    if search:
        groups = groups.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(leader__first_name__icontains=search) |
            Q(leader__last_name__icontains=search)
        )
    
    if group_type:
        groups = groups.filter(group_type=group_type)
    
    groups = groups.order_by('name')
    
    paginator = Paginator(groups, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'group_type': group_type,
        'total_groups': groups.count(),
        'care_groups_count': groups.filter(group_type='CARE').count(),
        'ministry_groups_count': groups.filter(group_type='MINISTRY').count(),
    }
    
    return render(request, 'members/group_list.html', context)


@login_required
def group_detail(request, pk):
    """Detailed view of a group"""
    user = request.user
    group = get_object_or_404(Group, pk=pk)
    
    if not user.can_access_church_data(group.church):
        messages.error(request, 'You do not have permission to view this group.')
        return redirect('members:group_list')
    
    members = group.members.select_related('user').order_by('user__first_name')
    
    recent_activity = ActivityLog.objects.filter(
        user__regular_member_profile__group=group
    ).select_related('user').order_by('-timestamp')[:10]
    
    context = {
        'group': group,
        'members': members,
        'recent_activity': recent_activity,
        'capacity_percentage': group.capacity_percentage,
        'is_full': group.is_full,
    }
    
    return render(request, 'members/group_detail.html', context)
