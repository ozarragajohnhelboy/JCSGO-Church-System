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
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.exceptions import PermissionDenied
import json
import csv
import io
from datetime import datetime, timedelta

from .models import (
    CustomUser, NewFriend, RegularMember, Group, Role, 
    ActivityLog, Attendance
)
from .forms import (
    CustomUserForm, NewFriendForm, RegularMemberForm, 
    GroupForm, ProfileUpdateForm, NewFriendImportForm, RegularMemberImportForm,
    CareGroupForm, CareGroupMemberForm, UserProfileForm, QRCodeScanForm,
    ManualAttendanceForm, AttendanceFilterForm, AttendanceExportForm, ProfileExportForm, ProfileImportForm
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
    paginator = Paginator(members, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get available roles for filter (exclude system roles)
    roles = Role.objects.filter(
        name__in=['VSL', 'CSL', 'CL', 'CM']
    ).order_by('name')
    
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
    
    # Determine the appropriate back URL based on user role and referrer
    back_url = 'members:member_list'  # Default fallback
    
    # Check if user came from role-specific new friends list
    if user.role.name in ['VSL', 'CSL', 'CL'] and member.is_new_friend:
        # Check if this new friend is endorsed to the current user
        try:
            new_friend_profile = member.new_friend_profile
            if new_friend_profile.endorsed_to == user:
                back_url = 'members:role_new_friends_list'
        except NewFriend.DoesNotExist:
            pass
    
    # Get related data based on user type
    new_friend_profile = None
    regular_member_profile = None
    
    if member.is_new_friend:
        # User is a new friend, only get NewFriend profile
        try:
            new_friend_profile = member.new_friend_profile
        except NewFriend.DoesNotExist:
            pass
    else:
        # User is a regular member, only get RegularMember profile
        try:
            regular_member_profile = member.regular_member_profile
        except RegularMember.DoesNotExist:
            pass
    
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
        'back_url': back_url,
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
    
    # Base queryset - Get all new friends from CustomUser model
    new_friends_users = CustomUser.objects.filter(
        church=church,
        is_active=True,
        is_new_friend=True  # This is the key filter
    )
    
    # Apply search filters
    if search:
        new_friends_users = new_friends_users.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search) |
            Q(new_friend_profile__invited_by__first_name__icontains=search) |
            Q(new_friend_profile__invited_by__last_name__icontains=search)
        )
    
    if timer_status:
        new_friends_users = new_friends_users.filter(timer_status=timer_status)
    
    # Get NewFriend profiles for these users (if they exist)
    new_friends = []
    for user_obj in new_friends_users:
        try:
            new_friend_profile = NewFriend.objects.get(user=user_obj)
            # Add follow-up status filter if specified
            if follow_up_status and new_friend_profile.follow_up_status != follow_up_status:
                continue
            new_friends.append(new_friend_profile)
        except NewFriend.DoesNotExist:
            # Create a default NewFriend profile if it doesn't exist
            new_friend_profile = NewFriend.objects.create(
                user=user_obj,
                invited_by=None,
                notes='',
                is_active=True
            )
            new_friends.append(new_friend_profile)
    
    # Apply follow-up status filter to the list
    if follow_up_status:
        new_friends = [nf for nf in new_friends if nf.follow_up_status == follow_up_status]
    
    # Order by registration date (newest first)
    new_friends.sort(key=lambda x: x.registration_date, reverse=True)
    
    # Pagination
    paginator = Paginator(new_friends, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'follow_up_status': follow_up_status,
        'timer_status': timer_status,
        'total_new_friends': len(new_friends),
        'pending_follow_up': len([nf for nf in new_friends if nf.follow_up_status == 'PENDING']),
        'engaged_count': len([nf for nf in new_friends if nf.follow_up_status == 'ENGAGED']),
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
    
    # Base queryset - Get all regular members from CustomUser model
    regular_members_users = CustomUser.objects.filter(
        church=church,
        is_active=True,
        is_new_friend=False  # This is the key filter
    )
    
    # Apply search filters
    if search:
        regular_members_users = regular_members_users.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )
    
    if role_type:
        regular_members_users = regular_members_users.filter(role__name=role_type)
    
    # Get RegularMember profiles for these users (if they exist)
    regular_members = []
    for user_obj in regular_members_users:
        try:
            regular_member_profile = RegularMember.objects.get(user=user_obj)
            # Add group filter if specified
            if group_filter and str(regular_member_profile.group.id) != group_filter:
                continue
            # Add availability filter if specified
            if availability and regular_member_profile.availability != availability:
                continue
            regular_members.append(regular_member_profile)
        except RegularMember.DoesNotExist:
            # Create a default RegularMember profile if it doesn't exist
            regular_member_profile = RegularMember.objects.create(
                user=user_obj,
                role_type=user_obj.role.name if user_obj.role else 'CM',
                is_active=True
            )
            regular_members.append(regular_member_profile)
    
    # Order by name
    regular_members.sort(key=lambda x: (x.user.first_name, x.user.last_name))
    
    # Pagination
    paginator = Paginator(regular_members, 10)
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
        'total_regular_members': len(regular_members),
        'by_role_type': {},
    }
    
    # Calculate role type counts
    for rm in regular_members:
        role = rm.role_type
        if role not in context['by_role_type']:
            context['by_role_type'][role] = {'count': 0, 'name': role}
        context['by_role_type'][role]['count'] += 1
    
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
    paginator = Paginator(activities, 10)
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
def ajax_get_available_members(request, group_id):
    """AJAX endpoint to get available members for a care group"""
    if request.method == 'GET':
        try:
            care_group = get_object_or_404(Group, pk=group_id, group_type='CARE')
            
            # Check if user can manage this care group
            if care_group.leader != request.user:
                return JsonResponse({'error': 'Permission denied'}, status=403)
            
            # Get available members
            available_members = CustomUser.objects.filter(
                church=care_group.church,
                is_active=True,
                is_new_friend=False,
                role__name__in=['VSL', 'CSL', 'CL', 'CM']
            ).exclude(
                regular_member_profile__group__isnull=False
            ).order_by('first_name', 'last_name')
            
            members_data = []
            for member in available_members:
                members_data.append({
                    'id': member.pk,
                    'full_name': member.full_name,
                    'role': member.get_role_display(),
                    'email': member.email
                })
            
            return JsonResponse({
                'success': True,
                'members': members_data
            })
            
        except Group.DoesNotExist:
            return JsonResponse({'error': 'Care group not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


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
    if not user.is_staff and not user.role.name in ['SUPER_ADMIN', 'ADMIN']:
        messages.error(request, 'You do not have permission to export data.')
        return redirect('members:member_list')
    
    # Get export format
    export_format = request.GET.get('format', 'csv')
    
    # Get status filter
    status = request.GET.get('status', '')
    
    # Get filtered data based on status
    if status == 'new_friends':
        members = CustomUser.objects.filter(church=church, is_active=True, is_new_friend=True)
        filename_prefix = "new_friends"
    elif status == 'regular_members':
        members = CustomUser.objects.filter(church=church, is_active=True, is_new_friend=False)
        filename_prefix = "regular_members"
    else:
        # Default: export all members
        members = CustomUser.objects.filter(church=church, is_active=True)
        filename_prefix = "members"
    
    # Create response
    from django.http import HttpResponse
    from import_export.formats import base_formats
    from .admin import CustomUserResource
    
    resource = CustomUserResource()
    dataset = resource.export(members)
    
    if export_format == 'csv':
        response = HttpResponse(dataset.csv, content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename_prefix}_{church.domain}_{timezone.now().strftime("%Y%m%d")}.csv"'
    elif export_format == 'xlsx':
        response = HttpResponse(dataset.xlsx, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{filename_prefix}_{church.domain}_{timezone.now().strftime("%Y%m%d")}.xlsx"'
    else:
        response = HttpResponse(dataset.json, content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{filename_prefix}_{church.domain}_{timezone.now().strftime("%Y%m%d")}.json"'
    
    return response


@login_required
def role_management(request):
    """Role management view for admins only"""
    user = request.user
    
    # Check if user has permission to access role management
    if not (user.is_superuser or user.role.name == 'ADMIN'):
        messages.error(request, 'You do not have permission to access role management.')
        return redirect('churches:dashboard')
    
    church = user.church
    
    # Get search parameters
    search = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    
    # Base queryset - get all users in the church
    users = CustomUser.objects.filter(church=church, is_active=True)
    
    # Apply filters
    if search:
        users = users.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )
    
    if role_filter:
        users = users.filter(role__name=role_filter)
    
    # Order by role priority, then by name
    users = users.order_by('role__name', 'first_name', 'last_name')
    
    # Pagination
    paginator = Paginator(users, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get available roles for filter
    roles = Role.objects.filter(
        name__in=['VSL', 'CSL', 'CL', 'CM', 'NEW_FRIEND']
    ).order_by('name')
    
    # Get role statistics
    role_stats = {}
    for role in roles:
        count = users.filter(role=role).count()
        if count > 0:
            role_stats[role.name] = {
                'name': role.get_name_display(),
                'count': count,
                'percentage': round((count / users.count() * 100) if users.count() > 0 else 0, 1)
            }
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'role_filter': role_filter,
        'roles': roles,
        'role_stats': role_stats,
        'total_users': users.count(),
    }
    
    return render(request, 'members/role_management.html', context)


@login_required
def ajax_update_user_role(request, user_id):
    """AJAX endpoint to update user role"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
    user = request.user
    
    # Check if user has permission
    if not (user.is_superuser or user.role.name == 'ADMIN'):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        target_user = get_object_or_404(CustomUser, pk=user_id, church=user.church)
        new_role_name = request.POST.get('role')
        
        if not new_role_name:
            return JsonResponse({'error': 'Role is required'}, status=400)
        
        # Get the new role
        new_role = get_object_or_404(Role, name=new_role_name)
        
        # Update user role
        old_role = target_user.role
        target_user.role = new_role
        target_user.save()
        
        # Log the role change
        ActivityLog.objects.create(
            user=user,
            action='ROLE_CHANGE',
            description=f'Changed role from {old_role.get_name_display() if old_role else "None"} to {new_role.get_name_display()} for {target_user.full_name}',
            related_user=target_user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # If transitioning from new friend to regular member
        if target_user.is_new_friend and new_role_name not in ['NEW_FRIEND']:
            target_user.is_new_friend = False
            target_user.transition_date = timezone.now()
            target_user.save()
            
            # Create RegularMember profile
            RegularMember.objects.get_or_create(
                user=target_user,
                defaults={'role_type': new_role_name}
            )
            
            # Log the transition
            ActivityLog.objects.create(
                user=user,
                action='STATUS_CHANGE',
                description=f'Transitioned {target_user.full_name} from New Friend to Regular Member',
                related_user=target_user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        
        return JsonResponse({
            'success': True,
            'message': f'Role updated successfully to {new_role.get_name_display()}',
            'new_role': new_role.get_name_display(),
            'is_new_friend': target_user.is_new_friend
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def ajax_get_user_details(request, user_id):
    """AJAX endpoint to get user details for role management"""
    user = request.user
    
    # Check if user has permission
    if not (user.is_superuser or user.role.name == 'ADMIN'):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        target_user = get_object_or_404(CustomUser, pk=user_id, church=user.church)
        
        # Get user's current group if any
        group_info = None
        if not target_user.is_new_friend:
            try:
                regular_profile = RegularMember.objects.get(user=target_user)
                if regular_profile.group:
                    group_info = {
                        'id': regular_profile.group.id,
                        'name': regular_profile.group.name,
                        'type': regular_profile.group.get_group_type_display()
                    }
            except RegularMember.DoesNotExist:
                pass
        
        # Get recent activity
        recent_activity = target_user.activity_logs.order_by('-timestamp')[:5]
        activity_list = []
        for activity in recent_activity:
            activity_list.append({
                'action': activity.get_action_display(),
                'description': activity.description,
                'timestamp': activity.timestamp.strftime('%Y-%m-%d %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'user': {
                'id': target_user.id,
                'full_name': target_user.full_name,
                'email': target_user.email,
                'phone_number': target_user.phone_number or 'Not provided',
                'current_role': target_user.role.get_name_display() if target_user.role else 'No role assigned',
                'is_new_friend': target_user.is_new_friend,
                'timer_status': target_user.timer_status if target_user.is_new_friend else None,
                'date_joined': target_user.date_joined.strftime('%Y-%m-%d'),
                'last_attendance': target_user.last_attendance.strftime('%Y-%m-%d %H:%M') if target_user.last_attendance else 'Never',
                'group': group_info,
                'recent_activity': activity_list
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def ajax_bulk_role_update(request):
    """AJAX endpoint for bulk role updates"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
    user = request.user
    
    # Check if user has permission
    if not (user.is_superuser or user.role.name == 'ADMIN'):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        user_ids = request.POST.getlist('user_ids[]')
        new_role_name = request.POST.get('role')
        
        if not user_ids or not new_role_name:
            return JsonResponse({'error': 'User IDs and role are required'}, status=400)
        
        # Get the new role
        new_role = get_object_or_404(Role, name=new_role_name)
        
        # Update users
        updated_count = 0
        for user_id in user_ids:
            try:
                target_user = CustomUser.objects.get(pk=user_id, church=user.church)
                old_role = target_user.role
                target_user.role = new_role
                target_user.save()
                
                # Log the role change
                ActivityLog.objects.create(
                    user=user,
                    action='ROLE_CHANGE',
                    description=f'Bulk update: Changed role from {old_role.get_name_display() if old_role else "None"} to {new_role.get_name_display()} for {target_user.full_name}',
                    related_user=target_user,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                updated_count += 1
                
            except CustomUser.DoesNotExist:
                continue
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully updated {updated_count} users to {new_role.get_name_display()}',
            'updated_count': updated_count
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def new_friend_add(request):
    """Add a new New Friend"""
    # Check if user has permission (admin only)
    if not (request.user.is_superuser or request.user.role.name == 'ADMIN'):
        messages.error(request, 'You do not have permission to add new friends.')
        return redirect('members:new_friends_list')
    
    if request.method == 'POST':
        form = NewFriendForm(request.POST, church=request.user.church)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create the user first with church-specific default password
                    default_password = f"jcsgo{request.user.church.domain}"
                    user = CustomUser.objects.create_user(
                        email=form.full_email,
                        first_name=form.cleaned_data['first_name'],
                        last_name=form.cleaned_data['last_name'],
                        phone_number=form.cleaned_data['phone'],
                        church=request.user.church,
                        is_new_friend=True,
                        is_active=True,
                        password=default_password  # Church-specific default password
                    )
                    
                    # Remove any existing RegularMember profile if it exists
                    try:
                        if hasattr(user, 'regular_member_profile'):
                            user.regular_member_profile.delete()
                    except RegularMember.DoesNotExist:
                        pass
                    
                    # Set timer status on the user
                    user.timer_status = form.cleaned_data['timer_status']
                    user.save()
                    
                    # Create the NewFriend profile
                    new_friend = NewFriend.objects.create(
                        user=user,
                        invited_by=form.cleaned_data['invited_by'],
                        endorsed_to=form.cleaned_data['endorsed_to'],
                        notes=form.cleaned_data['notes']
                    )
                    
                    # Log the activity
                    ActivityLog.objects.create(
                        user=request.user,
                        action='NEW_FRIEND_ADDED',
                        description=f'Added new friend: {user.full_name}',
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                    
                    messages.success(request, f'New friend "{user.full_name}" has been added successfully!')
                    return redirect('members:new_friends_list')
                    
            except Exception as e:
                messages.error(request, f'Error adding new friend: {str(e)}')
    else:
        form = NewFriendForm(church=request.user.church)
    
    context = {
        'form': form,
        'title': 'Add New Friend',
        'church': request.user.church
    }
    return render(request, 'members/new_friend_form.html', context)

@login_required
def new_friend_edit(request, new_friend_id):
    """Edit a New Friend"""
    # Check if user has permission (admin only)
    if not (request.user.is_superuser or request.user.role.name == 'ADMIN'):
        messages.error(request, 'You do not have permission to edit new friends.')
        return redirect('members:new_friends_list')
    
    new_friend = get_object_or_404(NewFriend, id=new_friend_id, user__church=request.user.church)
    
    if request.method == 'POST':
        form = NewFriendForm(request.POST, instance=new_friend, church=request.user.church)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Update user details
                    user = new_friend.user
                    user.first_name = form.cleaned_data['first_name']
                    user.last_name = form.cleaned_data['last_name']
                    user.phone_number = form.cleaned_data['phone']
                    user.timer_status = form.cleaned_data['timer_status']
                    user.save()
                    
                    # Update NewFriend profile
                    new_friend.invited_by = form.cleaned_data['invited_by']
                    new_friend.endorsed_to = form.cleaned_data['endorsed_to']
                    new_friend.notes = form.cleaned_data['notes']
                    new_friend.save()
                    
                    # Handle conversion to regular member if selected
                    if form.cleaned_data.get('convert_to_regular') and form.cleaned_data.get('regular_role'):
                        selected_role_name = form.cleaned_data['regular_role']
                        # Set user as regular
                        user.is_new_friend = False
                        user.transition_date = timezone.now()
                        # Assign Role on user
                        role = get_object_or_404(Role, name=selected_role_name)
                        user.role = role
                        user.save()
                        
                        # Create RegularMember profile
                        RegularMember.objects.get_or_create(
                            user=user,
                            defaults={'role_type': selected_role_name}
                        )
                        
                        # Remove NewFriend profile
                        try:
                            if hasattr(user, 'new_friend_profile'):
                                user.new_friend_profile.delete()
                        except NewFriend.DoesNotExist:
                            pass
                        
                        # Log the transition
                        ActivityLog.objects.create(
                            user=request.user,
                            action='STATUS_CHANGE',
                            description=f'Transitioned {user.full_name} from New Friend to Regular Member',
                            related_user=user,
                            ip_address=request.META.get('REMOTE_ADDR'),
                            user_agent=request.META.get('HTTP_USER_AGENT', '')
                        )
                    
                    # Log the update
                    ActivityLog.objects.create(
                        user=request.user,
                        action='NEW_FRIEND_UPDATED',
                        description=f'Updated new friend: {user.full_name}',
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                    
                    messages.success(request, f'New friend "{user.full_name}" has been updated successfully!')
                    return redirect('members:new_friends_list')
                    
            except Exception as e:
                messages.error(request, f'Error updating new friend: {str(e)}')
    else:
        # Pre-populate form with current data
        form = NewFriendForm(instance=new_friend, church=request.user.church)
        # Extract email prefix from the full email
        email_prefix = new_friend.user.email.split('@')[0] if '@' in new_friend.user.email else new_friend.user.email
        form.fields['email_prefix'].initial = email_prefix
        form.fields['first_name'].initial = new_friend.user.first_name
        form.fields['last_name'].initial = new_friend.user.last_name
        form.fields['phone'].initial = new_friend.user.phone_number
        form.fields['invited_by'].initial = new_friend.invited_by
        form.fields['endorsed_to'].initial = new_friend.endorsed_to
        form.fields['timer_status'].initial = new_friend.user.timer_status
    
    context = {
        'form': form,
        'new_friend': new_friend,
        'title': 'Edit New Friend',
        'church': request.user.church
    }
    return render(request, 'members/new_friend_form.html', context)

@login_required
@require_POST
def new_friend_delete(request, new_friend_id):
    """Delete a New Friend"""
    # Check if user has permission (admin only)
    if not (request.user.is_superuser or request.user.role.name == 'ADMIN'):
        messages.error(request, 'You do not have permission to delete new friends.')
        return redirect('members:new_friends_list')
    
    new_friend = get_object_or_404(NewFriend, id=new_friend_id, user__church=request.user.church)
    user_name = new_friend.user.full_name
    
    try:
        with transaction.atomic():
            # Log the activity before deletion
            ActivityLog.objects.create(
                user=request.user,
                action='NEW_FRIEND_DELETED',
                description=f'Deleted new friend: {user_name}',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Delete the user (this will cascade to NewFriend)
            new_friend.user.delete()
            
            messages.success(request, f'New friend "{user_name}" has been deleted successfully!')
            
    except Exception as e:
        messages.error(request, f'Error deleting new friend: {str(e)}')
    
    return redirect('members:new_friends_list')

@login_required
def new_friend_import(request):
    """Import New Friends from CSV/Excel"""
    # Check if user has permission (admin only)
    if not (request.user.is_superuser or request.user.role.name == 'ADMIN'):
        messages.error(request, 'You do not have permission to import new friends.')
        return redirect('members:new_friends_list')
    
    if request.method == 'POST':
        form = NewFriendImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                file = request.FILES['file']
                imported_count = 0
                errors = []
                
                if file.name.endswith('.csv'):
                    # Handle CSV import
                    decoded_file = file.read().decode('utf-8')
                    csv_data = csv.DictReader(io.StringIO(decoded_file))
                    
                    for row_num, row in enumerate(csv_data, start=2):  # Start from 2 to account for header
                        try:
                            with transaction.atomic():
                                # Create user with email_prefix and default password
                                email_prefix = row.get('email_prefix', '').strip()
                                if not email_prefix:
                                    # If no email_prefix, try to extract from email field
                                    email = row.get('email', '').strip()
                                    if '@' in email:
                                        email_prefix = email.split('@')[0]
                                    else:
                                        email_prefix = email
                                
                                full_email = f"{email_prefix}@{request.user.church.domain}.jcsgo.com"
                                
                                # Create user with church-specific default password
                                default_password = f"jcsgo{request.user.church.domain}"
                                user = CustomUser.objects.create_user(
                                    email=full_email,
                                    first_name=row.get('first_name', '').strip(),
                                    last_name=row.get('last_name', '').strip(),
                                    phone_number=row.get('phone', '').strip() or None,
                                    church=request.user.church,
                                    is_new_friend=True,
                                    is_active=True,
                                    password=default_password  # Church-specific default password
                                )
                                
                                # Remove any existing RegularMember profile if it exists
                                try:
                                    if hasattr(user, 'regular_member_profile'):
                                        user.regular_member_profile.delete()
                                except RegularMember.DoesNotExist:
                                    pass
                                
                                # Set timer status on the user
                                user.timer_status = int(row.get('timer_status', 1))
                                user.save()
                                
                                # Create NewFriend profile
                                NewFriend.objects.create(
                                    user=user,
                                    invited_by=None,  # CSV import doesn't have invited_by info
                                    endorsed_to=None,  # CSV import doesn't have endorsed_to info
                                    notes=row.get('notes', '').strip() or ''
                                )
                                
                                imported_count += 1
                                
                        except Exception as e:
                            errors.append(f"Row {row_num}: {str(e)}")
                
                if imported_count > 0:
                    messages.success(request, f'Successfully imported {imported_count} new friends!')
                    
                    # Log the activity
                    ActivityLog.objects.create(
                        user=request.user,
                        action='NEW_FRIENDS_IMPORTED',
                        description=f'Imported {imported_count} new friends from {file.name}',
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                
                if errors:
                    for error in errors[:5]:  # Show first 5 errors
                        messages.warning(request, error)
                    if len(errors) > 5:
                        messages.warning(request, f'... and {len(errors) - 5} more errors.')
                
                return redirect('members:new_friends_list')
                
            except Exception as e:
                messages.error(request, f'Error importing file: {str(e)}')
    else:
        form = NewFriendImportForm()
    
    context = {
        'form': form,
        'title': 'Import New Friends',
        'church': request.user.church
    }
    return render(request, 'members/new_friend_import.html', context)

@login_required
def regular_member_add(request):
    """Add a new Regular Member"""
    # Check if user has permission (admin only)
    if not (request.user.is_superuser or request.user.role.name == 'ADMIN'):
        messages.error(request, 'You do not have permission to add regular members.')
        return redirect('members:regular_members_list')
    
    if request.method == 'POST':
        form = RegularMemberForm(request.POST, church=request.user.church)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create the user first with church-specific default password
                    default_password = f"jcsgo{request.user.church.domain}"
                    user = CustomUser.objects.create_user(
                        email=form.full_email,
                        first_name=form.cleaned_data['first_name'],
                        last_name=form.cleaned_data['last_name'],
                        phone_number=form.cleaned_data['phone'],
                        church=request.user.church,
                        is_new_friend=False,
                        is_active=True,
                        password=default_password  # Church-specific default password
                    )
                    
                    # Assign role
                    user.role = form.cleaned_data['role']
                    user.save()
                    
                    # Remove any existing NewFriend profile if it exists
                    try:
                        if hasattr(user, 'new_friend_profile'):
                            user.new_friend_profile.delete()
                    except NewFriend.DoesNotExist:
                        pass
                    
                    # Create the RegularMember profile
                    regular_member = RegularMember.objects.create(
                        user=user,
                        role_type=form.cleaned_data['role'],
                        group=form.cleaned_data['group']
                    )
                    
                    # Log the activity
                    ActivityLog.objects.create(
                        user=request.user,
                        action='REGULAR_MEMBER_ADDED',
                        description=f'Added regular member: {user.full_name}',
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                    
                    messages.success(request, f'Regular member "{user.full_name}" has been added successfully!')
                    return redirect('members:regular_members_list')
                    
            except Exception as e:
                messages.error(request, f'Error adding regular member: {str(e)}')
    else:
        form = RegularMemberForm(church=request.user.church)
    
    context = {
        'form': form,
        'title': 'Add Regular Member',
        'church': request.user.church
    }
    return render(request, 'members/regular_member_form.html', context)

@login_required
def regular_member_edit(request, regular_member_id):
    """Edit a Regular Member"""
    # Check if user has permission (admin only)
    if not (request.user.is_superuser or request.user.role.name == 'ADMIN'):
        messages.error(request, 'You do not have permission to edit regular members.')
        return redirect('members:regular_members_list')
    
    regular_member = get_object_or_404(RegularMember, id=regular_member_id, user__church=request.user.church)
    
    if request.method == 'POST':
        form = RegularMemberForm(request.POST, instance=regular_member, church=request.user.church)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Update user details
                    user = regular_member.user
                    user.first_name = form.cleaned_data['first_name']
                    user.last_name = form.cleaned_data['last_name']
                    user.phone_number = form.cleaned_data['phone']
                    user.role = form.cleaned_data['role']
                    user.save()
                    
                    # Update RegularMember profile
                    regular_member.role_type = form.cleaned_data['role']
                    regular_member.group = form.cleaned_data['group']
                    regular_member.save()
                    
                    # Log the activity
                    ActivityLog.objects.create(
                        user=request.user,
                        action='REGULAR_MEMBER_UPDATED',
                        description=f'Updated regular member: {user.full_name}',
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                    
                    messages.success(request, f'Regular member "{user.full_name}" has been updated successfully!')
                    return redirect('members:regular_members_list')
                    
            except Exception as e:
                messages.error(request, f'Error updating regular member: {str(e)}')
    else:
        # Pre-populate form with current data
        form = RegularMemberForm(instance=regular_member, church=request.user.church)
        # Extract email prefix from the full email
        email_prefix = regular_member.user.email.split('@')[0] if '@' in regular_member.user.email else regular_member.user.email
        form.fields['email_prefix'].initial = email_prefix
        form.fields['first_name'].initial = regular_member.user.first_name
        form.fields['last_name'].initial = regular_member.user.last_name
        form.fields['phone'].initial = regular_member.user.phone_number
        form.fields['role'].initial = regular_member.user.role
    
    context = {
        'form': form,
        'regular_member': regular_member,
        'title': 'Edit Regular Member',
        'church': request.user.church
    }
    return render(request, 'members/regular_member_form.html', context)

@login_required
@require_POST
def regular_member_delete(request, regular_member_id):
    """Delete a Regular Member"""
    # Check if user has permission (admin only)
    if not (request.user.is_superuser or request.user.role.name == 'ADMIN'):
        messages.error(request, 'You do not have permission to delete regular members.')
        return redirect('members:regular_members_list')
    
    regular_member = get_object_or_404(RegularMember, id=regular_member_id, user__church=request.user.church)
    user_name = regular_member.user.full_name
    
    try:
        with transaction.atomic():
            # Log the activity before deletion
            ActivityLog.objects.create(
                user=request.user,
                action='REGULAR_MEMBER_DELETED',
                description=f'Deleted regular member: {user_name}',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Delete the user (this will cascade to RegularMember)
            regular_member.user.delete()
            
            messages.success(request, f'Regular member "{user_name}" has been deleted successfully!')
            
    except Exception as e:
        messages.error(request, f'Error deleting regular member: {str(e)}')
    
    return redirect('members:regular_members_list')

@login_required
def regular_member_import(request):
    """Import Regular Members from CSV/Excel"""
    # Check if user has permission (admin only)
    if not (request.user.is_superuser or request.user.role.name == 'ADMIN'):
        messages.error(request, 'You do not have permission to import regular members.')
        return redirect('members:regular_members_list')
    
    if request.method == 'POST':
        form = RegularMemberImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                file = request.FILES['file']
                imported_count = 0
                errors = []
                
                if file.name.endswith('.csv'):
                    # Handle CSV import
                    decoded_file = file.read().decode('utf-8')
                    csv_data = csv.DictReader(io.StringIO(decoded_file))
                    
                    for row_num, row in enumerate(csv_data, start=2):  # Start from 2 to account for header
                        try:
                            with transaction.atomic():
                                # Get or create role
                                role_name = row.get('role', 'CM').strip().upper()
                                role, created = Role.objects.get_or_create(name=role_name)
                                
                                # Get group if specified
                                group = None
                                if row.get('group'):
                                    group_name = row.get('group', '').strip()
                                    group, created = Group.objects.get_or_create(
                                        name=group_name,
                                        church=request.user.church,
                                        defaults={'is_active': True}
                                    )
                                
                                # Create user with email_prefix and default password
                                email_prefix = row.get('email_prefix', '').strip()
                                if not email_prefix:
                                    # If no email_prefix, try to extract from email field
                                    email = row.get('email', '').strip()
                                    if '@' in email:
                                        email_prefix = email.split('@')[0]
                                    else:
                                        email_prefix = email
                                
                                full_email = f"{email_prefix}@{request.user.church.domain}.jcsgo.com"
                                
                                # Create user with church-specific default password
                                default_password = f"jcsgo{request.user.church.domain}"
                                user = CustomUser.objects.create_user(
                                    email=full_email,
                                    first_name=row.get('first_name', '').strip(),
                                    last_name=row.get('last_name', '').strip(),
                                    phone_number=row.get('phone', '').strip() or None,
                                    church=request.user.church,
                                    role=role,
                                    is_new_friend=False,
                                    is_active=True,
                                    password=default_password  # Church-specific default password
                                )
                                
                                # Remove any existing NewFriend profile if it exists
                                try:
                                    if hasattr(user, 'new_friend_profile'):
                                        user.new_friend_profile.delete()
                                except NewFriend.DoesNotExist:
                                    pass
                                
                                # Create RegularMember profile
                                RegularMember.objects.create(
                                    user=user,
                                    role_type=role,
                                    group=group
                                )
                                
                                imported_count += 1
                                
                        except Exception as e:
                            errors.append(f"Row {row_num}: {str(e)}")
                
                if imported_count > 0:
                    messages.success(request, f'Successfully imported {imported_count} regular members!')
                    
                    # Log the activity
                    ActivityLog.objects.create(
                        user=request.user,
                        action='REGULAR_MEMBERS_IMPORTED',
                        description=f'Imported {imported_count} regular members from {file.name}',
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                
                if errors:
                    for error in errors[:5]:  # Show first 5 errors
                        messages.warning(request, error)
                    if len(errors) > 5:
                        messages.warning(request, f'... and {len(errors) - 5} more errors.')
                
                return redirect('members:regular_members_list')
                
            except Exception as e:
                messages.error(request, f'Error importing file: {str(e)}')
    else:
        form = RegularMemberImportForm()
    
    context = {
        'form': form,
        'title': 'Import Regular Members',
        'church': request.user.church
    }
    return render(request, 'members/regular_member_import.html', context)


# Care Group Views for VSL, CSL, CL roles
@login_required
def care_group_list(request):
    """List care groups for leadership roles (VSL, CSL, CL) and admin"""
    user = request.user
    
    # Check if user has permission to access care groups
    if user.role.name not in ['VSL', 'CSL', 'CL', 'ADMIN']:
        messages.error(request, 'You do not have permission to access care groups.')
        return redirect('churches:dashboard')
    
    church = user.church
    
    # Get search and filter parameters
    search = request.GET.get('search', '')
    
    # Base queryset - only care groups
    care_groups = Group.objects.filter(
        church=church,
        group_type='CARE',
        is_active=True
    ).select_related('leader').prefetch_related('members')
    
    # For VSL and ADMIN, show all care groups in their church
    # For CSL and CL, show only groups they lead or are members of
    if user.role.name in ['CSL', 'CL']:
        care_groups = care_groups.filter(
            Q(leader=user) | Q(members__user=user)
        ).distinct()
    
    # Apply search filter
    if search:
        care_groups = care_groups.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(leader__first_name__icontains=search) |
            Q(leader__last_name__icontains=search)
        )
    
    # Order by name
    care_groups = care_groups.order_by('name')
    
    # Pagination
    paginator = Paginator(care_groups, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get groups led by current user
    led_groups = Group.objects.filter(
        church=church,
        group_type='CARE',
        leader=user,
        is_active=True
    )
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'total_care_groups': care_groups.count(),
        'led_groups_count': led_groups.count(),
        'can_create_group': user.role.name in ['VSL', 'CSL', 'CL', 'ADMIN'],
        'user_role': user.role.name,
    }
    
    return render(request, 'members/care_group_list.html', context)


@login_required
def care_group_create(request):
    """Create a new care group - for VSL, CSL, CL roles and admin"""
    user = request.user
    
    # Check if user has permission to create care groups
    if user.role.name not in ['VSL', 'CSL', 'CL', 'ADMIN']:
        messages.error(request, 'You do not have permission to create care groups.')
        return redirect('members:care_group_list')
    
    if request.method == 'POST':
        form = CareGroupForm(request.POST, church=user.church, user=user)
        if form.is_valid():
            care_group = form.save()
            
            # Log the activity
            ActivityLog.objects.create(
                user=user,
                church=user.church,
                action='GROUP_CREATED',
                description=f'Created care group: {care_group.name}'
            )
            
            messages.success(request, f'Care group "{care_group.name}" created successfully!')
            return redirect('members:care_group_detail', group_id=care_group.pk)
    else:
        form = CareGroupForm(church=user.church, user=user)
    
    context = {
        'form': form,
        'user_role': user.role.name,
    }
    
    return render(request, 'members/care_group_create.html', context)


@login_required
def care_group_detail(request, group_id):
    """Detailed view of a care group"""
    user = request.user
    care_group = get_object_or_404(Group, pk=group_id, group_type='CARE')
    
    # Check if user can view this care group
    if not user.can_access_church_data(care_group.church):
        messages.error(request, 'You do not have permission to view this care group.')
        return redirect('members:care_group_list')
    
    # Additional permission check for CSL and CL (admin can view all groups)
    if user.role.name in ['CSL', 'CL'] and care_group.leader != user:
        # Check if user is a member of this group
        try:
            user_member_profile = RegularMember.objects.get(user=user)
            if user_member_profile.group != care_group:
                messages.error(request, 'You can only view care groups you lead or are a member of.')
                return redirect('members:care_group_list')
        except RegularMember.DoesNotExist:
            messages.error(request, 'You can only view care groups you lead or are a member of.')
            return redirect('members:care_group_list')
    
    # Get care group members
    members = care_group.members.select_related('user').order_by('user__first_name')
    
    # Get recent activity for the care group
    recent_activity = ActivityLog.objects.filter(
        user__regular_member_profile__group=care_group
    ).select_related('user').order_by('-timestamp')[:10]
    
    # Get available members to add (if user is the leader or admin)
    available_members = None
    if care_group.leader == user or user.role.name == 'ADMIN':
        available_members = CustomUser.objects.filter(
            church=care_group.church,
            is_active=True,
            is_new_friend=False,
            role__name__in=['VSL', 'CSL', 'CL', 'CM']
        ).exclude(
            regular_member_profile__group__isnull=False
        ).order_by('first_name', 'last_name')
    
    context = {
        'group': care_group,
        'members': members,
        'recent_activity': recent_activity,
        'capacity_percentage': care_group.capacity_percentage,
        'is_full': care_group.is_full,
        'is_leader': care_group.leader == user or user.role.name == 'ADMIN',
        'available_members': available_members,
        'user_role': user.role.name,
    }
    
    return render(request, 'members/care_group_detail.html', context)


@login_required
def care_group_edit(request, group_id):
    """Edit a care group - only the leader or admin can edit"""
    user = request.user
    care_group = get_object_or_404(Group, pk=group_id, group_type='CARE')
    
    # Check if user is the leader of this care group or admin
    if care_group.leader != user and user.role.name != 'ADMIN':
        messages.error(request, 'Only the group leader or admin can edit this care group.')
        return redirect('members:care_group_detail', group_id=group_id)
    
    if request.method == 'POST':
        form = CareGroupForm(request.POST, instance=care_group, church=user.church, user=user)
        if form.is_valid():
            updated_group = form.save()
            
            # Log the activity
            ActivityLog.objects.create(
                user=user,
                church=user.church,
                action='GROUP_UPDATED',
                description=f'Updated care group: {updated_group.name}'
            )
            
            messages.success(request, f'Care group "{updated_group.name}" updated successfully!')
            return redirect('members:care_group_detail', group_id=group_id)
    else:
        form = CareGroupForm(instance=care_group, church=user.church, user=user)
    
    context = {
        'form': form,
        'group': care_group,
        'user_role': user.role.name,
    }
    
    return render(request, 'members/care_group_edit.html', context)


@login_required
def care_group_add_member(request, group_id):
    """Add a member to a care group"""
    user = request.user
    care_group = get_object_or_404(Group, pk=group_id, group_type='CARE')
    
    # Check if user is the leader of this care group or admin
    if care_group.leader != user and user.role.name != 'ADMIN':
        messages.error(request, 'Only the group leader or admin can add members to this care group.')
        return redirect('members:care_group_detail', group_id=group_id)
    
    if care_group.is_full:
        messages.error(request, 'This care group is already at full capacity.')
        return redirect('members:care_group_detail', group_id=group_id)
    
    if request.method == 'POST':
        member_id = request.POST.get('member_id')
        try:
            member_user = CustomUser.objects.get(pk=member_id, church=care_group.church)
            
            # Get or create RegularMember profile
            regular_member, created = RegularMember.objects.get_or_create(
                user=member_user,
                defaults={'role_type': member_user.role.name}
            )
            
            # Check if member is already in a care group
            if regular_member.group:
                messages.error(request, f'{member_user.full_name} is already in a care group.')
                return redirect('members:care_group_detail', group_id=group_id)
            
            # Add member to care group
            regular_member.group = care_group
            regular_member.save()
            
            # Log the activity
            ActivityLog.objects.create(
                user=user,
                church=user.church,
                action='MEMBER_ADDED_TO_GROUP',
                description=f'Added {member_user.full_name} to care group: {care_group.name}',
                related_user=member_user
            )
            
            messages.success(request, f'{member_user.full_name} has been added to the care group!')
            
        except CustomUser.DoesNotExist:
            messages.error(request, 'Selected member not found.')
    
    return redirect('members:care_group_detail', group_id=group_id)


@login_required
def care_group_remove_member(request, group_id, member_id):
    """Remove a member from a care group"""
    user = request.user
    care_group = get_object_or_404(Group, pk=group_id, group_type='CARE')
    
    # Check if user is the leader of this care group or admin
    if care_group.leader != user and user.role.name != 'ADMIN':
        messages.error(request, 'Only the group leader or admin can remove members from this care group.')
        return redirect('members:care_group_detail', group_id=group_id)
    
    try:
        member_user = CustomUser.objects.get(pk=member_id)
        regular_member = RegularMember.objects.get(user=member_user, group=care_group)
        
        # Remove member from care group
        regular_member.group = None
        regular_member.save()
        
        # Log the activity
        ActivityLog.objects.create(
            user=user,
            church=user.church,
            action='MEMBER_REMOVED_FROM_GROUP',
            description=f'Removed {member_user.full_name} from care group: {care_group.name}',
            related_user=member_user
        )
        
        messages.success(request, f'{member_user.full_name} has been removed from the care group.')
        
    except (CustomUser.DoesNotExist, RegularMember.DoesNotExist):
        messages.error(request, 'Member not found in this care group.')
    
    return redirect('members:care_group_detail', group_id=group_id)


# Role-specific New Friends Views
@login_required
def role_new_friends_list(request):
    """List new friends endorsed to the current user (VSL, CSL, CL)"""
    user = request.user
    
    # Check if user has permission to access this view
    if user.role.name not in ['VSL', 'CSL', 'CL']:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('churches:dashboard')
    
    church = user.church
    
    # Get search and filter parameters
    search = request.GET.get('search', '')
    follow_up_status = request.GET.get('follow_up_status', '')
    timer_status = request.GET.get('timer_status', '')
    
    # Base queryset - Get new friends endorsed to this user
    new_friends_users = CustomUser.objects.filter(
        church=church,
        is_active=True,
        is_new_friend=True,
        new_friend_profile__endorsed_to=user  # Only show new friends endorsed to this user
    )
    
    # Apply search filters
    if search:
        new_friends_users = new_friends_users.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search) |
            Q(new_friend_profile__invited_by__first_name__icontains=search) |
            Q(new_friend_profile__invited_by__last_name__icontains=search)
        )
    
    if timer_status:
        new_friends_users = new_friends_users.filter(timer_status=timer_status)
    
    # Get NewFriend profiles for these users (if they exist)
    new_friends = []
    for user_obj in new_friends_users:
        try:
            new_friend_profile = NewFriend.objects.get(user=user_obj)
            # Add follow-up status filter if specified
            if follow_up_status and new_friend_profile.follow_up_status != follow_up_status:
                continue
            new_friends.append(new_friend_profile)
        except NewFriend.DoesNotExist:
            # Create a default NewFriend profile if it doesn't exist
            new_friend_profile = NewFriend.objects.create(
                user=user_obj,
                invited_by=None,
                endorsed_to=user,
                notes='',
                is_active=True
            )
            new_friends.append(new_friend_profile)
    
    # Apply follow-up status filter to the list
    if follow_up_status:
        new_friends = [nf for nf in new_friends if nf.follow_up_status == follow_up_status]
    
    # Order by registration date (newest first)
    new_friends.sort(key=lambda x: x.registration_date, reverse=True)
    
    # Pagination
    paginator = Paginator(new_friends, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'follow_up_status': follow_up_status,
        'timer_status': timer_status,
        'total_new_friends': len(new_friends),
        'pending_follow_up': len([nf for nf in new_friends if nf.follow_up_status == 'PENDING']),
        'engaged_count': len([nf for nf in new_friends if nf.follow_up_status == 'ENGAGED']),
        'user_role': user.role.name,
        'is_role_view': True,  # Flag to indicate this is a role-specific view
    }
    
    return render(request, 'members/role_new_friends_list.html', context)


# ==================== PROFILE AND ATTENDANCE VIEWS ====================

@login_required
def user_profile(request):
    """Display and edit user profile with QR code"""
    user = request.user
    
    # Generate QR code if it doesn't exist
    if not user.qr_code_image:
        try:
            user.generate_qr_code()
        except Exception as e:
            messages.warning(request, f'Could not generate QR code: {str(e)}')
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('members:user_profile')
    else:
        form = UserProfileForm(instance=user)
    
    # Get attendance summary
    attendance_summary = Attendance.get_user_attendance_summary(user, days=30)
    
    context = {
        'form': form,
        'user': user,
        'attendance_summary': attendance_summary,
    }
    
    return render(request, 'members/user_profile.html', context)


@login_required
def generate_qr_code(request, user_id):
    """Generate QR code for a user"""
    user = get_object_or_404(CustomUser, id=user_id)
    
    # Check permissions
    if not (request.user.is_superuser or 
            request.user.role.name in ['ADMIN', 'VSL', 'CSL', 'CL'] or 
            request.user == user):
        raise PermissionDenied("You don't have permission to generate QR codes for this user.")
    
    try:
        qr_image = user.generate_qr_code()
        messages.success(request, f'QR code generated successfully for {user.full_name}')
    except Exception as e:
        messages.error(request, f'Error generating QR code: {str(e)}')
    
    if request.user == user:
        return redirect('members:user_profile')
    else:
        return redirect('members:member_detail', pk=user_id)


@login_required
def qr_scanner(request):
    """QR code scanner for attendance"""
    user = request.user
    church = user.church
    
    # Initialize forms
    form = QRCodeScanForm()
    manual_form = ManualAttendanceForm(church=church)
    
    if request.method == 'POST':
        # Check if it's a manual attendance form submission
        if 'manual_attendance' in request.POST:
            form = ManualAttendanceForm(request.POST, church=church)
            if form.is_valid():
                try:
                    attendee = form.cleaned_data['member']
                    date = form.cleaned_data['date']
                    time = form.cleaned_data['time']
                    service_type = form.cleaned_data['service_type']
                    notes = form.cleaned_data['notes']
                    
                    # Check if already attended on this date for this service type
                    existing_attendance = Attendance.objects.filter(
                        user=attendee,
                        date=date,
                        attendance_type=service_type
                    ).first()
                    
                    if existing_attendance:
                        messages.warning(request, f'{attendee.full_name} has already been marked present for {service_type} on {date}.')
                    else:
                        # Create attendance record
                        attendance = Attendance.objects.create(
                            user=attendee,
                            church=church,
                            attendance_type=service_type,
                            date=date,
                            time_in=time,
                            notes=notes,
                            scanned_by=user,
                            ip_address=request.META.get('REMOTE_ADDR'),
                            user_agent=request.META.get('HTTP_USER_AGENT', '')
                        )
                        
                        # Update user's last attendance
                        attendee.record_attendance()
                        
                        messages.success(request, f'Manual attendance recorded for {attendee.full_name}')
                        
                        return JsonResponse({
                            'success': True,
                            'message': f'Manual attendance recorded for {attendee.full_name}',
                            'user': {
                                'name': attendee.full_name,
                                'role': attendee.role.get_name_display() if attendee.role else 'No Role',
                                'time': attendance.time_in.strftime('%I:%M %p')
                            }
                        })
                except Exception as e:
                    messages.error(request, f'Error recording manual attendance: {str(e)}')
                    return JsonResponse({
                        'success': False,
                        'message': f'Error recording manual attendance: {str(e)}'
                    })
        else:
            # QR code scanning
            form = QRCodeScanForm(request.POST)
            if form.is_valid():
                qr_data = form.cleaned_data['qr_data']
                attendance_type = form.cleaned_data['attendance_type']
                notes = form.cleaned_data['notes']
                
                try:
                    # Parse QR code data
                    if qr_data.startswith('CHURCH_ATTENDANCE:'):
                        parts = qr_data.split(':')
                        if len(parts) >= 3:
                            qr_code_id = parts[1]
                            email = parts[2]
                            
                            # Find user by QR code ID (only within the same church)
                            try:
                                attendee = CustomUser.objects.get(qr_code_id=qr_code_id, church=church)
                                
                                # Check if already attended today
                                today = timezone.now().date()
                                existing_attendance = Attendance.objects.filter(
                                    user=attendee,
                                    date=today,
                                    attendance_type=attendance_type
                                ).first()
                                
                                if existing_attendance:
                                    messages.warning(request, f'{attendee.full_name} has already been marked present for {attendance_type} today.')
                                    return JsonResponse({
                                        'success': False,
                                        'message': 'qr is already scanned'
                                    })
                                else:
                                    # Create attendance record (record in the church where scanning happens)
                                    attendance = Attendance.objects.create(
                                        user=attendee,
                                        church=church,  # Use scanner's church (where the scanning is happening)
                                        attendance_type=attendance_type,
                                        date=today,
                                        time_in=timezone.now().time(),
                                        notes=notes,
                                        scanned_by=user,
                                        ip_address=request.META.get('REMOTE_ADDR'),
                                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                                    )
                                    
                                    # Update user's last attendance
                                    attendee.record_attendance()
                                    
                                    messages.success(request, f'Attendance recorded for {attendee.full_name}')
                                    
                                    return JsonResponse({
                                        'success': True,
                                        'message': f'Attendance recorded for {attendee.full_name}',
                                        'user': {
                                            'name': attendee.full_name,
                                            'role': attendee.role.get_name_display() if attendee.role else 'No Role',
                                            'time': attendance.time_in.strftime('%I:%M %p')
                                        }
                                    })
                            except CustomUser.DoesNotExist:
                                messages.error(request, 'User not found or QR code is invalid.')
                                return JsonResponse({
                                    'success': False,
                                    'message': 'User not found or QR code is invalid.'
                                })
                        else:
                            messages.error(request, 'Invalid QR code format.')
                            return JsonResponse({
                                'success': False,
                                'message': 'Invalid QR code format.'
                            })
                    else:
                        messages.error(request, 'Invalid QR code. Please scan a valid church attendance QR code.')
                        return JsonResponse({
                            'success': False,
                            'message': 'Invalid QR code. Please scan a valid church attendance QR code.'
                        })
                except Exception as e:
                    messages.error(request, f'Error processing QR code: {str(e)}')
                    return JsonResponse({
                        'success': False,
                        'message': f'Error processing QR code: {str(e)}'
                    })
    
    # Get recent attendances
    recent_attendances = Attendance.objects.filter(
        church=church,
        date=timezone.now().date()
    ).select_related('user').order_by('-time_in')[:10]
    
    context = {
        'form': form,
        'manual_form': manual_form,
        'recent_attendances': recent_attendances,
    }
    
    return render(request, 'members/qr_scanner.html', context)


@login_required
def attendance_list(request):
    """List attendance records with filtering"""
    user = request.user
    church = user.church
    
    # Get filter parameters
    form = AttendanceFilterForm(request.GET, church=church)
    attendances = Attendance.objects.filter(church=church).select_related('user', 'scanned_by')
    
    if form.is_valid():
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        attendance_type = form.cleaned_data.get('attendance_type')
        user_filter = form.cleaned_data.get('user')
        
        if date_from:
            attendances = attendances.filter(date__gte=date_from)
        if date_to:
            attendances = attendances.filter(date__lte=date_to)
        if attendance_type:
            attendances = attendances.filter(attendance_type=attendance_type)
        if user_filter:
            attendances = attendances.filter(user=user_filter)
    
    # Pagination
    paginator = Paginator(attendances, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get summary statistics
    today = timezone.now().date()
    today_attendances = Attendance.objects.filter(church=church, date=today).count()
    this_week = Attendance.objects.filter(
        church=church, 
        date__gte=today - timedelta(days=7)
    ).count()
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'today_attendances': today_attendances,
        'this_week_attendances': this_week,
    }
    
    return render(request, 'members/attendance_list.html', context)


@login_required
def attendance_export(request):
    """Export attendance data"""
    user = request.user
    church = user.church
    
    if request.method == 'POST':
        form = AttendanceExportForm(request.POST)
        if form.is_valid():
            export_format = form.cleaned_data['format']
            date_from = form.cleaned_data.get('date_from')
            date_to = form.cleaned_data.get('date_to')
            attendance_type = form.cleaned_data.get('attendance_type')
            include_qr_codes = form.cleaned_data.get('include_qr_codes', False)
            
            # Filter attendances
            attendances = Attendance.objects.filter(church=church).select_related('user', 'scanned_by')
            
            if date_from:
                attendances = attendances.filter(date__gte=date_from)
            if date_to:
                attendances = attendances.filter(date__lte=date_to)
            if attendance_type:
                attendances = attendances.filter(attendance_type=attendance_type)
            
            # Create response based on format
            if export_format == 'csv':
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="attendance_{church.domain}_{timezone.now().strftime("%Y%m%d")}.csv"'
                
                writer = csv.writer(response)
                headers = ['Date', 'Time In', 'Time Out', 'Name', 'Email', 'Role', 'Attendance Type', 'Notes', 'Scanned By']
                if include_qr_codes:
                    headers.append('QR Code ID')
                writer.writerow(headers)
                
                for attendance in attendances:
                    row = [
                        attendance.date.strftime('%Y-%m-%d'),
                        attendance.time_in.strftime('%I:%M %p'),
                        attendance.time_out.strftime('%I:%M %p') if attendance.time_out else '',
                        attendance.user.full_name,
                        attendance.user.email,
                        attendance.user.role.get_name_display() if attendance.user.role else '',
                        attendance.get_attendance_type_display(),
                        attendance.notes,
                        attendance.scanned_by.full_name if attendance.scanned_by else ''
                    ]
                    if include_qr_codes:
                        row.append(str(attendance.user.qr_code_id))
                    writer.writerow(row)
                
                return response
            
            elif export_format == 'excel':
                # Excel export would require openpyxl
                messages.info(request, 'Excel export feature will be implemented soon.')
                return redirect('members:attendance_export')
            
            elif export_format == 'pdf':
                # PDF export would require reportlab
                messages.info(request, 'PDF export feature will be implemented soon.')
                return redirect('members:attendance_export')
    else:
        form = AttendanceExportForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'members/attendance_export.html', context)


@login_required
def profile_export(request):
    """Export user profiles with QR codes"""
    user = request.user
    church = user.church
    
    if request.method == 'POST':
        form = ProfileExportForm(request.POST)
        if form.is_valid():
            export_format = form.cleaned_data['format']
            include_qr_codes = form.cleaned_data.get('include_qr_codes', False)
            include_profile_pictures = form.cleaned_data.get('include_profile_pictures', False)
            member_type = form.cleaned_data.get('member_type', '')
            
            # Filter users
            users = CustomUser.objects.filter(church=church, is_active=True)
            
            if member_type == 'new_friends':
                users = users.filter(is_new_friend=True)
            elif member_type == 'regular_members':
                users = users.filter(is_new_friend=False)
            
            # Create response based on format
            if export_format == 'csv':
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="profiles_{church.domain}_{timezone.now().strftime("%Y%m%d")}.csv"'
                
                writer = csv.writer(response)
                headers = ['Name', 'Email', 'Phone', 'Address', 'Birth Date', 'Role', 'Member Type', 'Date Joined']
                if include_qr_codes:
                    headers.append('QR Code ID')
                writer.writerow(headers)
                
                for user_obj in users:
                    row = [
                        user_obj.full_name,
                        user_obj.email,
                        user_obj.phone_number,
                        user_obj.address,
                        user_obj.birth_date.strftime('%Y-%m-%d') if user_obj.birth_date else '',
                        user_obj.role.get_name_display() if user_obj.role else '',
                        'New Friend' if user_obj.is_new_friend else 'Regular Member',
                        user_obj.date_joined.strftime('%Y-%m-%d')
                    ]
                    if include_qr_codes:
                        row.append(str(user_obj.qr_code_id))
                    writer.writerow(row)
                
                return response
            
            elif export_format == 'excel':
                messages.info(request, 'Excel export feature will be implemented soon.')
                return redirect('members:profile_export')
            
            elif export_format == 'pdf':
                messages.info(request, 'PDF export feature will be implemented soon.')
                return redirect('members:profile_export')
    else:
        form = ProfileExportForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'members/profile_export.html', context)


@login_required
def profile_import(request):
    """Import user profiles"""
    user = request.user
    church = user.church
    
    if request.method == 'POST':
        form = ProfileImportForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['file']
            update_existing = form.cleaned_data.get('update_existing', False)
            generate_qr_codes = form.cleaned_data.get('generate_qr_codes', True)
            
            try:
                # Process the file
                if file.name.endswith('.csv'):
                    # CSV processing
                    decoded_file = file.read().decode('utf-8')
                    csv_data = csv.DictReader(io.StringIO(decoded_file))
                    
                    imported_count = 0
                    updated_count = 0
                    
                    for row in csv_data:
                        email = row.get('email', '').strip()
                        if not email:
                            continue
                        
                        # Check if user exists
                        try:
                            existing_user = CustomUser.objects.get(email=email, church=church)
                            if update_existing:
                                # Update existing user
                                existing_user.first_name = row.get('first_name', existing_user.first_name)
                                existing_user.last_name = row.get('last_name', existing_user.last_name)
                                existing_user.phone_number = row.get('phone_number', existing_user.phone_number)
                                existing_user.address = row.get('address', existing_user.address)
                                if row.get('birth_date'):
                                    try:
                                        existing_user.birth_date = datetime.strptime(row['birth_date'], '%Y-%m-%d').date()
                                    except ValueError:
                                        pass
                                existing_user.save()
                                updated_count += 1
                        except CustomUser.DoesNotExist:
                            # Create new user
                            new_user = CustomUser.objects.create(
                                email=email,
                                first_name=row.get('first_name', ''),
                                last_name=row.get('last_name', ''),
                                phone_number=row.get('phone_number', ''),
                                address=row.get('address', ''),
                                church=church,
                                is_new_friend=True,  # Default to new friend
                                is_active=True
                            )
                            
                            if row.get('birth_date'):
                                try:
                                    new_user.birth_date = datetime.strptime(row['birth_date'], '%Y-%m-%d').date()
                                    new_user.save()
                                except ValueError:
                                    pass
                            
                            # Generate QR code if requested
                            if generate_qr_codes:
                                new_user.generate_qr_code()
                            
                            imported_count += 1
                    
                    messages.success(request, f'Import completed: {imported_count} new users imported, {updated_count} users updated.')
                else:
                    messages.info(request, 'Excel import feature will be implemented soon.')
                
            except Exception as e:
                messages.error(request, f'Error importing file: {str(e)}')
    else:
        form = ProfileImportForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'members/profile_import.html', context)

