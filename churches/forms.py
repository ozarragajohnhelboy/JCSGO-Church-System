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
            ('CM', 'Care Member (CM)'),
            ('CL', 'Care Leader (CL)'),
            ('CSL', 'Cluster Servant Leader (CSL)'),
            ('VSL', 'Vine Servant Leader (VSL)'),
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


class ChurchForm(forms.ModelForm):
    """Form for adding/editing churches"""
    sector_choice = forms.ChoiceField(
        choices=[],  # Will be populated in __init__
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'sector-choice'}),
        label='Sector'
    )
    new_sector_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new sector name',
            'id': 'new-sector-name'
        }),
        label='New Sector Name'
    )
    
    class Meta:
        model = Church
        fields = ['name', 'location', 'sector', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter church name'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter church location'}),
            'sector': forms.HiddenInput(),  # Hidden field to store the actual sector value
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['location'].required = True
        self.fields['is_active'].initial = True
        # Make sector field not required since we handle it in clean()
        self.fields['sector'].required = False
        
        # Get existing sectors from all churches
        existing_sectors = Church.objects.values_list('sector', flat=True).distinct().order_by('sector')
        
        # Create choices for sector dropdown
        sector_choices = [('', 'Select a sector...')]
        for sector in existing_sectors:
            if sector:  # Skip empty sectors
                sector_choices.append((sector, sector))
        sector_choices.append(('__new__', 'Add New Sector'))
        
        self.fields['sector_choice'].choices = sector_choices
        
        # Set initial value for editing
        if self.instance.pk and self.instance.sector:
            self.fields['sector_choice'].initial = self.instance.sector
    
    def clean(self):
        cleaned_data = super().clean()
        sector_choice = cleaned_data.get('sector_choice')
        new_sector_name = cleaned_data.get('new_sector_name')
        church_name = cleaned_data.get('name')
        
        # Handle sector selection
        if sector_choice == '__new__':
            if not new_sector_name:
                raise forms.ValidationError('Please enter a name for the new sector.')
            # Set the sector field to the new sector name
            cleaned_data['sector'] = new_sector_name.strip()
        elif sector_choice:
            # Set the sector field to the selected existing sector
            cleaned_data['sector'] = sector_choice
        
        # Auto-generate domain from church name
        if church_name:
            # Remove "JCSGO" prefix and get the rest
            name_parts = church_name.strip()
            if name_parts.upper().startswith('JCSGO'):
                # Remove "JCSGO" and any following spaces
                name_parts = name_parts[5:].strip()
            
            # Convert to lowercase and remove spaces (join all words together)
            domain = name_parts.lower().replace(' ', '')
            # Remove special characters, keep only alphanumeric
            domain = ''.join(c for c in domain if c.isalnum())
            
            # Ensure domain is not empty
            if not domain:
                domain = 'church'
            
            # Check if domain already exists and make it unique if needed
            base_domain = domain
            counter = 1
            while Church.objects.filter(domain=domain).exclude(pk=self.instance.pk if self.instance.pk else None).exists():
                domain = f"{base_domain}{counter}"
                counter += 1
            
            # Set the domain field (this will be saved to the model)
            cleaned_data['domain'] = domain
        
        return cleaned_data
    
    def save(self, commit=True):
        """Override save to ensure domain is set"""
        instance = super().save(commit=False)
        
        # Ensure domain is set from cleaned_data
        if hasattr(self, 'cleaned_data') and 'domain' in self.cleaned_data:
            instance.domain = self.cleaned_data['domain']
        
        if commit:
            instance.save()
        return instance


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