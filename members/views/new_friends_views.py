from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
import csv
import io

from ..models import CustomUser, NewFriend, RegularMember, Role, ActivityLog
from ..forms import NewFriendForm, NewFriendImportForm

User = get_user_model()


@login_required
def new_friend_add(request):
    """Add a new New Friend"""
    if not (request.user.is_superuser or request.user.role.name == 'ADMIN'):
        messages.error(request, 'You do not have permission to add new friends.')
        return redirect('members:new_friends_list')
    
    if request.method == 'POST':
        form = NewFriendForm(request.POST, church=request.user.church)
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
                        is_new_friend=True,
                        is_active=True,
                        password=default_password 
                    )
                    
                    try:
                        if hasattr(user, 'regular_member_profile'):
                            user.regular_member_profile.delete()
                    except RegularMember.DoesNotExist:
                        pass
                    
                    user.timer_status = form.cleaned_data['timer_status']
                    
                    birth_date_val = form.cleaned_data.get('birth_date')
                    gender_val = form.cleaned_data.get('gender')
                    
                    if birth_date_val:
                        user.birth_date = birth_date_val
                    if gender_val:
                        user.gender = gender_val
                    
                    user.save()

                    new_friend = NewFriend.objects.create(
                        user=user,
                        invited_by=form.cleaned_data['invited_by'],
                        endorsed_to=form.cleaned_data['endorsed_to'],
                        notes=form.cleaned_data['notes']
                    )
                    
                    endorsed_to_user = form.cleaned_data['endorsed_to']
                    if endorsed_to_user and endorsed_to_user.role and endorsed_to_user.role.name == 'CM':
                        cl_role = Role.objects.get(name='CL')
                        endorsed_to_user.role = cl_role
                        endorsed_to_user.save()
                        
                        if hasattr(endorsed_to_user, 'regular_member_profile') and endorsed_to_user.regular_member_profile:
                            endorsed_to_user.regular_member_profile.role_type = 'CL'
                            endorsed_to_user.regular_member_profile.save()

                        ActivityLog.objects.create(
                            user=request.user,
                            action='ROLE_PROMOTED',
                            description=f'Promoted {endorsed_to_user.full_name} from CM to CL due to new friend endorsement',
                            related_user=endorsed_to_user,
                            ip_address=request.META.get('REMOTE_ADDR'),
                            user_agent=request.META.get('HTTP_USER_AGENT', '')
                        )

                        messages.info(request, f'{endorsed_to_user.full_name} has been automatically promoted from CM to CL due to new friend endorsement.')

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
    return render(request, 'members/forms/new_friend_form.html', context)


@login_required
def new_friend_edit(request, new_friend_id):
    """Edit a New Friend"""

    if not (request.user.is_superuser or request.user.role.name == 'ADMIN'):
        messages.error(request, 'You do not have permission to edit new friends.')
        return redirect('members:new_friends_list')
    
    new_friend = get_object_or_404(NewFriend, id=new_friend_id, user__church=request.user.church)
    
    if request.method == 'POST':
        form = NewFriendForm(request.POST, instance=new_friend, church=request.user.church)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = new_friend.user
                    user.first_name = form.cleaned_data['first_name']
                    user.last_name = form.cleaned_data['last_name']
                    user.phone_number = form.cleaned_data['phone']
                    user.timer_status = form.cleaned_data['timer_status']
                    
                    birth_date_val = form.cleaned_data.get('birth_date')
                    gender_val = form.cleaned_data.get('gender')
                    
                    if birth_date_val:
                        user.birth_date = birth_date_val
                    if gender_val:
                        user.gender = gender_val
                    
                    user.save()

                    new_friend.invited_by = form.cleaned_data['invited_by']
                    new_friend.endorsed_to = form.cleaned_data['endorsed_to']
                    new_friend.notes = form.cleaned_data['notes']
                    new_friend.save()

                    endorsed_to_user = form.cleaned_data['endorsed_to']
                    if endorsed_to_user and endorsed_to_user.role and endorsed_to_user.role.name == 'CM':
                        cl_role = Role.objects.get(name='CL')
                        endorsed_to_user.role = cl_role
                        endorsed_to_user.save()

                        if hasattr(endorsed_to_user, 'regular_member_profile') and endorsed_to_user.regular_member_profile:
                            endorsed_to_user.regular_member_profile.role_type = 'CL'
                            endorsed_to_user.regular_member_profile.save()

                        ActivityLog.objects.create(
                            user=request.user,
                            action='ROLE_PROMOTED',
                            description=f'Promoted {endorsed_to_user.full_name} from CM to CL due to new friend endorsement',
                            related_user=endorsed_to_user,
                            ip_address=request.META.get('REMOTE_ADDR'),
                            user_agent=request.META.get('HTTP_USER_AGENT', '')
                        )

                        messages.info(request, f'{endorsed_to_user.full_name} has been automatically promoted from CM to CL due to new friend endorsement.')

                    if form.cleaned_data.get('convert_to_regular') and form.cleaned_data.get('regular_role'):
                        selected_role_name = form.cleaned_data['regular_role']
                        user.is_new_friend = False
                        user.transition_date = timezone.now()
                        role = get_object_or_404(Role, name=selected_role_name)
                        user.role = role
                        user.save()

                        RegularMember.objects.get_or_create(
                            user=user,
                            defaults={'role_type': selected_role_name}
                        )

                        try:
                            if hasattr(user, 'new_friend_profile'):
                                user.new_friend_profile.delete()
                        except NewFriend.DoesNotExist:
                            pass

                        ActivityLog.objects.create(
                            user=request.user,
                            action='STATUS_CHANGE',
                            description=f'Transitioned {user.full_name} from New Friend to Regular Member',
                            related_user=user,
                            ip_address=request.META.get('REMOTE_ADDR'),
                            user_agent=request.META.get('HTTP_USER_AGENT', '')
                        )

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
        form = NewFriendForm(instance=new_friend, church=request.user.church)
        email_prefix = new_friend.user.email.split('@')[0] if '@' in new_friend.user.email else new_friend.user.email
        form.fields['email_prefix'].initial = email_prefix
        form.fields['first_name'].initial = new_friend.user.first_name
        form.fields['last_name'].initial = new_friend.user.last_name
        form.fields['phone'].initial = new_friend.user.phone_number
        form.fields['birth_date'].initial = new_friend.user.birth_date
        form.fields['gender'].initial = new_friend.user.gender
        form.fields['invited_by'].initial = new_friend.invited_by
        form.fields['endorsed_to'].initial = new_friend.endorsed_to
        form.fields['timer_status'].initial = new_friend.user.timer_status
    
    context = {
        'form': form,
        'new_friend': new_friend,
        'title': 'Edit New Friend',
        'church': request.user.church
    }
    return render(request, 'members/forms/new_friend_form.html', context)


@login_required
@require_POST
def new_friend_delete(request, new_friend_id):
    """Delete a New Friend"""
    if not (request.user.is_superuser or request.user.role.name == 'ADMIN'):
        messages.error(request, 'You do not have permission to delete new friends.')
        return redirect('members:new_friends_list')
    
    new_friend = get_object_or_404(NewFriend, id=new_friend_id, user__church=request.user.church)
    user_name = new_friend.user.full_name
    
    try:
        with transaction.atomic():
            ActivityLog.objects.create(
                user=request.user,
                action='NEW_FRIEND_DELETED',
                description=f'Deleted new friend: {user_name}',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            new_friend.user.delete()
            
            messages.success(request, f'New friend "{user_name}" has been deleted successfully!')
            
    except Exception as e:
        messages.error(request, f'Error deleting new friend: {str(e)}')
    
    return redirect('members:new_friends_list')


@login_required
def new_friend_import(request):
    """Import New Friends from CSV/Excel"""
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
                    decoded_file = file.read().decode('utf-8')
                    csv_data = csv.DictReader(io.StringIO(decoded_file))
                    
                    for row_num, row in enumerate(csv_data, start=2):
                        try:
                            with transaction.atomic():
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
                                    is_new_friend=True,
                                    is_active=True,
                                    password=default_password 
                                )

                                try:
                                    if hasattr(user, 'regular_member_profile'):
                                        user.regular_member_profile.delete()
                                except RegularMember.DoesNotExist:
                                    pass

                                user.timer_status = int(row.get('timer_status', 1))
                                user.save()

                                NewFriend.objects.create(
                                    user=user,
                                    invited_by=None,  
                                    endorsed_to=None,
                                    notes=row.get('notes', '').strip() or ''
                                )
                                
                                imported_count += 1
                                
                        except Exception as e:
                            errors.append(f"Row {row_num}: {str(e)}")
                
                if imported_count > 0:
                    messages.success(request, f'Successfully imported {imported_count} new friends!')

                    ActivityLog.objects.create(
                        user=request.user,
                        action='NEW_FRIENDS_IMPORTED',
                        description=f'Imported {imported_count} new friends from {file.name}',
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                
                if errors:
                    for error in errors[:5]:
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
    return render(request, 'members/forms/new_friend_import.html', context)
