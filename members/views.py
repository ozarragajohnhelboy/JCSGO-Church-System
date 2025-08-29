from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin

from .models import (
    Church, Role, CustomUser, NewFriend, RegularMember, 
    Group, ActivityLog
)
from .forms import (
    CustomUserForm, NewFriendForm, RegularMemberForm, 
    GroupForm, ProfileUpdateForm
)


@login_required
def member_list(request):
    """List all members for the user's church"""
    user = request.user
    church = user.church
    
    # Get search parameters
    search = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')
    
    # Base queryset
    members = CustomUser.objects.filter(church=church, is_active=True)
    
    # Apply filters
    if search:
        members = members.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone_number__icontains=search)
        )
    
    if role_filter:
        members = members.filter(role__name=role_filter)
    
    if status_filter == 'new_friends':
        members = members.filter(is_new_friend=True)
    elif status_filter == 'regular_members':
        members = members.filter(is_new_friend=False)
    
    # Order by name
    members = members.order_by('first_name', 'last_name')
    
    # Pagination
    paginator = Paginator(members, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get available roles for filter
    roles = Role.objects.filter(users__church=church).distinct()
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'roles': roles,
        'total_members': members.count(),
        'new_friends_count': members.filter(is_new_friend=True).count(),
        'regular_members_count': members.filter(is_new_friend=False).count(),
    }
    
    return render(request, 'members/member_list.html', context)


@login_required
def member_detail(request, pk):
    """Detailed view of a member"""
    user = request.user
    member = get_object_or_404(CustomUser, pk=pk)
    
    # Check if user can view this member
    if not user.can_access_church_data(member.church):
        messages.error(request, 'You do not have permission to view this member.')
        return redirect('members:member_list')
    
    # Get related data
    new_friend_profile = getattr(member, 'new_friend_profile', None)
    regular_member_profile = getattr(member, 'regular_member_profile', None)
    
    # Get recent activity
    recent_activity = member.activity_logs.order_by('-timestamp')[:10]
    
    # Get group membership
    group_membership = None
    if regular_member_profile and regular_member_profile.group:
        group_membership = regular_member_profile.group
    
    context = {
        'member': member,
        'new_friend_profile': new_friend_profile,
        'regular_member_profile': regular_member_profile,
        'recent_activity': recent_activity,
        'group_membership': group_membership,
        'activity_summary': member.get_activity_summary(),
    }
    
    return render(request, 'members/member_detail.html', context)


@login_required
def new_friends_list(request):
    """List all new friends for the user's church"""
    user = request.user
    church = user.church
    
    # Get search and filter parameters
    search = request.GET.get('search', '')
    follow_up_status = request.GET.get('follow_up_status', '')
    timer_status = request.GET.get('timer_status', '')
    
    # Base queryset
    new_friends = NewFriend.objects.filter(
        user__church=church,
        user__is_active=True,
        is_active=True
    ).select_related('user', 'invited_by')
    
    # Apply filters
    if search:
        new_friends = new_friends.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__email__icontains=search) |
            Q(source__icontains=search)
        )
    
    if follow_up_status:
        new_friends = new_friends.filter(follow_up_status=follow_up_status)
    
    if timer_status:
        new_friends = new_friends.filter(user__timer_status=timer_status)
    
    # Order by registration date (newest first)
    new_friends = new_friends.order_by('-registration_date')
    
    # Pagination
    paginator = Paginator(new_friends, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'follow_up_status': follow_up_status,
        'timer_status': timer_status,
        'total_new_friends': new_friends.count(),
        'pending_follow_up': new_friends.filter(follow_up_status='PENDING').count(),
        'engaged_count': new_friends.filter(follow_up_status='ENGAGED').count(),
    }
    
    return render(request, 'members/new_friends_list.html', context)


@login_required
def regular_members_list(request):
    """List all regular members for the user's church"""
    user = request.user
    church = user.church
    
    # Get search and filter parameters
    search = request.GET.get('search', '')
    role_type = request.GET.get('role_type', '')
    group_filter = request.GET.get('group', '')
    availability = request.GET.get('availability', '')
    
    # Base queryset
    regular_members = RegularMember.objects.filter(
        user__church=church,
        user__is_active=True,
        is_active=True
    ).select_related('user', 'group')
    
    # Apply filters
    if search:
        regular_members = regular_members.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__email__icontains=search) |
            Q(ministry_involvement__icontains=search) |
            Q(skills__icontains=search)
        )
    
    if role_type:
        regular_members = regular_members.filter(role_type=role_type)
    
    if group_filter:
        regular_members = regular_members.filter(group__id=group_filter)
    
    if availability:
        regular_members = regular_members.filter(availability=availability)
    
    # Order by name
    regular_members = regular_members.order_by('user__first_name', 'user__last_name')
    
    # Pagination
    paginator = Paginator(regular_members, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get available groups for filter
    groups = Group.objects.filter(church=church, is_active=True)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'role_type': role_type,
        'group_filter': group_filter,
        'availability': availability,
        'groups': groups,
        'total_regular_members': regular_members.count(),
        'by_role_type': regular_members.values('role_type').annotate(count=Count('id')),
    }
    
    return render(request, 'members/regular_members_list.html', context)


@login_required
def group_list(request):
    """List all groups for the user's church"""
    user = request.user
    church = user.church
    
    # Get search and filter parameters
    search = request.GET.get('search', '')
    group_type = request.GET.get('group_type', '')
    
    # Base queryset
    groups = Group.objects.filter(
        church=church,
        is_active=True
    ).select_related('leader').prefetch_related('members')
    
    # Apply filters
    if search:
        groups = groups.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(leader__first_name__icontains=search) |
            Q(leader__last_name__icontains=search)
        )
    
    if group_type:
        groups = groups.filter(group_type=group_type)
    
    # Order by name
    groups = groups.order_by('name')
    
    # Pagination
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
    
    # Check if user can view this group
    if not user.can_access_church_data(group.church):
        messages.error(request, 'You do not have permission to view this group.')
        return redirect('members:group_list')
    
    # Get group members
    members = group.members.select_related('user').order_by('user__first_name')
    
    # Get recent activity for the group
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


@login_required
def activity_logs(request):
    """View activity logs for the user's church"""
    user = request.user
    church = user.church
    
    # Get filter parameters
    action_filter = request.GET.get('action', '')
    user_filter = request.GET.get('user', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Base queryset
    activities = ActivityLog.objects.filter(
        church=church
    ).select_related('user', 'related_user').order_by('-timestamp')
    
    # Apply filters
    if action_filter:
        activities = activities.filter(action=action_filter)
    
    if user_filter:
        activities = activities.filter(user__id=user_filter)
    
    if date_from:
        activities = activities.filter(timestamp__date__gte=date_from)
    
    if date_to:
        activities = activities.filter(timestamp__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(activities, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get available users for filter
    users = CustomUser.objects.filter(church=church, is_active=True).order_by('first_name')
    
    # Get activity summary
    activity_summary = ActivityLog.get_church_activity_summary(church)
    
    context = {
        'page_obj': page_obj,
        'action_filter': action_filter,
        'user_filter': user_filter,
        'date_from': date_from,
        'date_to': date_to,
        'users': users,
        'activity_summary': activity_summary,
        'total_activities': activities.count(),
    }
    
    return render(request, 'members/activity_logs.html', context)


@login_required
def church_statistics(request):
    """Church statistics and analytics"""
    user = request.user
    church = user.church
    
    # Get member statistics
    member_stats = church.get_member_statistics()
    
    # Get activity summary
    activity_summary = ActivityLog.get_church_activity_summary(church)
    
    # Get group statistics
    groups = Group.objects.filter(church=church, is_active=True)
    group_stats = {
        'total_groups': groups.count(),
        'care_groups': groups.filter(group_type='CARE').count(),
        'ministry_groups': groups.filter(group_type='MINISTRY').count(),
        'total_members_in_groups': sum(group.member_count for group in groups),
        'average_group_size': round(sum(group.member_count for group in groups) / groups.count(), 1) if groups.count() > 0 else 0,
    }
    
    # Get growth trends (last 6 months)
    from datetime import datetime, timedelta
    growth_data = []
    for i in range(6):
        date = datetime.now() - timedelta(days=30*i)
        month_start = date.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        new_members = CustomUser.objects.filter(
            church=church,
            date_joined__gte=month_start,
            date_joined__lte=month_end,
            is_active=True
        ).count()
        
        growth_data.append({
            'month': date.strftime('%B %Y'),
            'new_members': new_members
        })
    
    growth_data.reverse()  # Show oldest first
    
    context = {
        'church': church,
        'member_stats': member_stats,
        'activity_summary': activity_summary,
        'group_stats': group_stats,
        'growth_data': growth_data,
        'monthly_growth': church.growth_rate,
    }
    
    return render(request, 'members/church_statistics.html', context)


# AJAX Views for dynamic functionality
@csrf_exempt
@login_required
def ajax_update_timer_status(request, user_id):
    """AJAX endpoint to update timer status"""
    if request.method == 'POST':
        try:
            user = get_object_or_404(CustomUser, id=user_id)
            
            # Check permissions
            if not request.user.can_access_church_data(user.church):
                return JsonResponse({'error': 'Permission denied'}, status=403)
            
            new_status = int(request.POST.get('timer_status'))
            user.update_timer_status(new_status)
            
            return JsonResponse({
                'success': True,
                'timer_status': user.timer_status,
                'is_new_friend': user.is_new_friend
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
@login_required
def ajax_record_attendance(request, user_id):
    """AJAX endpoint to record attendance"""
    if request.method == 'POST':
        try:
            user = get_object_or_404(CustomUser, id=user_id)
            
            # Check permissions
            if not request.user.can_access_church_data(user.church):
                return JsonResponse({'error': 'Permission denied'}, status=403)
            
            user.record_attendance()
            
            return JsonResponse({
                'success': True,
                'last_attendance': user.last_attendance.isoformat() if user.last_attendance else None
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
@login_required
def ajax_update_follow_up(request, new_friend_id):
    """AJAX endpoint to update follow up status"""
    if request.method == 'POST':
        try:
            new_friend = get_object_or_404(NewFriend, id=new_friend_id)
            
            # Check permissions
            if not request.user.can_access_church_data(new_friend.user.church):
                return JsonResponse({'error': 'Permission denied'}, status=403)
            
            status = request.POST.get('status')
            notes = request.POST.get('notes', '')
            
            new_friend.update_follow_up(status, notes)
            
            return JsonResponse({
                'success': True,
                'follow_up_status': new_friend.follow_up_status,
                'last_follow_up': new_friend.last_follow_up.isoformat() if new_friend.last_follow_up else None
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
@login_required
def ajax_add_to_group(request, user_id, group_id):
    """AJAX endpoint to add user to group"""
    if request.method == 'POST':
        try:
            user = get_object_or_404(CustomUser, id=user_id)
            group = get_object_or_404(Group, id=group_id)
            
            # Check permissions
            if not request.user.can_access_church_data(user.church):
                return JsonResponse({'error': 'Permission denied'}, status=403)
            
            success = group.add_member(user)
            
            if success:
                return JsonResponse({
                    'success': True,
                    'member_count': group.member_count,
                    'capacity_percentage': group.capacity_percentage
                })
            else:
                return JsonResponse({'error': 'Could not add member to group'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
@login_required
def ajax_remove_from_group(request, user_id, group_id):
    """AJAX endpoint to remove user from group"""
    if request.method == 'POST':
        try:
            user = get_object_or_404(CustomUser, id=user_id)
            group = get_object_or_404(Group, id=group_id)
            
            # Check permissions
            if not request.user.can_access_church_data(user.church):
                return JsonResponse({'error': 'Permission denied'}, status=403)
            
            success = group.remove_member(user)
            
            if success:
                return JsonResponse({
                    'success': True,
                    'member_count': group.member_count,
                    'capacity_percentage': group.capacity_percentage
                })
            else:
                return JsonResponse({'error': 'Could not remove member from group'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


# Export functionality
@login_required
def export_members(request):
    """Export members data"""
    user = request.user
    church = user.church
    
    # Check permissions
    if not user.is_staff and not user.role.name in ['ADMIN']:
        messages.error(request, 'You do not have permission to export data.')
        return redirect('members:member_list')
    
    # Get export format
    export_format = request.GET.get('format', 'csv')
    
    # Get filtered data
    members = CustomUser.objects.filter(church=church, is_active=True)
    
    # Create response
    from django.http import HttpResponse
    from import_export import resources
    from import_export.formats import base_formats
    
    resource = resources.CustomUserResource()
    dataset = resource.export(members)
    
    if export_format == 'csv':
        response = HttpResponse(dataset.csv, content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="members_{church.domain}_{timezone.now().strftime("%Y%m%d")}.csv"'
    elif export_format == 'xlsx':
        response = HttpResponse(dataset.xlsx, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="members_{church.domain}_{timezone.now().strftime("%Y%m%d")}.xlsx"'
    else:
        response = HttpResponse(dataset.json, content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="members_{church.domain}_{timezone.now().strftime("%Y%m%d")}.json"'
    
    return response
