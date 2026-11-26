from django import forms
from django.contrib.auth.forms import PasswordChangeForm

from churches.models import ChurchSettings


class StyledPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels = {
            'old_password': 'Current password',
            'new_password1': 'New password',
            'new_password2': 'Confirm new password',
        }
        for name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            if name in labels:
                field.label = labels[name]


class ChurchRegistrationSettingsForm(forms.ModelForm):
    class Meta:
        model = ChurchSettings
        fields = ('allow_public_registration', 'require_email_verification')
        labels = {
            'allow_public_registration': 'Allow public registration',
            'require_email_verification': 'Require email verification before login',
        }
        widgets = {
            'allow_public_registration': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'require_email_verification': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
