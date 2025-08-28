from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


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

    def __str__(self):
        return self.name


class Role(models.Model):
    """User roles and permissions"""
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('CHURCH_LEADER', 'Church Leader'),
        ('VSL', 'VSL'),
        ('CSL', 'CSL'),
        ('CL', 'CL'),
        ('CM', 'CM'),
        ('NEW_FRIEND', 'New Friend'),
    ]
    
    name = models.CharField(max_length=20, choices=ROLE_CHOICES, unique=True)
    description = models.TextField(blank=True)
    permissions = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.get_name_display()


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

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def transition_to_regular(self):
        """Transition from New Friend to Regular Member"""
        if self.is_new_friend:
            self.is_new_friend = False
            self.transition_date = timezone.now()
            self.save()

    def update_timer_status(self, new_status):
        """Update timer status for New Friends"""
        if 1 <= new_status <= 5:
            self.timer_status = new_status
            if new_status == 5:
                self.transition_to_regular()
            self.save()


class NewFriend(models.Model):
    """Extended model for New Friends tracking"""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='new_friend_profile')
    registration_date = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=100, blank=True, help_text="How they found the church")
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"New Friend: {self.user.full_name}"

    class Meta:
        verbose_name = "New Friend"
        verbose_name_plural = "New Friends"


class RegularMember(models.Model):
    """Extended model for Regular Members"""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='regular_member_profile')
    role_type = models.CharField(max_length=10, choices=Role.ROLE_CHOICES[2:-1])  # Exclude ADMIN, CHURCH_LEADER, NEW_FRIEND
    group = models.ForeignKey('Group', on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    ministry_involvement = models.TextField(blank=True)
    skills = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Regular Member: {self.user.full_name} ({self.role_type})"

    class Meta:
        verbose_name = "Regular Member"
        verbose_name_plural = "Regular Members"


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
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_group_type_display()})"

    class Meta:
        verbose_name = "Group"
        verbose_name_plural = "Groups"


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
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.full_name} - {self.get_action_display()} - {self.timestamp}"

    class Meta:
        verbose_name = "Activity Log"
        verbose_name_plural = "Activity Logs"
        ordering = ['-timestamp']
