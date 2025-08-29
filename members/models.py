from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db.models import Count, Q
from django.urls import reverse


class CustomUserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, first_name, last_name, password, **extra_fields)


class Church(models.Model):
    """Church branch model"""
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    domain = models.CharField(max_length=100, unique=True)
    logo = models.ImageField(upload_to='church_logos/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Churches"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('churches:church_dashboard', kwargs={'church_domain': self.domain})

    @property
    def total_members(self):
        """Get total number of active members"""
        return self.members.filter(is_active=True).count()

    @property
    def new_friends_count(self):
        """Get count of new friends"""
        return self.members.filter(is_active=True, is_new_friend=True).count()

    @property
    def regular_members_count(self):
        """Get count of regular members"""
        return self.members.filter(is_active=True, is_new_friend=False).count()

    @property
    def growth_rate(self):
        """Calculate monthly growth rate"""
        from datetime import timedelta
        last_month = timezone.now() - timedelta(days=30)
        new_members_this_month = self.members.filter(
            date_joined__gte=last_month,
            is_active=True
        ).count()
        return new_members_this_month

    def get_member_statistics(self):
        """Get detailed member statistics"""
        members = self.members.filter(is_active=True)
        
        stats = {
            'total': members.count(),
            'new_friends': members.filter(is_new_friend=True).count(),
            'regular_members': members.filter(is_new_friend=False).count(),
            'by_role': {},
            'by_timer_status': {},
        }
        
        # Count by role
        for role in Role.objects.all():
            count = members.filter(role=role).count()
            if count > 0:
                stats['by_role'][role.name] = count
        
        # Count by timer status (for new friends)
        for i in range(1, 6):
            count = members.filter(is_new_friend=True, timer_status=i).count()
            if count > 0:
                stats['by_timer_status'][f'{i}st timer'] = count
        
        return stats


class Role(models.Model):
    """User roles and permissions"""
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('VSL', 'Vine Servant Leader'),
        ('CSL', 'Cluster Servant Leader'),
        ('CL', 'Care Leader'),
        ('CM', 'Care Member'),
        ('NEW_FRIEND', 'New Friend'),
    ]
    
    name = models.CharField(max_length=20, choices=ROLE_CHOICES, unique=True)
    description = models.TextField(blank=True)
    permissions = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.get_name_display()

    @property
    def user_count(self):
        """Get number of users with this role"""
        return self.users.filter(is_active=True).count()

    def get_permission_level(self):
        """Get permission level for this role"""
        permission_levels = {
            'ADMIN': 100,
            'VSL': 80,
            'CSL': 70,
            'CL': 60,
            'CM': 50,
            'NEW_FRIEND': 10,
        }
        return permission_levels.get(self.name, 0)


class CustomUser(AbstractUser):
    """Custom user model with church and role integration"""
    # Remove username field since we're using email
    username = None
    
    # Basic fields
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    
    # Church and role fields
    church = models.ForeignKey(Church, on_delete=models.CASCADE, related_name='members', null=True, blank=True)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='users', null=True, blank=True)
    
    # Profile fields
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    birth_date = models.DateField(null=True, blank=True)
    
    # Member status fields
    is_new_friend = models.BooleanField(default=True)
    timer_status = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1st to 5th timer status"
    )
    
    # Timestamps
    date_joined = models.DateTimeField(auto_now_add=True)
    last_attendance = models.DateTimeField(null=True, blank=True)
    transition_date = models.DateTimeField(null=True, blank=True)
    
    # Email verification
    email_verified = models.BooleanField(default=False)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    def get_absolute_url(self):
        return reverse('members:user_detail', kwargs={'pk': self.pk})

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        """Calculate age from birth date"""
        if self.birth_date:
            from datetime import date
            today = date.today()
            return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        return None

    @property
    def membership_duration(self):
        """Calculate membership duration in days"""
        return (timezone.now() - self.date_joined).days

    @property
    def days_since_last_attendance(self):
        """Calculate days since last attendance"""
        if self.last_attendance:
            return (timezone.now() - self.last_attendance).days
        return None

    def transition_to_regular(self):
        """Transition from New Friend to Regular Member"""
        if self.is_new_friend:
            self.is_new_friend = False
            self.transition_date = timezone.now()
            self.save()
            
            # Create RegularMember profile if it doesn't exist
            RegularMember.objects.get_or_create(
                user=self,
                defaults={'role_type': self.role.name if self.role else 'CM'}
            )

    def update_timer_status(self, new_status):
        """Update timer status for New Friends"""
        if 1 <= new_status <= 5:
            self.timer_status = new_status
            if new_status == 5:
                self.transition_to_regular()
            self.save()

    def record_attendance(self):
        """Record user attendance"""
        self.last_attendance = timezone.now()
        self.save()
        
        # Log the attendance
        ActivityLog.objects.create(
            user=self,
            action='ATTENDANCE',
            description=f'Recorded attendance at {self.church.name if self.church else "church"}',
            ip_address='',  # Will be set by middleware
            user_agent=''   # Will be set by middleware
        )

    def get_activity_summary(self, days=30):
        """Get user activity summary for the last N days"""
        from datetime import timedelta
        start_date = timezone.now() - timedelta(days=days)
        
        activities = self.activity_logs.filter(timestamp__gte=start_date)
        
        return {
            'total_activities': activities.count(),
            'login_count': activities.filter(action='LOGIN').count(),
            'attendance_count': activities.filter(action='ATTENDANCE').count(),
            'profile_updates': activities.filter(action='PROFILE_UPDATE').count(),
            'recent_activities': activities.order_by('-timestamp')[:5]
        }

    def can_access_church_data(self, target_church):
        """Check if user can access data from a specific church"""
        if self.is_superuser:
            return True
        if self.role and self.role.name == 'ADMIN':
            return True
        return self.church == target_church


class NewFriend(models.Model):
    """Extended model for New Friends tracking"""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='new_friend_profile')
    registration_date = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=100, blank=True, help_text="How they found the church")
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    # Additional tracking fields
    invited_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='invited_new_friends'
    )
    follow_up_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('CONTACTED', 'Contacted'),
            ('FOLLOWED_UP', 'Followed Up'),
            ('ENGAGED', 'Engaged'),
            ('NOT_INTERESTED', 'Not Interested'),
        ],
        default='PENDING'
    )
    follow_up_notes = models.TextField(blank=True)
    last_follow_up = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "New Friend"
        verbose_name_plural = "New Friends"
        ordering = ['-registration_date']

    def __str__(self):
        return f"New Friend: {self.user.full_name}"

    @property
    def days_since_registration(self):
        """Calculate days since registration"""
        return (timezone.now() - self.registration_date).days

    @property
    def days_since_last_follow_up(self):
        """Calculate days since last follow up"""
        if self.last_follow_up:
            return (timezone.now() - self.last_follow_up).days
        return None

    def update_follow_up(self, status, notes=''):
        """Update follow up status and notes"""
        self.follow_up_status = status
        self.follow_up_notes = notes
        self.last_follow_up = timezone.now()
        self.save()


class RegularMember(models.Model):
    """Extended model for Regular Members"""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='regular_member_profile')
    role_type = models.CharField(max_length=10, choices=Role.ROLE_CHOICES[1:-1])  # Exclude ADMIN, NEW_FRIEND
    group = models.ForeignKey('Group', on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    ministry_involvement = models.TextField(blank=True)
    skills = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    # Additional fields
    baptism_date = models.DateField(null=True, blank=True)
    membership_date = models.DateField(null=True, blank=True)
    spiritual_gifts = models.TextField(blank=True, help_text="Spiritual gifts and talents")
    availability = models.CharField(
        max_length=20,
        choices=[
            ('AVAILABLE', 'Available'),
            ('LIMITED', 'Limited'),
            ('UNAVAILABLE', 'Unavailable'),
        ],
        default='AVAILABLE'
    )

    class Meta:
        verbose_name = "Regular Member"
        verbose_name_plural = "Regular Members"
        ordering = ['user__first_name']

    def __str__(self):
        return f"Regular Member: {self.user.full_name} ({self.role_type})"

    @property
    def membership_years(self):
        """Calculate years of membership"""
        if self.membership_date:
            from datetime import date
            today = date.today()
            return today.year - self.membership_date.year
        return None


class Group(models.Model):
    """Care Groups and Ministry Groups"""
    GROUP_TYPES = [
        ('CARE', 'Care Group'),
        ('MINISTRY', 'Ministry Group'),
    ]
    
    name = models.CharField(max_length=100)
    group_type = models.CharField(max_length=10, choices=GROUP_TYPES)
    leader = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='led_groups')
    church = models.ForeignKey(Church, on_delete=models.CASCADE, related_name='groups')
    description = models.TextField(blank=True)
    meeting_schedule = models.CharField(max_length=200, blank=True)
    meeting_location = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Additional fields
    max_members = models.PositiveIntegerField(default=20, help_text="Maximum number of members")
    current_members_count = models.PositiveIntegerField(default=0)
    meeting_day = models.CharField(
        max_length=10,
        choices=[
            ('MONDAY', 'Monday'),
            ('TUESDAY', 'Tuesday'),
            ('WEDNESDAY', 'Wednesday'),
            ('THURSDAY', 'Thursday'),
            ('FRIDAY', 'Friday'),
            ('SATURDAY', 'Saturday'),
            ('SUNDAY', 'Sunday'),
        ],
        blank=True
    )
    meeting_time = models.TimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Group"
        verbose_name_plural = "Groups"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_group_type_display()})"

    def get_absolute_url(self):
        return reverse('members:group_detail', kwargs={'pk': self.pk})

    @property
    def member_count(self):
        """Get current member count"""
        return self.members.count()

    @property
    def capacity_percentage(self):
        """Calculate capacity percentage"""
        if self.max_members > 0:
            return round((self.member_count / self.max_members) * 100, 1)
        return 0

    @property
    def is_full(self):
        """Check if group is at capacity"""
        return self.member_count >= self.max_members

    def add_member(self, user):
        """Add a member to the group"""
        if not self.is_full and user.church == self.church:
            regular_member, created = RegularMember.objects.get_or_create(user=user)
            regular_member.group = self
            regular_member.save()
            return True
        return False

    def remove_member(self, user):
        """Remove a member from the group"""
        try:
            regular_member = RegularMember.objects.get(user=user, group=self)
            regular_member.group = None
            regular_member.save()
            return True
        except RegularMember.DoesNotExist:
            return False

    def get_meeting_info(self):
        """Get formatted meeting information"""
        info = []
        if self.meeting_day:
            info.append(self.get_meeting_day_display())
        if self.meeting_time:
            info.append(self.meeting_time.strftime('%I:%M %p'))
        if self.meeting_location:
            info.append(self.meeting_location)
        return ' | '.join(info) if info else 'No meeting info'


class ActivityLog(models.Model):
    """System activity logging"""
    ACTION_CHOICES = [
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
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Additional fields for better tracking
    church = models.ForeignKey(Church, on_delete=models.CASCADE, related_name='activity_logs', null=True, blank=True)
    related_user = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='related_activities'
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Activity Log"
        verbose_name_plural = "Activity Logs"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.full_name} - {self.get_action_display()} - {self.timestamp}"

    def save(self, *args, **kwargs):
        # Auto-set church from user if not provided
        if not self.church and self.user:
            self.church = self.user.church
        super().save(*args, **kwargs)

    @classmethod
    def log_activity(cls, user, action, description, ip_address=None, user_agent=None, related_user=None, metadata=None):
        """Convenience method to log activity"""
        return cls.objects.create(
            user=user,
            action=action,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            related_user=related_user,
            metadata=metadata or {}
        )

    @classmethod
    def get_church_activity_summary(cls, church, days=30):
        """Get activity summary for a church"""
        from datetime import timedelta
        start_date = timezone.now() - timedelta(days=days)
        
        activities = cls.objects.filter(
            church=church,
            timestamp__gte=start_date
        )
        
        return {
            'total_activities': activities.count(),
            'unique_users': activities.values('user').distinct().count(),
            'by_action': activities.values('action').annotate(count=Count('id')),
            'recent_activities': activities.select_related('user')[:10]
        }
