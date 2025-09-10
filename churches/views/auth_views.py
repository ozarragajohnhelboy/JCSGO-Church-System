from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db import transaction

from members.models import Church, CustomUser, NewFriend, ActivityLog
from churches.models import ChurchSettings
from ..forms import ChurchSelectionForm, ChurchLoginForm, ChurchRegistrationForm

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
    return render(request, 'churches/auth/church_selection.html', context)


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
    return render(request, 'churches/auth/church_login.html', context)


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
    return render(request, 'churches/auth/church_registration.html', context)


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
    
    return render(request, 'churches/auth/super_admin_login.html')


def custom_logout(request):
    """Custom logout view that logs out directly without confirmation"""
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('churches:church_selection')
