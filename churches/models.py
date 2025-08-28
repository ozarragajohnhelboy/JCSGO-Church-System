from django.db import models
from members.models import Church


class ChurchSettings(models.Model):
    """Church-specific settings and configurations"""
    church = models.OneToOneField(Church, on_delete=models.CASCADE, related_name='settings')
    
    # Registration settings
    allow_public_registration = models.BooleanField(default=True)
    require_email_verification = models.BooleanField(default=True)
    require_admin_approval = models.BooleanField(default=False)
    
    # Email settings
    welcome_email_template = models.TextField(blank=True)
    notification_email = models.EmailField(blank=True)
    
    # Dashboard settings
    show_new_friends_count = models.BooleanField(default=True)
    show_regulars_count = models.BooleanField(default=True)
    show_growth_charts = models.BooleanField(default=True)
    
    # Privacy settings
    show_member_contact_info = models.BooleanField(default=False)
    allow_member_directory = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Church Setting"
        verbose_name_plural = "Church Settings"

    def __str__(self):
        return f"Settings for {self.church.name}"


class ChurchAnnouncement(models.Model):
    """Church announcements and notifications"""
    church = models.ForeignKey(Church, on_delete=models.CASCADE, related_name='announcements')
    title = models.CharField(max_length=200)
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    priority = models.CharField(
        max_length=10,
        choices=[
            ('LOW', 'Low'),
            ('MEDIUM', 'Medium'),
            ('HIGH', 'High'),
            ('URGENT', 'Urgent'),
        ],
        default='MEDIUM'
    )
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey('members.CustomUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority', '-created_at']

    def __str__(self):
        return f"{self.title} - {self.church.name}"

    @property
    def is_current(self):
        """Check if announcement is currently active"""
        from django.utils import timezone
        now = timezone.now()
        return (
            self.is_active and 
            self.start_date <= now and 
            (self.end_date is None or self.end_date >= now)
        )
