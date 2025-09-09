"""
Placeholder views for functions that need to be implemented
These are temporary implementations to keep the system working
while we organize the views systematically
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from ..models import *
from ..forms import *

User = get_user_model()

@login_required
def activity_logs(request):
    """View activity logs for the user's church"""
    user = request.user
    church = user.church
    
    action_filter = request.GET.get('action', '')
    user_filter = request.GET.get('user', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    activities = ActivityLog.objects.filter(
        church=church
    ).select_related('user', 'related_user').order_by('-timestamp')
    
    if action_filter:
        activities = activities.filter(action=action_filter)
    
    if user_filter:
        activities = activities.filter(user__id=user_filter)
    
    if date_from:
        activities = activities.filter(timestamp__date__gte=date_from)
    
    if date_to:
        activities = activities.filter(timestamp__date__lte=date_to)
    
    paginator = Paginator(activities, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    action_choices = [
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('NEW_FRIEND_ADDED', 'New Friend Added'),
        ('REGULAR_MEMBER_ADDED', 'Regular Member Added'),
        ('STATUS_CHANGE', 'Status Change'),
        ('ROLE_UPDATED', 'Role Updated'),
        ('GROUP_JOINED', 'Group Joined'),
        ('GROUP_LEFT', 'Group Left'),
        ('ATTENDANCE_RECORDED', 'Attendance Recorded'),
    ]
    
    church_users = CustomUser.objects.filter(church=church, is_active=True).order_by('first_name')
    
    context = {
        'page_obj': page_obj,
        'action_filter': action_filter,
        'user_filter': user_filter,
        'date_from': date_from,
        'date_to': date_to,
        'action_choices': action_choices,
        'church_users': church_users,
        'total_activities': activities.count(),
    }
    
    return render(request, 'members/activity_logs.html', context)

@login_required  
def church_statistics(request):
    """Church statistics dashboard"""
    return render(request, 'members/church_statistics.html', {})

@csrf_exempt
@login_required
def ajax_get_available_members(request, group_id):
    """AJAX endpoint to get available members for a group"""
    return JsonResponse({'members': []})

@csrf_exempt
@login_required
def ajax_update_timer_status(request, user_id):
    """AJAX endpoint to update timer status"""
    return JsonResponse({'success': True})

@csrf_exempt
@login_required
def ajax_record_attendance(request, user_id):
    """AJAX endpoint to record attendance"""
    return JsonResponse({'success': True})

@csrf_exempt
@login_required
def ajax_update_follow_up(request, new_friend_id):
    """AJAX endpoint to update follow up status"""
    return JsonResponse({'success': True})

@csrf_exempt
@login_required
def ajax_add_to_group(request, user_id, group_id):
    """AJAX endpoint to add member to group"""
    return JsonResponse({'success': True})

@csrf_exempt
@login_required
def ajax_remove_from_group(request, user_id, group_id):
    """AJAX endpoint to remove member from group"""
    return JsonResponse({'success': True})

@login_required
def export_members(request):
    """Export members data"""
    return render(request, 'members/export_members.html', {})

@login_required
def role_management(request):
    """Role management view for admins only"""
    user = request.user

    if not (user.is_superuser or user.role.name == 'ADMIN'):
        messages.error(request, 'You do not have permission to access role management.')
        return redirect('churches:dashboard')
    
    church = user.church
    
    search = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    
    users = CustomUser.objects.filter(church=church, is_active=True)
    
    if search:
        users = users.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )
    
    if role_filter:
        users = users.filter(role__name=role_filter)
    
    users = users.order_by('role__name', 'first_name', 'last_name')
    
    paginator = Paginator(users, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    roles = Role.objects.filter(
        name__in=['VSL', 'CSL', 'CL', 'CM', 'NEW_FRIEND']
    ).order_by('name')
    
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
    
    if not (user.is_superuser or user.role.name == 'ADMIN'):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        target_user = get_object_or_404(CustomUser, pk=user_id, church=user.church)
        new_role_name = request.POST.get('role')
        
        if not new_role_name:
            return JsonResponse({'error': 'Role is required'}, status=400)
        
        new_role = get_object_or_404(Role, name=new_role_name)

        old_role = target_user.role
        target_user.role = new_role
        target_user.save()
        
        ActivityLog.objects.create(
            user=user,
            action='ROLE_CHANGE',
            description=f'Changed role from {old_role.get_name_display() if old_role else "None"} to {new_role.get_name_display()} for {target_user.full_name}',
            related_user=target_user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        if target_user.is_new_friend and new_role_name not in ['NEW_FRIEND']:
            target_user.is_new_friend = False
            target_user.transition_date = timezone.now()
            target_user.save()
            
            RegularMember.objects.get_or_create(
                user=target_user,
                defaults={'role_type': new_role_name}
            )

            try:
                if hasattr(target_user, 'new_friend_profile'):
                    target_user.new_friend_profile.delete()
            except NewFriend.DoesNotExist:
                pass

        return JsonResponse({
            'success': True,
            'message': f'Role updated to {new_role.get_name_display()}',
            'new_role': new_role.get_name_display()
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def ajax_get_user_details(request, user_id):
    """AJAX endpoint to get user details for role management"""
    user = request.user
    
    if not (user.is_superuser or user.role.name == 'ADMIN'):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        target_user = get_object_or_404(CustomUser, pk=user_id, church=user.church)
        
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
    
    if not (user.is_superuser or user.role.name == 'ADMIN'):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        user_ids = request.POST.getlist('user_ids[]')
        new_role_name = request.POST.get('role')
        
        if not user_ids or not new_role_name:
            return JsonResponse({'error': 'User IDs and role are required'}, status=400)
        
        new_role = get_object_or_404(Role, name=new_role_name)
        
        updated_count = 0
        for user_id in user_ids:
            try:
                target_user = CustomUser.objects.get(pk=user_id, church=user.church)
                old_role = target_user.role
                target_user.role = new_role
                target_user.save()
                
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
def care_group_list(request):
    """List care groups for leadership roles (VSL, CSL, CL) and admin"""
    user = request.user

    if user.role.name not in ['VSL', 'CSL', 'CL', 'ADMIN']:
        messages.error(request, 'You do not have permission to access care groups.')
        return redirect('churches:dashboard')
    
    church = user.church

    search = request.GET.get('search', '')

    care_groups = Group.objects.filter(
        church=church,
        group_type='CARE',
        is_active=True
    ).select_related('leader').prefetch_related('members')

    if user.role.name == 'VSL':
        user_groups = Group.objects.filter(leader=user, group_type='CARE')
        member_users = CustomUser.objects.filter(
            regular_member_profile__group__in=user_groups
        ).exclude(id=user.id)
        
        care_groups = care_groups.filter(
            Q(leader=user) | 
            Q(leader__in=member_users)
        ).distinct()
    elif user.role.name == 'CSL':
        user_groups = Group.objects.filter(leader=user, group_type='CARE')
        member_users = CustomUser.objects.filter(
            regular_member_profile__group__in=user_groups
        ).exclude(id=user.id)
        
        care_groups = care_groups.filter(
            Q(leader=user) | 
            Q(leader__in=member_users)
        ).distinct()
    elif user.role.name == 'CL':
        care_groups = care_groups.filter(leader=user)
    elif user.role.name == 'ADMIN':
        pass
    
    if search:
        care_groups = care_groups.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(leader__first_name__icontains=search) |
            Q(leader__last_name__icontains=search)
        )

    care_groups = care_groups.order_by('name')

    paginator = Paginator(care_groups, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

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

    if user.role.name not in ['VSL', 'CSL', 'CL', 'ADMIN']:
        messages.error(request, 'You do not have permission to create care groups.')
        return redirect('members:care_group_list')
    
    if request.method == 'POST':
        form = CareGroupForm(request.POST, church=user.church, user=user)
        if form.is_valid():
            care_group = form.save()

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
    
    if not user.can_access_church_data(care_group.church):
        messages.error(request, 'You do not have permission to view this care group.')
        return redirect('members:care_group_list')
    
    if user.role.name in ['CSL', 'CL'] and care_group.leader != user:
        try:
            user_member_profile = RegularMember.objects.get(user=user)
            if user_member_profile.group != care_group:
                messages.error(request, 'You can only view care groups you lead or are a member of.')
                return redirect('members:care_group_list')
        except RegularMember.DoesNotExist:
            messages.error(request, 'You can only view care groups you lead or are a member of.')
            return redirect('members:care_group_list')

    members = care_group.members.select_related('user').order_by('user__first_name')

    recent_activity = ActivityLog.objects.filter(
        user__regular_member_profile__group=care_group
    ).select_related('user').order_by('-timestamp')[:10]

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

    if care_group.leader != user and user.role.name != 'ADMIN':
        messages.error(request, 'Only the group leader or admin can edit this care group.')
        return redirect('members:care_group_detail', group_id=group_id)
    
    if request.method == 'POST':
        form = CareGroupForm(request.POST, instance=care_group, church=user.church, user=user)
        if form.is_valid():
            updated_group = form.save()
 
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

            regular_member, created = RegularMember.objects.get_or_create(
                user=member_user,
                defaults={'role_type': member_user.role.name}
            )

            if regular_member.group:
                messages.error(request, f'{member_user.full_name} is already in a care group.')
                return redirect('members:care_group_detail', group_id=group_id)

            regular_member.group = care_group
            regular_member.save()

            ActivityLog.objects.create(
                user=user,
                church=user.church,
                action='GROUP_JOINED',
                description=f'{member_user.full_name} joined care group: {care_group.name}',
                related_user=member_user
            )

            messages.success(request, f'{member_user.full_name} has been added to {care_group.name}.')
            
        except CustomUser.DoesNotExist:
            messages.error(request, 'Selected member not found.')
        except Exception as e:
            messages.error(request, f'Error adding member: {str(e)}')
    
    return redirect('members:care_group_detail', group_id=group_id)

@login_required
def care_group_remove_member(request, group_id, member_id):
    """Remove a member from a care group"""
    user = request.user
    care_group = get_object_or_404(Group, pk=group_id, group_type='CARE')

    if care_group.leader != user and user.role.name != 'ADMIN':
        messages.error(request, 'Only the group leader or admin can remove members from this care group.')
        return redirect('members:care_group_detail', group_id=group_id)
    
    try:
        regular_member = get_object_or_404(RegularMember, pk=member_id, group=care_group)
        member_user = regular_member.user

        regular_member.group = None
        regular_member.save()

        ActivityLog.objects.create(
            user=user,
            church=user.church,
            action='GROUP_LEFT',
            description=f'{member_user.full_name} left care group: {care_group.name}',
            related_user=member_user
        )

        messages.success(request, f'{member_user.full_name} has been removed from {care_group.name}.')
        
    except Exception as e:
        messages.error(request, f'Error removing member: {str(e)}')
    
    return redirect('members:care_group_detail', group_id=group_id)

@login_required
def role_new_friends_list(request):
    """New friends list for specific roles"""
    return render(request, 'members/role_new_friends_list.html', {})

@login_required
def user_profile(request):
    """User profile page"""
    return render(request, 'members/user_profile.html', {})

@login_required
def generate_qr_code(request, user_id):
    """Generate QR code"""
    return render(request, 'members/generate_qr_code.html', {})

@login_required
def qr_scanner(request):
    """QR code scanner for attendance"""
    user = request.user
    church = user.church

    form = QRCodeScanForm()
    manual_form = ManualAttendanceForm(church=church)
    
    if request.method == 'POST':

        if 'manual_attendance' in request.POST:
            form = ManualAttendanceForm(request.POST, church=church)
            if form.is_valid():
                try:
                    attendee = form.cleaned_data['member']
                    date = form.cleaned_data['date']
                    time = form.cleaned_data['time']
                    service_type = form.cleaned_data['service_type']
                    notes = form.cleaned_data['notes']

                    existing_attendance = Attendance.objects.filter(
                        user=attendee,
                        date=date,
                        attendance_type=service_type
                    ).first()
                    
                    if existing_attendance:
                        messages.warning(request, f'{attendee.full_name} has already been marked present for {service_type} on {date}.')
                    else:
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
                        
                        attendee.record_attendance()
                        
                        status_update_message = ""
                        if attendee.is_new_friend and service_type == 'SUNDAY':
                            current_status = attendee.timer_status
                            if current_status < 5:
                                new_status = current_status + 1
                                attendee.timer_status = new_status
                                attendee.save()
                                status_update_message = f" Status updated to {new_status}{'st' if new_status == 1 else 'nd' if new_status == 2 else 'rd' if new_status == 3 else 'th'} timer."
                            
                            elif current_status == 5:
                                from members.models import Role
                                cm_role, created = Role.objects.get_or_create(
                                    name='CM',
                                    defaults={'description': 'Care Member'}
                                )
                                attendee.transition_to_regular()
                                attendee.role = cm_role
                                attendee.save()
                                status_update_message = " Congratulations! You are now a regular member with CM role!"
                            else:
                                status_update_message = " You are already a regular member!"
                        
                        messages.success(request, f'Manual attendance recorded for {attendee.full_name}{status_update_message}')
                        
                        return JsonResponse({
                            'success': True,
                            'message': f'Manual attendance recorded for {attendee.full_name}{status_update_message}',
                            'user': {
                                'name': attendee.full_name,
                                'role': attendee.role.get_name_display() if attendee.role else 'No Role',
                                'time': attendance.time_in.strftime('%I:%M %p'),
                                'timer_status': attendee.timer_status if attendee.is_new_friend else None,
                                'is_new_friend': attendee.is_new_friend
                            }
                        })
                except Exception as e:
                    messages.error(request, f'Error recording manual attendance: {str(e)}')
                    return JsonResponse({
                        'success': False,
                        'message': f'Error recording manual attendance: {str(e)}'
                    })
        else:
            form = QRCodeScanForm(request.POST)
            if form.is_valid():
                qr_data = form.cleaned_data['qr_data']
                attendance_type = form.cleaned_data['attendance_type']
                notes = form.cleaned_data['notes']

                client_date_str = request.POST.get('client_date')
                client_time_str = request.POST.get('client_time')

                if client_date_str and client_time_str:
                    try:
                        from datetime import datetime
                        client_date = datetime.strptime(client_date_str, '%Y-%m-%d').date()
                        client_time = datetime.strptime(client_time_str, '%H:%M:%S').time()
                    except ValueError:
                        client_date = timezone.now().date()
                        client_time = timezone.now().time()
                else:
                    client_date = timezone.now().date()
                    client_time = timezone.now().time()
                
                try:
                    if qr_data.startswith('CHURCH_ATTENDANCE:'):
                        parts = qr_data.split(':')
                        if len(parts) >= 3:
                            qr_code_id = parts[1]
                            email = parts[2]

                            try:
                                attendee = CustomUser.objects.get(qr_code_id=qr_code_id, church=church)
                                existing_attendance = Attendance.objects.filter(
                                    user=attendee,
                                    date=client_date,
                                    attendance_type=attendance_type
                                ).first()
                                
                                if existing_attendance:
                                    messages.warning(request, f'{attendee.full_name} has already been marked present for {attendance_type} today.')
                                    return JsonResponse({
                                        'success': False,
                                        'message': 'qr is already scanned'
                                    })
                                else:
                                    attendance = Attendance.objects.create(
                                        user=attendee,
                                        church=church,
                                        attendance_type=attendance_type,
                                        date=client_date,     
                                        time_in=client_time, 
                                        notes=notes,
                                        scanned_by=user,
                                        ip_address=request.META.get('REMOTE_ADDR'),
                                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                                    )

                                    attendee.record_attendance()

                                    status_update_message = ""
                                    if attendee.is_new_friend and attendance_type == 'SUNDAY':
                                        current_status = attendee.timer_status
                                        if current_status < 5:
                                            new_status = current_status + 1
                                            attendee.timer_status = new_status
                                            attendee.save()
                                            status_update_message = f" Status updated to {new_status}{'st' if new_status == 1 else 'nd' if new_status == 2 else 'rd' if new_status == 3 else 'th'} timer."
                                        
                                        elif current_status == 5:
                                            from members.models import Role
                                            cm_role, created = Role.objects.get_or_create(
                                                name='CM',
                                                defaults={'description': 'Care Member'}
                                            )
                                            attendee.transition_to_regular()
                                            attendee.role = cm_role
                                            attendee.save()
                                            status_update_message = " Congratulations! You are now a regular member with CM role!"
                                        else:
                                            status_update_message = " You are already a regular member!"
                                    
                                    messages.success(request, f'Attendance recorded for {attendee.full_name}{status_update_message}')
                                    
                                    return JsonResponse({
                                        'success': True,
                                        'message': f'Attendance recorded for {attendee.full_name}{status_update_message}',
                                        'user': {
                                            'name': attendee.full_name,
                                            'role': attendee.role.get_name_display() if attendee.role else 'No Role',
                                            'time': attendance.time_in.strftime('%I:%M %p'),
                                            'timer_status': attendee.timer_status if attendee.is_new_friend else None,
                                            'is_new_friend': attendee.is_new_friend
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

    paginator = Paginator(attendances, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

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

            attendances = Attendance.objects.filter(church=church).select_related('user', 'scanned_by')
            
            if date_from:
                attendances = attendances.filter(date__gte=date_from)
            if date_to:
                attendances = attendances.filter(date__lte=date_to)
            if attendance_type:
                attendances = attendances.filter(attendance_type=attendance_type)

            if export_format == 'csv':
                from django.http import HttpResponse
                import csv
                
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
                        attendance.time_in.strftime('%H:%M:%S') if attendance.time_in else '',
                        attendance.time_out.strftime('%H:%M:%S') if attendance.time_out else '',
                        attendance.user.full_name,
                        attendance.user.email,
                        attendance.user.role.get_name_display() if attendance.user.role else '',
                        attendance.get_attendance_type_display(),
                        attendance.notes or '',
                        attendance.scanned_by.full_name if attendance.scanned_by else ''
                    ]
                    if include_qr_codes:
                        row.append(attendance.user.qr_code_id or '')
                    writer.writerow(row)
                
                return response
    else:
        form = AttendanceExportForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'members/attendance_export.html', context)

@login_required
def profile_export(request):
    """Export profiles"""
    return render(request, 'members/profile_export.html', {})

@login_required
def profile_import(request):
    """Import profiles"""
    return render(request, 'members/profile_import.html', {})

@login_required
def care_group_report_list(request):
    """Care group reports list"""
    return render(request, 'members/care_group_report_list.html', {})

@login_required
def care_group_report_create(request):
    """Create care group report"""
    return render(request, 'members/care_group_report_create.html', {})

@login_required
def care_group_member_report_create(request, report_id):
    """Create care group member report"""
    return render(request, 'members/care_group_member_report_create.html', {})

@login_required
def care_group_report_detail(request, report_id):
    """Care group report detail"""
    return render(request, 'members/care_group_report_detail.html', {})

@login_required
def care_group_report_print(request, report_id):
    """Print care group report"""
    return render(request, 'members/care_group_report_print.html', {})

@login_required
def care_group_report_edit(request, report_id):
    """Edit care group report"""
    return render(request, 'members/care_group_report_edit.html', {})

@login_required
def care_group_report_delete(request, report_id):
    """Delete care group report"""
    return redirect('members:care_group_report_list')

@login_required
def care_group_attendance_tracking(request, group_id):
    """Care group attendance tracking"""
    return render(request, 'members/care_group_attendance_tracking.html', {})
