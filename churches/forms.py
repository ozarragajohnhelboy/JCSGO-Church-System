from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from members.models import Church, Role, NewFriend
from .utils import detect_church_from_email

User = get_user_model()


class ChurchSelectionForm(forms.Form):
    """Form for selecting a church"""
    church = forms.ModelChoiceField(
        queryset=Church.objects.filter(is_active=True).order_by('name'),
        empty_label="Select your church",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'church-select'
        })
    )


class ChurchLoginForm(forms.Form):
    """Church-specific login form"""
    email_prefix = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your username (e.g., johnhb)',
            'id': 'login-email-prefix'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.church = kwargs.pop('church', None)
        super().__init__(*args, **kwargs)
    
    def clean_email_prefix(self):
        email_prefix = self.cleaned_data['email_prefix']
        if self.church:
            # Create full email from email_prefix and church domain
            full_email = f"{email_prefix}@{self.church.domain}.jcsgo.com"
            
            # Check if user exists and belongs to this church
            try:
                user = User.objects.get(email=full_email)
                if user.church != self.church:
                    raise ValidationError(
                        f'This username is registered with {user.church.name}, not {self.church.name}.'
                    )
            except User.DoesNotExist:
                pass  # User doesn't exist, which is fine for login form
            
            # Store the full email for later use
            self.full_email = full_email
        
        return email_prefix


class ChurchRegistrationForm(UserCreationForm):
    """Church-specific registration form"""
    email_prefix = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your username (e.g., johnhb)',
            'id': 'email-prefix'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        })
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your phone number (optional)'
        })
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter your address (optional)'
        }),
        required=False
    )
    birth_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    
    role = forms.ChoiceField(
        choices=[
            ('NEW_FRIEND', 'New Friend (1st-5th timer)'),
            ('CM', 'Cell Member (CM)'),
            ('CL', 'Cell Leader (CL)'),
            ('CSL', 'Cell Servant Leader (CSL)'),
            ('VSL', 'Vision Servant Leader (VSL)'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'placeholder': 'Select your role'
        }),
        initial='NEW_FRIEND',
        help_text='Select your current role in the church'
    )
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        self.church = kwargs.pop('church', None)
        super().__init__(*args, **kwargs)
        
        # Remove email field from display since we'll generate it
        if 'email' in self.fields:
            del self.fields['email']
        
        # Customize password fields
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })
        
        # Get NEW_FRIEND role
        try:
            new_friend_role = Role.objects.get(name='NEW_FRIEND')
            self.initial['role'] = new_friend_role
        except Role.DoesNotExist:
            pass
    
    def clean_email_prefix(self):
        email_prefix = self.cleaned_data['email_prefix']
        
        # Validate email prefix format
        if not email_prefix.isalnum():
            raise ValidationError('Username can only contain letters and numbers.')
        
        if len(email_prefix) < 3:
            raise ValidationError('Username must be at least 3 characters long.')
        
        # Create full email
        if self.church:
            full_email = f"{email_prefix}@{self.church.domain}.jcsgo.com"
            
            # Check if email already exists
            if User.objects.filter(email=full_email).exists():
                raise ValidationError('This username is already taken.')
            
            # Store the full email for later use
            self.full_email = full_email
        
        return email_prefix
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Set email from email_prefix and church domain
        user.email = self.full_email
        
        # Set church and role
        user.church = self.church
        selected_role = self.cleaned_data.get('role', 'NEW_FRIEND')
        user.role = Role.objects.get(name=selected_role)
        
        # Set new friend status based on role
        if selected_role == 'NEW_FRIEND':
            user.is_new_friend = True
            user.timer_status = 1
        else:
            user.is_new_friend = False
            user.timer_status = 5  # Regular members have completed 5+ visits
        
        if commit:
            user.save()
        return user


class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile"""
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone_number', 'address', 'birth_date', 'profile_picture')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        } 