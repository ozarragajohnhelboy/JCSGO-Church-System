from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate, get_user_model
from .models import CustomUser, NewFriend, RegularMember, Group, Role, Church
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
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email address'
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
    source = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'How did they hear about us?'
        })
    )
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
    
    class Meta:
        model = NewFriend
        fields = ['email', 'first_name', 'last_name', 'phone', 'source', 'notes', 'timer_status']
    
    def __init__(self, *args, **kwargs):
        self.church = kwargs.pop('church', None)
        super().__init__(*args, **kwargs)
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if self.church:
            # Check if email already exists in this church
            if CustomUser.objects.filter(email=email, church=self.church).exists():
                if not self.instance.pk:  # Only for new users
                    raise ValidationError('A user with this email already exists in this church.')
        return email


class RegularMemberForm(forms.ModelForm):
    """Form for adding/editing Regular Members"""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email address'
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
        fields = ['email', 'first_name', 'last_name', 'phone', 'role', 'group']
    
    def __init__(self, *args, **kwargs):
        self.church = kwargs.pop('church', None)
        super().__init__(*args, **kwargs)
        if self.church:
            self.fields['group'].queryset = Group.objects.filter(church=self.church, is_active=True)
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if self.church:
            # Check if email already exists in this church
            if CustomUser.objects.filter(email=email, church=self.church).exists():
                if not self.instance.pk:  # Only for new users
                    raise ValidationError('A user with this email already exists in this church.')
        return email


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