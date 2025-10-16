from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Count

from members.models import Church, Role, CustomUser, ActivityLog

User = get_user_model()


@login_required
def dashboard(request):
    """User dashboard based on role and church"""
    user = request.user
    
    new_friends_count = CustomUser.objects.filter(
        church=user.church, 
        is_new_friend=True, 
        is_active=True
    ).count()
    
    regulars_count = CustomUser.objects.filter(
        church=user.church, 
        is_new_friend=False, 
        is_active=True
    ).count()
    
    total_members = new_friends_count + regulars_count

    from datetime import datetime, timedelta
    from django.db.models import Count
    from django.utils import timezone
    
    activity_date_filter = request.GET.get('activity_date', '')
    
    # Get recent activity with date filter
    recent_activity_query = ActivityLog.objects.filter(user__church=user.church)
    
    if activity_date_filter:
        try:
            # Parse the date filter
            filter_date = datetime.strptime(activity_date_filter, '%Y-%m-%d').date()
            # Filter activities for the specific date
            recent_activity_query = recent_activity_query.filter(
                timestamp__date=filter_date
            )
        except ValueError:
            # If date parsing fails, use default (last 7 days)
            pass
    
    # If no date filter or invalid date, show last 7 days by default
    if not activity_date_filter:
        week_ago = timezone.now() - timedelta(days=7)
        recent_activity_query = recent_activity_query.filter(timestamp__gte=week_ago)
    
    # Limit to 5 items and order by timestamp
    recent_activity = recent_activity_query.select_related('user').order_by('-timestamp')[:5]
    
    # Get last 6 months of data
    months = []
    new_friends_monthly = []
    regulars_monthly = []
    
    for i in range(6):
        date = timezone.now() - timedelta(days=30*i)
        month_start = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = month_start + timedelta(days=32)
        month_end = month_end.replace(day=1) - timedelta(seconds=1)
        
        months.append(month_start.strftime('%b %Y'))
        
        # Count new friends for this month
        month_new_friends = CustomUser.objects.filter(
            church=user.church,
            is_new_friend=True,
            date_joined__gte=month_start,
            date_joined__lte=month_end
        ).count()
        new_friends_monthly.append(month_new_friends)
        
        # Count regular members for this month
        month_regulars = CustomUser.objects.filter(
            church=user.church,
            is_new_friend=False,
            date_joined__gte=month_start,
            date_joined__lte=month_end
        ).count()
        regulars_monthly.append(month_regulars)
    
    # Reverse to show oldest to newest
    months.reverse()
    new_friends_monthly.reverse()
    regulars_monthly.reverse()
    
    # Get role distribution data
    role_distribution = []
    if not user.is_new_friend:
        roles = Role.objects.filter(name__in=['VSL', 'CSL', 'CL', 'CM'])
        for role in roles:
            count = CustomUser.objects.filter(
                church=user.church,
                role=role,
                is_new_friend=False,
                is_active=True
            ).count()
            if count > 0:
                role_distribution.append({
                    'role': role.get_name_display(),
                    'count': count,
                    'percentage': round((count / regulars_count * 100) if regulars_count > 0 else 0, 1)
                })
    
    # Get activity trends
    activity_trends = []
    for i in range(7):
        date = timezone.now() - timedelta(days=i)
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1) - timedelta(seconds=1)
        
        daily_activities = ActivityLog.objects.filter(
            user__church=user.church,
            timestamp__gte=day_start,
            timestamp__lte=day_end
        ).count()
        
        activity_trends.append({
            'date': date.strftime('%a'),
            'count': daily_activities
        })
    
    activity_trends.reverse()
    
    context = {
        'user': user,
        'church': user.church,
        'new_friends_count': new_friends_count,
        'regulars_count': regulars_count,
        'total_members': total_members,
        'recent_activity': recent_activity,
        'activity_date_filter': activity_date_filter,
        'months': months,
        'new_friends_monthly': new_friends_monthly,
        'regulars_monthly': regulars_monthly,
        'role_distribution': role_distribution,
        'activity_trends': activity_trends,
    }
    
    # Super admin dashboard
    if user.is_superuser:
        # Get all churches data for super admin
        all_churches = Church.objects.filter(is_active=True).order_by('name')
        
        # Get church stats for super admin
        church_stats = []
        total_system_members = 0
        total_system_new_friends = 0
        total_system_regulars = 0
        
        for church in all_churches:
            church_new_friends = CustomUser.objects.filter(
                church=church, is_new_friend=True, is_active=True
            ).count()
            church_regulars = CustomUser.objects.filter(
                church=church, is_new_friend=False, is_active=True
            ).count()
            church_total = church_new_friends + church_regulars
            
            total_system_members += church_total
            total_system_new_friends += church_new_friends
            total_system_regulars += church_regulars
            
            church_stats.append({
                'church': church,
                'total_members': church_total,
                'new_friends': church_new_friends,
                'regular_members': church_regulars,
            })
        
        # Get system-wide monthly growth
        system_months = []
        system_growth = []
        
        for i in range(6):
            date = timezone.now() - timedelta(days=30*i)
            month_start = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = month_start + timedelta(days=32)
            month_end = month_end.replace(day=1) - timedelta(seconds=1)
            
            system_months.append(month_start.strftime('%b %Y'))
            
            month_total = CustomUser.objects.filter(
                date_joined__gte=month_start,
                date_joined__lte=month_end,
                is_active=True
            ).count()
            system_growth.append(month_total)
        
        system_months.reverse()
        system_growth.reverse()
        
        context.update({
            'churches': all_churches,
            'church_stats': church_stats,
            'total_system_members': total_system_members,
            'total_system_new_friends': total_system_new_friends,
            'total_system_regulars': total_system_regulars,
            'system_months': system_months,
            'system_growth': system_growth,
        })
        return render(request, 'churches/dashboard/super_admin_dashboard.html', context)
    
    # Church admin dashboard
    elif user.role.name == 'ADMIN':
        # Get church-specific data for admin
        church = user.church
        
        # Get regular members breakdown by role
        vsl_count = CustomUser.objects.filter(
            church=church, role__name='VSL', is_new_friend=False, is_active=True
        ).count()
        csl_count = CustomUser.objects.filter(
            church=church, role__name='CSL', is_new_friend=False, is_active=True
        ).count()
        cl_count = CustomUser.objects.filter(
            church=church, role__name='CL', is_new_friend=False, is_active=True
        ).count()
        cm_count = CustomUser.objects.filter(
            church=church, role__name='CM', is_new_friend=False, is_active=True
        ).count()
        
        # Calculate percentages
        total_regulars = vsl_count + csl_count + cl_count + cm_count
        vsl_percentage = round((vsl_count / total_regulars * 100) if total_regulars > 0 else 0, 1)
        csl_percentage = round((csl_count / total_regulars * 100) if total_regulars > 0 else 0, 1)
        cl_percentage = round((cl_count / total_regulars * 100) if total_regulars > 0 else 0, 1)
        cm_percentage = round((cm_count / total_regulars * 100) if total_regulars > 0 else 0, 1)
        
        # Get active groups count
        from members.models import Group
        active_groups_count = Group.objects.filter(
            church=church, is_active=True
        ).count()
        
        # Get group capacity data (limit to 5)
        groups = Group.objects.filter(church=church, is_active=True)[:5]
        group_capacity_data = []
        for group in groups:
            group_capacity_data.append({
                'name': group.name,
                'current': group.member_count,
                'max': group.max_members,
                'percentage': group.capacity_percentage
            })
        
        # Get timer status distribution for new friends
        timer_distribution = []
        for i in range(1, 6):
            count = CustomUser.objects.filter(
                church=church,
                is_new_friend=True,
                timer_status=i,
                is_active=True
            ).count()
            if count > 0:
                timer_distribution.append({
                    'timer': f'{i}{"st" if i == 1 else "nd" if i == 2 else "rd" if i == 3 else "th"} Timer',
                    'count': count,
                    'percentage': round((count / new_friends_count * 100) if new_friends_count > 0 else 0, 1)
                })
        
        # Get monthly transition statistics (new friends to regular members)
        transition_months = []
        transition_counts = []
        
        for i in range(6):
            date = timezone.now() - timedelta(days=30*i)
            month_start = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = month_start + timedelta(days=32)
            month_end = month_end.replace(day=1) - timedelta(seconds=1)
            
            transition_months.append(month_start.strftime('%b %Y'))
            
            # Count transitions in this month
            month_transitions = CustomUser.objects.filter(
                church=church,
                is_new_friend=False,
                transition_date__gte=month_start,
                transition_date__lte=month_end,
                is_active=True
            ).count()
            transition_counts.append(month_transitions)
        
        # Reverse to show oldest to newest
        transition_months.reverse()
        transition_counts.reverse()
        
        # Get transition rate (this month)
        current_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        current_month_transitions = CustomUser.objects.filter(
            church=church,
            is_new_friend=False,
            transition_date__gte=current_month_start,
            is_active=True
        ).count()
        
        # Calculate transition rate percentage
        transition_rate = round((current_month_transitions / new_friends_count * 100) if new_friends_count > 0 else 0, 1)
        
        context.update({
            'church': church,
            'vsl_count': vsl_count,
            'csl_count': csl_count,
            'cl_count': cl_count,
            'cm_count': cm_count,
            'vsl_percentage': vsl_percentage,
            'csl_percentage': csl_percentage,
            'cl_percentage': cl_percentage,
            'cm_percentage': cm_percentage,
            'active_groups_count': active_groups_count,
            'group_capacity_data': group_capacity_data,
            'timer_distribution': timer_distribution,
            'transition_months': transition_months,
            'transition_counts': transition_counts,
            'current_month_transitions': current_month_transitions,
            'transition_rate': transition_rate,
        })
        return render(request, 'churches/dashboard/admin_dashboard.html', context)
    
    # Church leader dashboard (VSL, CSL, CL)
    elif user.role.name in ['VSL', 'CSL', 'CL']:
        from members.models import Group, RegularMember
        
        # Get care groups led by this user
        led_groups = Group.objects.filter(
            leader=user,
            church=user.church,
            group_type='CARE',
            is_active=True
        )
        
        # Get direct care group members
        direct_members = CustomUser.objects.filter(
            regular_member_profile__group__in=led_groups,
            church=user.church,
            is_active=True
        ).distinct()
        
        # Get nested members (members of their members' groups)
        nested_members = CustomUser.objects.none()
        if user.role.name in ['VSL', 'CSL']:
            # Get members who are leaders of other care groups
            member_leaders = CustomUser.objects.filter(
                regular_member_profile__group__in=led_groups,
                church=user.church,
                is_active=True
            ).exclude(id=user.id)
            
            # Get care groups led by these member leaders
            nested_groups = Group.objects.filter(
                leader__in=member_leaders,
                church=user.church,
                group_type='CARE',
                is_active=True
            )
            
            # Get members of these nested groups
            nested_members = CustomUser.objects.filter(
                regular_member_profile__group__in=nested_groups,
                church=user.church,
                is_active=True
            ).distinct()
        
        # Calculate member counts
        direct_members_count = direct_members.count()
        nested_members_count = nested_members.count()
        total_care_group_members = direct_members_count + nested_members_count
        
        # Get role distribution of members under this leader only
        role_distribution = []
        
        # Get all member IDs under this leader (direct + nested)
        direct_member_ids = list(direct_members.values_list('id', flat=True))
        nested_member_ids = list(nested_members.values_list('id', flat=True))
        all_leader_member_ids = list(set(direct_member_ids + nested_member_ids))
        total_leader_members = len(all_leader_member_ids)
        
        # Add self to the count
        self_count = 1
        role_distribution.append({
            'role': user.role.get_name_display(),
            'count': self_count,
            'percentage': round((self_count / (total_leader_members + 1) * 100) if (total_leader_members + 1) > 0 else 0, 1)
        })
        
        # Get role distributions of members under this leader
        roles = Role.objects.filter(name__in=['VSL', 'CSL', 'CL', 'CM', 'NEW_FRIEND'])
        for role in roles:
            if role.name != user.role.name:
                count = CustomUser.objects.filter(
                    id__in=all_leader_member_ids,
                    role=role,
                    church=user.church,
                    is_active=True
                ).count()
                if count > 0:
                    role_distribution.append({
                        'role': role.get_name_display(),
                        'count': count,
                        'percentage': round((count / (total_leader_members + 1) * 100) if (total_leader_members + 1) > 0 else 0, 1)
                    })
        
        # Get care group growth over time (last 6 months)
        care_group_growth_months = []
        care_group_growth_counts = []
        
        for i in range(6):
            date = timezone.now() - timedelta(days=30*i)
            month_start = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = month_start + timedelta(days=32)
            month_end = month_end.replace(day=1) - timedelta(seconds=1)
            
            care_group_growth_months.append(month_start.strftime('%b %Y'))
            
            # Count new members in care groups for this month
            month_new_members = CustomUser.objects.filter(
                church=user.church,
                regular_member_profile__group__in=led_groups,
                date_joined__gte=month_start,
                date_joined__lte=month_end,
                is_active=True
            ).count()
            care_group_growth_counts.append(month_new_members)
        
        care_group_growth_months.reverse()
        care_group_growth_counts.reverse()
        
        # Get group statistics with enhanced data
        group_stats = []
        total_group_members = 0
        
        for group in led_groups:
            member_count = group.member_count
            total_group_members += member_count
            
            # Get recent activities for this group
            recent_group_activities = ActivityLog.objects.filter(
                user__regular_member_profile__group=group,
                action__in=['GROUP_JOIN', 'GROUP_LEAVE', 'ATTENDANCE'],
                timestamp__gte=timezone.now() - timedelta(days=7)
            ).select_related('user')[:3]
            
            group_stats.append({
                'group': group,
                'member_count': member_count,
                'capacity_percentage': group.capacity_percentage,
                'is_full': group.is_full,
                'recent_activities': recent_group_activities
            })
        
        # Get recent group activities
        recent_group_activities = ActivityLog.objects.filter(
            user__church=user.church,
            action__in=['GROUP_JOIN', 'GROUP_LEAVE', 'ATTENDANCE'],
            timestamp__gte=timezone.now() - timedelta(days=7)
        ).select_related('user')[:10]
        
        # Get care group reports for this leader
        from members.models import CareGroupReport
        recent_reports = CareGroupReport.objects.filter(
            care_group__leader=user,
            church=user.church
        ).order_by('-date_of_cg')[:5]
        
        context.update({
            'led_groups': led_groups,
            'group_stats': group_stats,
            'total_group_members': total_group_members,
            'direct_members_count': direct_members_count,
            'nested_members_count': nested_members_count,
            'total_care_group_members': total_care_group_members,
            'role_distribution': role_distribution,
            'care_group_growth_months': care_group_growth_months,
            'care_group_growth_counts': care_group_growth_counts,
            'recent_group_activities': recent_group_activities,
            'recent_reports': recent_reports,
        })
        return render(request, 'churches/dashboard/leader_dashboard.html', context)
    
    # Regular member dashboard
    else:
        # Get user's group membership
        from members.models import RegularMember
        try:
            regular_profile = RegularMember.objects.get(user=user)
            user_group = regular_profile.group
        except RegularMember.DoesNotExist:
            user_group = None
        
        # Get user's recent activities
        user_activities = ActivityLog.objects.filter(
            user=user
        ).order_by('-timestamp')[:10]
        
        # Get attendance streak
        attendance_streak = 0
        if user.last_attendance:
            current_date = timezone.now().date()
            last_attendance_date = user.last_attendance.date()
            days_since = (current_date - last_attendance_date).days
            
            if days_since <= 7:  # Within a week
                attendance_streak = 1
                # Could implement more complex streak logic here
        
        context.update({
            'user_group': user_group,
            'user_activities': user_activities,
            'attendance_streak': attendance_streak,
        })
        return render(request, 'churches/dashboard/member_dashboard.html', context)


@login_required
def church_report(request):
    """Church Report with demographic statistics"""
    user = request.user
    
    # Check if user has permission to view church reports
    if not (user.is_superuser or user.role.name == 'ADMIN'):
        from django.contrib import messages
        messages.error(request, 'You do not have permission to view church reports.')
        return redirect('churches:dashboard')
    
    church = user.church
    
    # Get date range from request parameters
    from datetime import datetime, timedelta
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            start_date = None
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            end_date = None
    
    # Get demographic statistics
    demographic_stats = church.get_demographic_statistics()
    
    # Get Sunday attendance statistics
    sunday_attendance_stats = church.get_sunday_attendance_statistics(start_date, end_date)
    
    # Get 2025 target (this would typically come from church settings or be configurable)
    # For now, we'll calculate it as a percentage of current registered disciples
    current_total = demographic_stats['registered_disciples']['total']
    target_2025 = {
        'registered_disciples': int(current_total * 1.2),  # 20% growth target
        'youth_men': int(demographic_stats['registered_disciples']['youth_men'] * 1.2),
        'youth_women': int(demographic_stats['registered_disciples']['youth_women'] * 1.2),
        'men': int(demographic_stats['registered_disciples']['men'] * 1.2),
        'women': int(demographic_stats['registered_disciples']['women'] * 1.2),
    }
    
    # Get additional statistics
    total_members = church.total_members
    new_friends_count = church.new_friends_count
    regular_members_count = church.regular_members_count
    
    context = {
        'user': user,
        'church': church,
        'demographic_stats': demographic_stats,
        'sunday_attendance_stats': sunday_attendance_stats,
        'target_2025': target_2025,
        'total_members': total_members,
        'new_friends_count': new_friends_count,
        'regular_members_count': regular_members_count,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'churches/dashboard/church_report.html', context)


@login_required
def export_church_report_to_sheets(request):
    user = request.user
    
    if not (user.is_superuser or user.role.name == 'ADMIN'):
        from django.contrib import messages
        messages.error(request, 'You do not have permission to export church reports.')
        return redirect('churches:church_report')
    
    church = user.church
    
    from datetime import datetime
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            start_date = None
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            end_date = None
    
    demographic_stats = church.get_demographic_statistics()
    sunday_attendance_stats = church.get_sunday_attendance_statistics(start_date, end_date)
    
    current_total = demographic_stats['registered_disciples']['total']
    target_2025 = {
        'registered_disciples': int(current_total * 1.2),
        'youth_men': int(demographic_stats['registered_disciples']['youth_men'] * 1.2),
        'youth_women': int(demographic_stats['registered_disciples']['youth_women'] * 1.2),
        'men': int(demographic_stats['registered_disciples']['men'] * 1.2),
        'women': int(demographic_stats['registered_disciples']['women'] * 1.2),
    }
    
    try:
        from ..google_sheets import GoogleSheetsService
        sheets_service = GoogleSheetsService()
        spreadsheet_url = sheets_service.export_church_report(
            church, 
            demographic_stats, 
            sunday_attendance_stats, 
            target_2025
        )
        
        from django.contrib import messages
        messages.success(request, f'Church report exported to Google Sheets successfully!')
        return redirect(spreadsheet_url)
        
    except Exception as e:
        from django.contrib import messages
        messages.error(request, f'Failed to export to Google Sheets: {str(e)}')
        return redirect('churches:church_report')
