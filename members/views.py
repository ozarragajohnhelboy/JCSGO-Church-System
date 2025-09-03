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
    ActivityLog
)
from .forms import (
    CustomUserForm, NewFriendForm, RegularMemberForm, 
    GroupForm, ProfileUpdateForm, NewFriendImportForm, RegularMemberImportForm
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
    paginator = Paginator(new_friends, 15)
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
    paginator = Paginator(users, 25)
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
                    # Create the user first
                    user = CustomUser.objects.create_user(
                        email=form.cleaned_data['email'],
                        first_name=form.cleaned_data['first_name'],
                        last_name=form.cleaned_data['last_name'],
                        phone_number=form.cleaned_data['phone'],
                        church=request.user.church,
                        is_new_friend=True,
                        is_active=True
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
                    new_friend.notes = form.cleaned_data['notes']
                    new_friend.save()
                    
                    # Log the activity
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
        form.fields['email'].initial = new_friend.user.email
        form.fields['first_name'].initial = new_friend.user.first_name
        form.fields['last_name'].initial = new_friend.user.last_name
        form.fields['phone'].initial = new_friend.user.phone_number
        form.fields['invited_by'].initial = new_friend.invited_by
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
                                # Create user
                                user = CustomUser.objects.create_user(
                                    email=row.get('email', '').strip(),
                                    first_name=row.get('first_name', '').strip(),
                                    last_name=row.get('last_name', '').strip(),
                                    phone_number=row.get('phone', '').strip() or None,
                                    church=request.user.church,
                                    is_new_friend=True,
                                    is_active=True
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
                    # Create the user first
                    user = CustomUser.objects.create_user(
                        email=form.cleaned_data['email'],
                        first_name=form.cleaned_data['first_name'],
                        last_name=form.cleaned_data['last_name'],
                        phone_number=form.cleaned_data['phone'],
                        church=request.user.church,
                        is_new_friend=False,
                        is_active=True
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
        form.fields['email'].initial = regular_member.user.email
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
                                
                                # Create user
                                user = CustomUser.objects.create_user(
                                    email=row.get('email', '').strip(),
                                    first_name=row.get('first_name', '').strip(),
                                    last_name=row.get('last_name', '').strip(),
                                    phone_number=row.get('phone', '').strip() or None,
                                    church=request.user.church,
                                    role=role,
                                    is_new_friend=False,
                                    is_active=True
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
