from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import (
    Church, Role, CustomUser, NewFriend, RegularMember, 
    Group, ActivityLog
)


@admin.register(Church)
class ChurchAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'domain', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'location', 'domain']
    ordering = ['name']


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active', 'created_at']
    list_filter = ['is_active', 'name']
    search_fields = ['name', 'description']
    ordering = ['name']


class NewFriendInline(admin.StackedInline):
    model = NewFriend
    extra = 0
    fields = ['registration_date', 'source', 'notes', 'is_active']


class RegularMemberInline(admin.StackedInline):
    model = RegularMember
    extra = 0
    fields = ['role_type', 'group', 'ministry_involvement', 'skills', 'is_active']


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = [
        'email', 'full_name', 'church', 'role', 'is_new_friend', 
        'timer_status', 'is_active', 'date_joined'
    ]
    list_filter = [
        'church', 'role', 'is_new_friend', 'is_active', 
        'date_joined', 'is_staff', 'is_superuser'
    ]
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'profile_picture', 'phone_number', 'address', 'birth_date')
        }),
        ('Church & Role', {
            'fields': ('church', 'role', 'is_new_friend', 'timer_status')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'church', 'role', 'password1', 'password2'),
        }),
    )
    
    inlines = [NewFriendInline, RegularMemberInline]
    
    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'Full Name'


@admin.register(NewFriend)
class NewFriendAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'user_church', 'timer_status', 'registration_date', 
        'source', 'is_active'
    ]
    list_filter = ['registration_date', 'is_active', 'user__church']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'source']
    ordering = ['-registration_date']
    
    def user_church(self, obj):
        return obj.user.church
    user_church.short_description = 'Church'
    
    def timer_status(self, obj):
        return obj.user.timer_status
    timer_status.short_description = 'Timer Status'


@admin.register(RegularMember)
class RegularMemberAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'user_church', 'role_type', 'group', 'is_active'
    ]
    list_filter = ['role_type', 'is_active', 'user__church', 'group']
    search_fields = ['user__first_name', 'user__last_name', 'user__email']
    ordering = ['user__first_name']
    
    def user_church(self, obj):
        return obj.user.church
    user_church.short_description = 'Church'


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'group_type', 'leader', 'church', 'is_active', 'created_at'
    ]
    list_filter = ['group_type', 'is_active', 'church', 'created_at']
    search_fields = ['name', 'leader__first_name', 'leader__last_name']
    ordering = ['name']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('leader', 'church')


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'action', 'ip_address', 'timestamp'
    ]
    list_filter = ['action', 'timestamp', 'user__church']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'description']
    ordering = ['-timestamp']
    readonly_fields = ['user', 'action', 'description', 'ip_address', 'user_agent', 'timestamp']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
