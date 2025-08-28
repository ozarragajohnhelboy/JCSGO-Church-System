from django.contrib import admin
from .models import ChurchSettings, ChurchAnnouncement


@admin.register(ChurchSettings)
class ChurchSettingsAdmin(admin.ModelAdmin):
    list_display = ['church', 'allow_public_registration', 'require_email_verification', 'updated_at']
    list_filter = ['allow_public_registration', 'require_email_verification', 'require_admin_approval']
    search_fields = ['church__name']
    ordering = ['church__name']


@admin.register(ChurchAnnouncement)
class ChurchAnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'church', 'priority', 'is_active', 'start_date', 'created_by']
    list_filter = ['priority', 'is_active', 'church', 'start_date']
    search_fields = ['title', 'content', 'church__name']
    ordering = ['-created_at']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        (None, {
            'fields': ('church', 'title', 'content')
        }),
        ('Settings', {
            'fields': ('is_active', 'priority', 'start_date', 'end_date')
        }),
        ('Metadata', {
            'fields': ('created_by',),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
