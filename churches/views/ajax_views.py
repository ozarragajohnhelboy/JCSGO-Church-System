from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, datetime

from members.models import Church, Role, CustomUser, ActivityLog
from ..utils import detect_church_from_email

User = get_user_model()


@csrf_exempt
def ajax_church_dashboard(request, church_domain):
    """AJAX endpoint to load church dashboard content for super admin"""
    if not request.user.is_authenticated or not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        church = get_object_or_404(Church, domain=church_domain, is_active=True)
        
        # Get church-specific data
        new_friends_count = CustomUser.objects.filter(
            church=church, is_new_friend=True, is_active=True
        ).count()
        
        regulars_count = CustomUser.objects.filter(
            church=church, is_new_friend=False, is_active=True
        ).count()
        
        total_members = new_friends_count + regulars_count
        
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
        
        # Get monthly member growth data (new friends and regulars)
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
                church=church,
                is_new_friend=True,
                date_joined__gte=month_start,
                date_joined__lte=month_end,
                is_active=True
            ).count()
            new_friends_monthly.append(month_new_friends)
            
            # Count regular members for this month
            month_regulars = CustomUser.objects.filter(
                church=church,
                is_new_friend=False,
                date_joined__gte=month_start,
                date_joined__lte=month_end,
                is_active=True
            ).count()
            regulars_monthly.append(month_regulars)
        
        # Reverse to show oldest to newest
        months.reverse()
        new_friends_monthly.reverse()
        regulars_monthly.reverse()
        
        # Get role distribution data
        role_distribution = []
        roles = Role.objects.filter(name__in=['VSL', 'CSL', 'CL', 'CM'])
        for role in roles:
            count = CustomUser.objects.filter(
                church=church,
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
        
        # Get date filter for recent activity
        activity_date_filter = request.GET.get('activity_date', '')
        
        # Get recent activity with date filter
        recent_activity_query = ActivityLog.objects.filter(user__church=church)
        
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
        
        context = {
            'church': church,
            'new_friends_count': new_friends_count,
            'regulars_count': regulars_count,
            'total_members': total_members,
            'vsl_count': vsl_count,
            'csl_count': csl_count,
            'cl_count': cl_count,
            'cm_count': cm_count,
            'vsl_percentage': vsl_percentage,
            'csl_percentage': csl_percentage,
            'cl_percentage': cl_percentage,
            'cm_percentage': cm_percentage,
            'recent_activity': recent_activity,
            'activity_date_filter': activity_date_filter,
            'group_capacity_data': group_capacity_data,
            'months': months,
            'new_friends_monthly': new_friends_monthly,
            'regulars_monthly': regulars_monthly,
            'role_distribution': role_distribution,
            'transition_months': transition_months,
            'transition_counts': transition_counts,
            'current_month_transitions': current_month_transitions,
            'transition_rate': transition_rate,
            'active_groups_count': active_groups_count,
        }
        
        return render(request, 'churches/modals/church_dashboard_modal.html', context)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def ajax_church_detection(request):
    """AJAX endpoint for church detection from email"""
    if request.method == 'POST':
        email = request.POST.get('email', '')
        church_domain = detect_church_from_email(email)
        
        if church_domain:
            try:
                church = Church.objects.get(domain=church_domain, is_active=True)
                return JsonResponse({
                    'success': True,
                    'church_name': church.name,
                    'church_domain': church.domain,
                })
            except Church.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Church not found'
                })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Please use a valid church email address'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})
