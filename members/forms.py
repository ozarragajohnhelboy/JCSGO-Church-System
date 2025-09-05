from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate, get_user_model
from .models import CustomUser, NewFriend, RegularMember, Group, Role, Church, Attendance
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime
import csv
import io

User = get_user_model()


class CustomUserForm(forms.ModelForm):
    """Form for creating/editing users"""
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'email', 'church', 'role',
            'phone_number', 'address', 'birth_date', 'profile_picture',
            'is_new_friend', 'timer_status', 'is_active'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'church': forms.Select(attrs={'class': 'form-select'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'timer_status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter churches and roles based on user permissions
        if 'church' in self.fields:
            self.fields['church'].queryset = Church.objects.filter(is_active=True)
        if 'role' in self.fields:
            self.fields['role'].queryset = Role.objects.filter(is_active=True)


class NewFriendForm(forms.ModelForm):
    """Form for adding/editing New Friends"""
    email_prefix = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username (e.g., johnhb)',
            'id': 'new-friend-email-prefix'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter first name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter last name'
        })
    )
    phone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter phone number'
        })
    )
    invited_by = forms.ModelChoiceField(
        queryset=CustomUser.objects.none(),
        required=False,
        empty_label="Select who invited this person",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    endorsed_to = forms.ModelChoiceField(
        queryset=CustomUser.objects.none(),
        required=False,
        empty_label="Select who will follow up with this person",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.church = kwargs.pop('church', None)
        super().__init__(*args, **kwargs)
        
        # Populate invited_by field with regular members from the same church
        if self.church:
            self.fields['invited_by'].queryset = CustomUser.objects.filter(
                church=self.church,
                is_active=True,
                is_new_friend=False  # Only regular members can invite
            ).order_by('first_name', 'last_name')
            
            # Populate endorsed_to field with VSL, CSL, CL from the same church
            self.fields['endorsed_to'].queryset = CustomUser.objects.filter(
                church=self.church,
                is_active=True,
                is_new_friend=False,
                role__name__in=['VSL', 'CSL', 'CL']  # Only leadership roles can be endorsed to
            ).order_by('first_name', 'last_name')
            
            # Custom label to show only names, not emails
            self.fields['invited_by'].label_from_instance = lambda obj: obj.full_name
            self.fields['endorsed_to'].label_from_instance = lambda obj: f"{obj.full_name} ({obj.role.get_name_display()})"
        
        # Limit regular_role choices to VSL, CSL, CL, CM (exclude admin, super, new_friend)
        role_choices = Role.ROLE_CHOICES[2:-1]
        self.fields['regular_role'].choices = role_choices
    notes = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Additional notes about this person'
        })
    )
    timer_status = forms.ChoiceField(
        choices=[
            (1, '1st Timer'),
            (2, '2nd Timer'),
            (3, '3rd Timer'),
            (4, '4th Timer'),
            (5, '5th Timer'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    convert_to_regular = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    regular_role = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = NewFriend
        fields = ['email_prefix', 'first_name', 'last_name', 'phone', 'invited_by', 'endorsed_to', 'notes', 'timer_status', 'convert_to_regular', 'regular_role']
    
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
            
            # Check if email already exists (exclude current user if editing)
            existing_users = CustomUser.objects.filter(email=full_email)
            if self.instance and self.instance.user:
                existing_users = existing_users.exclude(pk=self.instance.user.pk)
            
            if existing_users.exists():
                raise ValidationError('This username is already taken.')
            
            # Store the full email for later use
            self.full_email = full_email
        
        return email_prefix

    def clean(self):
        cleaned = super().clean()
        convert = cleaned.get('convert_to_regular')
        role = cleaned.get('regular_role')
        if convert and not role:
            raise ValidationError('Please select a role for the regular member.')
        return cleaned


class RegularMemberForm(forms.ModelForm):
    """Form for adding/editing Regular Members"""
    email_prefix = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username (e.g., johnhb)',
            'id': 'regular-member-email-prefix'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter first name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter last name'
        })
    )
    phone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter phone number'
        })
    )
    role = forms.ModelChoiceField(
        queryset=Role.objects.filter(name__in=['VSL', 'CSL', 'CL', 'CM']),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    group = forms.ModelChoiceField(
        queryset=Group.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    class Meta:
        model = RegularMember
        fields = ['email_prefix', 'first_name', 'last_name', 'phone', 'role', 'group']
    
    def __init__(self, *args, **kwargs):
        self.church = kwargs.pop('church', None)
        super().__init__(*args, **kwargs)
        if self.church:
            self.fields['group'].queryset = Group.objects.filter(church=self.church, is_active=True)
    
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
            
            # Check if email already exists (exclude current user if editing)
            existing_users = CustomUser.objects.filter(email=full_email)
            if self.instance and self.instance.user:
                existing_users = existing_users.exclude(pk=self.instance.user.pk)
            
            if existing_users.exists():
                raise ValidationError('This username is already taken.')
            
            # Store the full email for later use
            self.full_email = full_email
        
        return email_prefix


class GroupForm(forms.ModelForm):
    """Form for creating/editing groups"""
    class Meta:
        model = Group
        fields = [
            'name', 'group_type', 'leader', 'description', 
            'meeting_schedule', 'meeting_location', 'max_members',
            'meeting_day', 'meeting_time', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'group_type': forms.Select(attrs={'class': 'form-select'}),
            'leader': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'meeting_schedule': forms.TextInput(attrs={'class': 'form-control'}),
            'meeting_location': forms.TextInput(attrs={'class': 'form-control'}),
            'max_members': forms.NumberInput(attrs={'class': 'form-control'}),
            'meeting_day': forms.Select(attrs={'class': 'form-select'}),
            'meeting_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        self.church = kwargs.pop('church', None)
        super().__init__(*args, **kwargs)
        
        if self.church and 'leader' in self.fields:
            self.fields['leader'].queryset = CustomUser.objects.filter(
                church=self.church, 
                is_active=True,
                is_new_friend=False  # Only regular members can be leaders
            )

    def clean_max_members(self):
        max_members = self.cleaned_data.get('max_members')
        if max_members and max_members < 1:
            raise ValidationError('Maximum members must be at least 1.')
        return max_members


class ProfileUpdateForm(forms.ModelForm):
    """Form for users to update their own profile"""
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'phone_number', 'address', 
            'birth_date', 'profile_picture'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make fields required for profile updates
        for field in self.fields.values():
            field.required = True


class CareGroupForm(forms.ModelForm):
    """Form for creating/editing care groups - specifically for VSL, CSL, CL roles"""
    class Meta:
        model = Group
        fields = [
            'name', 'description', 'meeting_schedule', 'meeting_location', 
            'max_members', 'meeting_day', 'meeting_time', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter care group name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe the care group purpose and goals'}),
            'meeting_schedule': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Weekly Bible Study'}),
            'meeting_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Church Hall or Member\'s Home'}),
            'max_members': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 50, 'value': 12}),
            'meeting_day': forms.Select(attrs={'class': 'form-select'}),
            'meeting_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        self.church = kwargs.pop('church', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        care_group = super().save(commit=False)
        care_group.group_type = 'CARE'  # Force care group type
        care_group.leader = self.user
        care_group.church = self.church
        if commit:
            care_group.save()
        return care_group

    def clean_max_members(self):
        max_members = self.cleaned_data.get('max_members')
        if max_members and max_members < 1:
            raise ValidationError('Maximum members must be at least 1.')
        if max_members and max_members > 50:
            raise ValidationError('Maximum members cannot exceed 50 for care groups.')
        return max_members


class CareGroupMemberForm(forms.Form):
    """Form for adding members to care groups"""
    member = forms.ModelChoiceField(
        queryset=CustomUser.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Select a regular member to add to this care group"
    )

    def __init__(self, *args, **kwargs):
        self.church = kwargs.pop('church', None)
        self.group = kwargs.pop('group', None)
        super().__init__(*args, **kwargs)
        
        if self.church:
            # Get available regular members who are not in any care group yet
            available_members = CustomUser.objects.filter(
                church=self.church,
                is_active=True,
                is_new_friend=False,
                role__name__in=['VSL', 'CSL', 'CL', 'CM']
            ).exclude(
                regular_member_profile__group__isnull=False
            ).order_by('first_name', 'last_name')
            
            self.fields['member'].queryset = available_members


class MemberSearchForm(forms.Form):
    """Form for searching members"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, email, or phone...'
        })
    )
    role = forms.ModelChoiceField(
        queryset=Role.objects.all(),
        required=False,
        empty_label="All Roles",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=[
            ('', 'All Members'),
            ('new_friends', 'New Friends'),
            ('regular_members', 'Regular Members'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class NewFriendSearchForm(forms.Form):
    """Form for searching new friends"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, email, or source...'
        })
    )
    follow_up_status = forms.ChoiceField(
        choices=[
            ('', 'All Statuses'),
            ('PENDING', 'Pending'),
            ('CONTACTED', 'Contacted'),
            ('FOLLOWED_UP', 'Followed Up'),
            ('ENGAGED', 'Engaged'),
            ('NOT_INTERESTED', 'Not Interested'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    timer_status = forms.ChoiceField(
        choices=[
            ('', 'All Timer Status'),
            ('1', '1st Timer'),
            ('2', '2nd Timer'),
            ('3', '3rd Timer'),
            ('4', '4th Timer'),
            ('5', '5th Timer'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class RegularMemberSearchForm(forms.Form):
    """Form for searching regular members"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, email, or ministry...'
        })
    )
    role_type = forms.ChoiceField(
        choices=[
            ('', 'All Roles'),
            ('VSL', 'VSL'),
            ('CSL', 'CSL'),
            ('CL', 'CL'),
            ('CM', 'CM'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        empty_label="All Groups",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    availability = forms.ChoiceField(
        choices=[
            ('', 'All Availability'),
            ('AVAILABLE', 'Available'),
            ('LIMITED', 'Limited'),
            ('UNAVAILABLE', 'Unavailable'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class GroupSearchForm(forms.Form):
    """Form for searching groups"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, description, or leader...'
        })
    )
    group_type = forms.ChoiceField(
        choices=[
            ('', 'All Types'),
            ('CARE', 'Care Group'),
            ('MINISTRY', 'Ministry Group'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class ActivityLogSearchForm(forms.Form):
    """Form for searching activity logs"""
    action = forms.ChoiceField(
        choices=[
            ('', 'All Actions'),
            ('LOGIN', 'User Login'),
            ('LOGOUT', 'User Logout'),
            ('REGISTER', 'User Registration'),
            ('PROFILE_UPDATE', 'Profile Update'),
            ('ROLE_CHANGE', 'Role Change'),
            ('STATUS_CHANGE', 'Status Change'),
            ('GROUP_JOIN', 'Group Join'),
            ('GROUP_LEAVE', 'Group Leave'),
            ('ATTENDANCE', 'Attendance Recorded'),
            ('NEW_FRIEND_ADDED', 'New Friend Added'),
            ('REGULAR_MEMBER_TRANSITION', 'Transitioned to Regular Member'),
            ('FOLLOW_UP', 'Follow Up Activity'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    user = forms.ModelChoiceField(
        queryset=CustomUser.objects.all(),
        required=False,
        empty_label="All Users",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )


class BulkActionForm(forms.Form):
    """Form for bulk actions on members"""
    action = forms.ChoiceField(
        choices=[
            ('', 'Select Action'),
            ('export', 'Export Selected'),
            ('update_role', 'Update Role'),
            ('update_status', 'Update Status'),
            ('add_to_group', 'Add to Group'),
            ('remove_from_group', 'Remove from Group'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    members = forms.MultipleChoiceField(
        choices=[],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    
    # Additional fields for specific actions
    new_role = forms.ModelChoiceField(
        queryset=Role.objects.all(),
        required=False,
        empty_label="Select Role",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    new_status = forms.ChoiceField(
        choices=[
            ('', 'Select Status'),
            ('new_friend', 'New Friend'),
            ('regular_member', 'Regular Member'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    target_group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        empty_label="Select Group",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        self.church = kwargs.pop('church', None)
        super().__init__(*args, **kwargs)
        
        if self.church:
            # Set choices for members
            members = CustomUser.objects.filter(church=self.church, is_active=True)
            self.fields['members'].choices = [(m.id, m.full_name) for m in members]
            
            # Set querysets for related fields
            self.fields['new_role'].queryset = Role.objects.filter(is_active=True)
            self.fields['target_group'].queryset = Group.objects.filter(
                church=self.church, is_active=True
            )


class FollowUpForm(forms.Form):
    """Form for updating follow up status"""
    status = forms.ChoiceField(
        choices=NewFriend._meta.get_field('follow_up_status').choices,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Add follow up notes...'
        })
    )


class AttendanceForm(forms.Form):
    """Form for recording attendance"""
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    members = forms.MultipleChoiceField(
        choices=[],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        self.church = kwargs.pop('church', None)
        super().__init__(*args, **kwargs)
        
        if self.church:
            members = CustomUser.objects.filter(church=self.church, is_active=True)
            self.fields['members'].choices = [(m.id, m.full_name) for m in members] 


class NewFriendImportForm(forms.Form):
    """Form for importing New Friends from CSV/Excel"""
    file = forms.FileField(
        label='Upload File',
        help_text='Upload CSV or Excel file with New Friends data',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls'
        })
    )
    
    def clean_file(self):
        file = self.cleaned_data['file']
        if file:
            # Check file size (max 5MB)
            if file.size > 5 * 1024 * 1024:
                raise ValidationError('File size must be under 5MB.')
            
            # Check file extension
            ext = file.name.split('.')[-1].lower()
            if ext not in ['csv', 'xlsx', 'xls']:
                raise ValidationError('Please upload a CSV or Excel file.')
        return file

class RegularMemberImportForm(forms.Form):
    """Form for importing Regular Members from CSV/Excel"""
    file = forms.FileField(
        label='Upload File',
        help_text='Upload CSV or Excel file with Regular Members data',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls'
        })
    )
    
    def clean_file(self):
        file = self.cleaned_data['file']
        if file:
            # Check file size (max 5MB)
            if file.size > 5 * 1024 * 1024:
                raise ValidationError('File size must be under 5MB.')
            
            # Check file extension
            ext = file.name.split('.')[-1].lower()
            if ext not in ['csv', 'xlsx', 'xls']:
                raise ValidationError('Please upload a CSV or Excel file.')
        return file


class UserProfileForm(forms.ModelForm):
    """Enhanced form for user profile editing with QR code display"""
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'email', 'phone_number', 'address', 
            'birth_date', 'profile_picture'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'readonly': True}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make email readonly for security
        self.fields['email'].widget.attrs['readonly'] = True
        self.fields['email'].help_text = "Email cannot be changed for security reasons"


class QRCodeScanForm(forms.Form):
    """Form for QR code scanning"""
    qr_data = forms.CharField(
        max_length=500,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Scan QR code or enter QR data manually',
            'id': 'qr-scanner-input'
        })
    )
    attendance_type = forms.ChoiceField(
        choices=Attendance.ATTENDANCE_TYPES,
        initial='SERVICE',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Optional notes...'
        })
    )


class ManualAttendanceForm(forms.Form):
    """Form for manual attendance entry"""
    date = forms.DateField(
        initial=timezone.now().date,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    time = forms.TimeField(
        initial=timezone.now().time,
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        })
    )
    member = forms.ModelChoiceField(
        queryset=CustomUser.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Select the member to record attendance for"
    )
    role_status = forms.ChoiceField(
        choices=[
            ('', 'Select Role/Status'),
            ('VSL', 'VSL (Vine Servant Leader)'),
            ('CSL', 'CSL (Cluster Servant Leader)'),
            ('CL', 'CL (Care Leader)'),
            ('CM', 'CM (Care Member)'),
            ('NEW_FRIEND', 'New Friend'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Select the member's role or status"
    )
    service_type = forms.ChoiceField(
        choices=[
            ('SERVICE', 'Church Service'),
            ('MIDWEEK', 'Midweek Service'),
            ('SUNDAY', 'Sunday Service'),
            ('CARE_GROUP', 'Care Group'),
            ('MINISTRY', 'Ministry Meeting'),
            ('EVENT', 'Special Event'),
            ('OTHER', 'Other'),
        ],
        initial='SERVICE',
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Select the type of service/event"
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Optional notes about the attendance...'
        })
    )

    def __init__(self, *args, **kwargs):
        self.church = kwargs.pop('church', None)
        super().__init__(*args, **kwargs)
        
        if self.church:
            self.fields['member'].queryset = CustomUser.objects.filter(
                church=self.church, 
                is_active=True
            ).order_by('first_name', 'last_name')
            
            # Custom label to show only names, not emails
            self.fields['member'].label_from_instance = lambda obj: obj.full_name


class AttendanceFilterForm(forms.Form):
    """Form for filtering attendance records"""
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    attendance_type = forms.ChoiceField(
        choices=[('', 'All Types')] + list(Attendance.ATTENDANCE_TYPES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    user = forms.ModelChoiceField(
        queryset=CustomUser.objects.none(),
        required=False,
        empty_label="All Users",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        self.church = kwargs.pop('church', None)
        super().__init__(*args, **kwargs)
        
        if self.church:
            self.fields['user'].queryset = CustomUser.objects.filter(
                church=self.church, 
                is_active=True
            ).order_by('first_name', 'last_name')


class AttendanceExportForm(forms.Form):
    """Form for exporting attendance data"""
    EXPORT_FORMATS = [
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('pdf', 'PDF'),
    ]
    
    format = forms.ChoiceField(
        choices=EXPORT_FORMATS,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    attendance_type = forms.ChoiceField(
        choices=[('', 'All Types')] + list(Attendance.ATTENDANCE_TYPES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    include_qr_codes = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Include QR codes in the export"
    )


class ProfileExportForm(forms.Form):
    """Form for exporting user profiles with QR codes"""
    EXPORT_FORMATS = [
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('pdf', 'PDF'),
    ]
    
    format = forms.ChoiceField(
        choices=EXPORT_FORMATS,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    include_qr_codes = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Include QR codes in the export"
    )
    include_profile_pictures = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Include profile pictures in the export"
    )
    member_type = forms.ChoiceField(
        choices=[
            ('', 'All Members'),
            ('new_friends', 'New Friends Only'),
            ('regular_members', 'Regular Members Only'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class ProfileImportForm(forms.Form):
    """Form for importing user profiles"""
    file = forms.FileField(
        label='Upload File',
        help_text='Upload CSV or Excel file with user profile data',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls'
        })
    )
    update_existing = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Update existing users if found"
    )
    generate_qr_codes = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Generate QR codes for imported users"
    )
    
    def clean_file(self):
        file = self.cleaned_data['file']
        if file:
            # Check file size (max 10MB for profile imports)
            if file.size > 10 * 1024 * 1024:
                raise ValidationError('File size must be under 10MB.')
            
            # Check file extension
            ext = file.name.split('.')[-1].lower()
            if ext not in ['csv', 'xlsx', 'xls']:
                raise ValidationError('Please upload a CSV or Excel file.')
        return file