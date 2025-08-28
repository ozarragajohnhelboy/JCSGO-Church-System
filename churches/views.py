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
    
    # Group churches by region
    region_4a_churches = Church.objects.filter(
        domain__in=['kasiglahan', 'sanjose', 'christinville', 'tabak']
    ).order_by('name')
    
    central_region_churches = Church.objects.filter(
        domain__in=['10amfamily', '3pmfamily']
    ).order_by('name')
    
    context = {
        'form': form,
        'region_4a_churches': region_4a_churches,
        'central_region_churches': central_region_churches,
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
    
    # Get recent activity
    recent_activity = ActivityLog.objects.filter(
        user__church=user.church
    ).select_related('user')[:10]
    
    context = {
        'user': user,
        'church': user.church,
        'new_friends_count': new_friends_count,
        'regulars_count': regulars_count,
        'total_members': total_members,
        'recent_activity': recent_activity,
    }
    
    # Super admin dashboard
    if user.is_superuser:
        # Get all churches data for super admin
        all_churches = Church.objects.filter(is_active=True).order_by('name')
        
        # Get church stats for super admin
        church_stats = []
        for church in all_churches:
            church_new_friends = CustomUser.objects.filter(
                church=church, is_new_friend=True, is_active=True
            ).count()
            church_regulars = CustomUser.objects.filter(
                church=church, is_new_friend=False, is_active=True
            ).count()
            church_stats.append({
                'church': church,
                'total_members': church_new_friends + church_regulars,
                'new_friends': church_new_friends,
                'regular_members': church_regulars,
            })
        
        context.update({
            'churches': all_churches,
            'church_stats': church_stats,
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
        
        # Get active groups count (placeholder for now)
        active_groups_count = 0  # Will be implemented in Phase 2
        
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
        })
        return render(request, 'churches/admin_dashboard.html', context)
    
    # Church leader dashboard
    elif user.role.name == 'CHURCH_LEADER':
        # Get groups count for church leader
        from members.models import Group
        active_groups_count = Group.objects.filter(
            church=user.church, is_active=True
        ).count()
        
        context['active_groups_count'] = active_groups_count
        return render(request, 'churches/leader_dashboard.html', context)
    
    # Regular member dashboard
    else:
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
        
        # Get recent activity
        recent_activity = ActivityLog.objects.filter(
            user__church=church
        ).select_related('user')[:5]
        
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
