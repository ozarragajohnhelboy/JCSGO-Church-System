from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.urls import reverse
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from members.models import Church, Role, CustomUser, NewFriend, ActivityLog
from churches.models import ChurchSettings
from .forms import ChurchSelectionForm, ChurchLoginForm, ChurchRegistrationForm
from .utils import detect_church_from_email

User = get_user_model()


def church_selection(request):
    """Church selection page - first page users see"""
    if request.method == 'POST':
        form = ChurchSelectionForm(request.POST)
        if form.is_valid():
            church = form.cleaned_data['church']
            return redirect('churches:church_login', church_domain=church.domain)
    else:
        form = ChurchSelectionForm()
    
    # Get all active churches
    all_churches = Church.objects.filter(is_active=True).order_by('name')
    
    # Organize churches by sectors
    rizal_sector_churches = all_churches.filter(
        domain__in=['kasiglahan', 'sanjose', 'christinville', 'tabak']
    ).order_by('name')
    
    central_sector_churches = all_churches.filter(
        domain__in=['10amfamily', '3pmfamily']
    ).order_by('name')
    
    context = {
        'form': form,
        'all_churches': all_churches,
        'rizal_sector_churches': rizal_sector_churches,
        'central_sector_churches': central_sector_churches,
    }
    return render(request, 'churches/church_selection.html', context)


def church_login(request, church_domain):
    """Church-specific login page"""
    church = get_object_or_404(Church, domain=church_domain, is_active=True)
    
    if request.method == 'POST':
        form = ChurchLoginForm(request.POST, church=church)
        if form.is_valid():
            email_prefix = form.cleaned_data['email_prefix']
            password = form.cleaned_data['password']
            full_email = form.full_email
            user = authenticate(request, email=full_email, password=password)
            
            if user is not None and user.church == church:
                login(request, user)
                messages.success(request, f'Welcome back to {church.name}!')
                return redirect('churches:dashboard')
            else:
                messages.error(request, 'Invalid email or password for this church.')
    else:
        form = ChurchLoginForm(church=church)
    
    context = {
        'form': form,
        'church': church,
    }
    return render(request, 'churches/church_login.html', context)


def church_registration(request, church_domain):
    """Church-specific registration page"""
    church = get_object_or_404(Church, domain=church_domain, is_active=True)
    church_settings = get_object_or_404(ChurchSettings, church=church)
    
    if not church_settings.allow_public_registration:
        messages.error(request, 'Registration is not currently open for this church.')
        return redirect('churches:church_login', church_domain=church_domain)
    
    if request.method == 'POST':
        form = ChurchRegistrationForm(request.POST, church=church)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create user
                    user = form.save(commit=False)
                    user.church = church
                    user.save()
                    
                    # Create NewFriend profile
                    new_friend = NewFriend.objects.create(
                        user=user,
                        source=form.cleaned_data.get('source', ''),
                        notes=form.cleaned_data.get('notes', '')
                    )
                    
                    # Log the registration
                    ActivityLog.objects.create(
                        user=user,
                        action='REGISTER',
                        description=f'New user registration for {church.name}',
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                    
                    # Auto-login if no email verification required
                    if not church_settings.require_email_verification:
                        login(request, user)
                        messages.success(request, f'Welcome to {church.name}! Your account has been created successfully.')
                        return redirect('churches:dashboard')
                    else:
                        messages.success(request, f'Registration successful! Please check your email to verify your account.')
                        return redirect('churches:church_login', church_domain=church_domain)
                        
            except Exception as e:
                messages.error(request, f'Registration failed: {str(e)}')
    else:
        form = ChurchRegistrationForm(church=church)
    
    context = {
        'form': form,
        'church': church,
    }
    return render(request, 'churches/church_registration.html', context)


@login_required
def dashboard(request):
    """User dashboard based on role and church"""
    user = request.user
    
    # Get church-specific data
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
    
    # Get monthly growth data for charts
    from datetime import datetime, timedelta
    from django.db.models import Count
    from django.utils import timezone
    
    # Get date filter for recent activity
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
        return render(request, 'churches/super_admin_dashboard.html', context)
    
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
        return render(request, 'churches/admin_dashboard.html', context)
    
    # Church leader dashboard (VSL, CSL, CL)
    elif user.role.name in ['VSL', 'CSL', 'CL']:
        # Get groups led by this user
        from members.models import Group
        led_groups = Group.objects.filter(
            leader=user,
            church=user.church,
            is_active=True
        )
        
        # Get group statistics
        group_stats = []
        total_group_members = 0
        
        for group in led_groups:
            member_count = group.member_count
            total_group_members += member_count
            group_stats.append({
                'group': group,
                'member_count': member_count,
                'capacity_percentage': group.capacity_percentage,
                'is_full': group.is_full
            })
        
        # Get recent group activities
        recent_group_activities = ActivityLog.objects.filter(
            user__church=user.church,
            action__in=['GROUP_JOIN', 'GROUP_LEAVE'],
            timestamp__gte=timezone.now() - timedelta(days=7)
        ).select_related('user')[:5]
        
        context.update({
            'led_groups': led_groups,
            'group_stats': group_stats,
            'total_group_members': total_group_members,
            'recent_group_activities': recent_group_activities,
        })
        return render(request, 'churches/leader_dashboard.html', context)
    
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
        return render(request, 'churches/member_dashboard.html', context)





def super_admin_login(request):
    """Super admin login page"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            user = authenticate(request, email=email, password=password)
            if user and user.is_superuser:
                login(request, user)
                messages.success(request, f'Welcome back, {user.full_name}!')
                return redirect('churches:dashboard')
            else:
                messages.error(request, 'Invalid credentials or not a super admin.')
        except Exception as e:
            messages.error(request, f'Login failed: {str(e)}')
    
    return render(request, 'churches/super_admin_login.html')

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
        
        # Get group capacity data (limit to 5)
        from members.models import Group
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
        }
        
        return render(request, 'churches/church_dashboard_modal.html', context)
        
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


def custom_logout(request):
    """Custom logout view that logs out directly without confirmation"""
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('churches:church_selection')
