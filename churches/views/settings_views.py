from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from churches.models import ChurchSettings
from churches.settings_forms import ChurchRegistrationSettingsForm, StyledPasswordChangeForm


def _is_church_admin(user):
    role_name = user.role.name if getattr(user, 'role', None) else None
    return role_name == 'ADMIN' and bool(getattr(user, 'church_id', None))


@login_required
def account_settings(request):
    user = request.user
    can_manage_church = _is_church_admin(user)
    church_settings = None
    church_form = None

    if can_manage_church:
        church_settings, _created = ChurchSettings.objects.get_or_create(church=user.church)

    if request.method == 'POST':
        which = request.POST.get('form')
        if which == 'password':
            password_form = StyledPasswordChangeForm(user, request.POST)
            if can_manage_church:
                church_form = ChurchRegistrationSettingsForm(instance=church_settings)
            if password_form.is_valid():
                password_form.save()
                update_session_auth_hash(request, password_form.user)
                messages.success(request, 'Password updated.')
                return redirect('churches:account_settings')
        elif which == 'church' and can_manage_church:
            password_form = StyledPasswordChangeForm(user)
            church_form = ChurchRegistrationSettingsForm(request.POST, instance=church_settings)
            if church_form.is_valid():
                settings_obj = church_form.save(commit=False)
                settings_obj.church = user.church
                settings_obj.save()
                messages.success(request, 'Church settings updated.')
                return redirect('churches:account_settings')
        else:
            messages.error(request, 'You do not have permission to change those settings.')
            return redirect('churches:account_settings')
    else:
        password_form = StyledPasswordChangeForm(user)
        if can_manage_church:
            church_form = ChurchRegistrationSettingsForm(instance=church_settings)

    return render(request, 'churches/settings/account_settings.html', {
        'password_form': password_form,
        'church_form': church_form,
        'can_manage_church': can_manage_church,
    })
