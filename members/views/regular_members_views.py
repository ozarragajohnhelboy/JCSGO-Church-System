from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from django.db import transaction
import csv
import io

from ..models import CustomUser, NewFriend, RegularMember, Role, Group, ActivityLog
from ..forms import RegularMemberForm, RegularMemberImportForm

User = get_user_model()


@login_required
def regular_member_add(request):
    """Add a new Regular Member"""
    if not (request.user.is_superuser or request.user.role.name == 'ADMIN'):
        messages.error(request, 'You do not have permission to add regular members.')
        return redirect('members:regular_members_list')
    
    if request.method == 'POST':
        form = RegularMemberForm(request.POST, church=request.user.church)
        if form.is_valid():
            try:
                with transaction.atomic():
                    default_password = f"jcsgo{request.user.church.domain}"
                    user = CustomUser.objects.create_user(
                        email=form.full_email,
                        first_name=form.cleaned_data['first_name'],
                        last_name=form.cleaned_data['last_name'],
                        phone_number=form.cleaned_data['phone'],
                        church=request.user.church,
                        is_new_friend=False,
                        is_active=True,
                        password=default_password
                    )

                    user.role = form.cleaned_data['role']
                    user.save()

                    try:
                        if hasattr(user, 'new_friend_profile'):
                            user.new_friend_profile.delete()
                    except NewFriend.DoesNotExist:
                        pass

                    regular_member = RegularMember.objects.create(
                        user=user,
                        role_type=form.cleaned_data['role'].name,
                        group=form.cleaned_data['group']
                    )

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
    return render(request, 'members/forms/regular_member_form.html', context)


@login_required
def regular_member_edit(request, regular_member_id):
    """Edit a Regular Member"""
    if not (request.user.is_superuser or request.user.role.name == 'ADMIN'):
        messages.error(request, 'You do not have permission to edit regular members.')
        return redirect('members:regular_members_list')
    
    regular_member = get_object_or_404(RegularMember, id=regular_member_id, user__church=request.user.church)
    
    if request.method == 'POST':
        form = RegularMemberForm(request.POST, instance=regular_member, church=request.user.church)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = regular_member.user
                    user.first_name = form.cleaned_data['first_name']
                    user.last_name = form.cleaned_data['last_name']
                    user.phone_number = form.cleaned_data['phone']
                    user.role = form.cleaned_data['role']
                    user.save()
                    
                    regular_member.role_type = form.cleaned_data['role'].name
                    regular_member.group = form.cleaned_data['group']
                    regular_member.save()
                    
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
        form = RegularMemberForm(instance=regular_member, church=request.user.church)
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
    return render(request, 'members/forms/regular_member_form.html', context)


@login_required
@require_POST
def regular_member_delete(request, regular_member_id):
    """Delete a Regular Member"""
    if not (request.user.is_superuser or request.user.role.name == 'ADMIN'):
        messages.error(request, 'You do not have permission to delete regular members.')
        return redirect('members:regular_members_list')
    
    regular_member = get_object_or_404(RegularMember, id=regular_member_id, user__church=request.user.church)
    user_name = regular_member.user.full_name
    
    try:
        with transaction.atomic():
            ActivityLog.objects.create(
                user=request.user,
                action='REGULAR_MEMBER_DELETED',
                description=f'Deleted regular member: {user_name}',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )

            regular_member.user.delete()
            
            messages.success(request, f'Regular member "{user_name}" has been deleted successfully!')
            
    except Exception as e:
        messages.error(request, f'Error deleting regular member: {str(e)}')
    
    return redirect('members:regular_members_list')


@login_required
def regular_member_import(request):
    """Import Regular Members from CSV/Excel"""
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
                    decoded_file = file.read().decode('utf-8')
                    csv_data = csv.DictReader(io.StringIO(decoded_file))
                    
                    for row_num, row in enumerate(csv_data, start=2):  
                        try:
                            with transaction.atomic():
                                role_name = row.get('role', 'CM').strip().upper()
                                role, created = Role.objects.get_or_create(name=role_name)

                                group = None
                                if row.get('group'):
                                    group_name = row.get('group', '').strip()
                                    group, created = Group.objects.get_or_create(
                                        name=group_name,
                                        church=request.user.church,
                                        defaults={'is_active': True}
                                    )

                                email_prefix = row.get('email_prefix', '').strip()
                                if not email_prefix:
                                    email = row.get('email', '').strip()
                                    if '@' in email:
                                        email_prefix = email.split('@')[0]
                                    else:
                                        email_prefix = email
                                
                                full_email = f"{email_prefix}@{request.user.church.domain}.jcsgo.com"

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
                                    password=default_password  
                                )
                                
                                try:
                                    if hasattr(user, 'new_friend_profile'):
                                        user.new_friend_profile.delete()
                                except NewFriend.DoesNotExist:
                                    pass
                                
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

                    ActivityLog.objects.create(
                        user=request.user,
                        action='REGULAR_MEMBERS_IMPORTED',
                        description=f'Imported {imported_count} regular members from {file.name}',
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                
                if errors:
                    for error in errors[:5]:
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
    return render(request, 'members/forms/regular_member_import.html', context)
