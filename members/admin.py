from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export.fields import Field
from import_export.widgets import ForeignKeyWidget, DateWidget

from .models import (
    Church, Role, CustomUser, NewFriend, RegularMember, 
    Group, ActivityLog
)


# Import/Export Resources
class ChurchResource(resources.ModelResource):
    class Meta:
        model = Church
        import_id_fields = ('domain',)
        fields = ('id', 'name', 'location', 'domain', 'is_active', 'created_at', 'updated_at')
        export_order = fields


class RoleResource(resources.ModelResource):
    class Meta:
        model = Role
        import_id_fields = ('name',)
        fields = ('id', 'name', 'description', 'permissions', 'is_active', 'created_at')
        export_order = fields


class CustomUserResource(resources.ModelResource):
    church = Field(column_name='church', attribute='church', widget=ForeignKeyWidget(Church, 'domain'))
    role = Field(column_name='role', attribute='role', widget=ForeignKeyWidget(Role, 'name'))
    
    class Meta:
        model = CustomUser
        import_id_fields = ('email',)
        fields = (
            'id', 'email', 'first_name', 'last_name', 'church', 'role',
            'phone_number', 'address', 'birth_date', 'is_new_friend', 
            'timer_status', 'date_joined', 'last_attendance', 'transition_date',
            'email_verified', 'is_active', 'is_staff', 'is_superuser'
        )
        export_order = fields


class NewFriendResource(resources.ModelResource):
    user = Field(column_name='user', attribute='user', widget=ForeignKeyWidget(CustomUser, 'email'))
    
    class Meta:
        model = NewFriend
        import_id_fields = ('user',)
        fields = ('id', 'user', 'registration_date', 'source', 'notes', 'is_active')
        export_order = fields


class RegularMemberResource(resources.ModelResource):
    user = Field(column_name='user', attribute='user', widget=ForeignKeyWidget(CustomUser, 'email'))
    group = Field(column_name='group', attribute='group', widget=ForeignKeyWidget(Group, 'name'))
    
    class Meta:
        model = RegularMember
        import_id_fields = ('user',)
        fields = ('id', 'user', 'role_type', 'group', 'ministry_involvement', 'skills', 'is_active')
        export_order = fields


class GroupResource(resources.ModelResource):
    leader = Field(column_name='leader', attribute='leader', widget=ForeignKeyWidget(CustomUser, 'email'))
    church = Field(column_name='church', attribute='church', widget=ForeignKeyWidget(Church, 'domain'))
    
    class Meta:
        model = Group
        import_id_fields = ('name', 'church')
        fields = ('id', 'name', 'group_type', 'leader', 'church', 'description', 'meeting_schedule', 'is_active', 'created_at')
        export_order = fields


class ActivityLogResource(resources.ModelResource):
    user = Field(column_name='user', attribute='user', widget=ForeignKeyWidget(CustomUser, 'email'))
    timestamp = Field(column_name='timestamp', attribute='timestamp', widget=DateWidget(format='%Y-%m-%d %H:%M:%S'))
    
    class Meta:
        model = ActivityLog
        fields = ('id', 'user', 'action', 'description', 'ip_address', 'user_agent', 'timestamp')
        export_order = fields


# Admin Classes
@admin.register(Church)
class ChurchAdmin(ImportExportModelAdmin):
    resource_class = ChurchResource
    list_display = ('name', 'location', 'domain', 'member_count', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'location', 'domain')
    readonly_fields = ('created_at', 'updated_at')
    
    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Members'


@admin.register(Role)
class RoleAdmin(ImportExportModelAdmin):
    resource_class = RoleResource
    list_display = ('name', 'description', 'user_count', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at',)
    
    def user_count(self, obj):
        return obj.users.count()
    user_count.short_description = 'Users'


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin, ImportExportModelAdmin):
    resource_class = CustomUserResource
    list_display = ('email', 'full_name', 'church', 'role', 'status_display', 'is_active', 'date_joined')
    list_filter = ('church', 'role', 'is_new_friend', 'is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'profile_picture', 'phone_number', 'address', 'birth_date')}),
        ('Church & Role', {'fields': ('church', 'role')}),
        ('Member Status', {'fields': ('is_new_friend', 'timer_status', 'last_attendance', 'transition_date')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
        ('Email', {'fields': ('email_verified',)}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'church', 'role'),
        }),
    )
    
    readonly_fields = ('date_joined', 'last_login', 'transition_date')
    
    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'Full Name'
    
    def status_display(self, obj):
        if obj.is_new_friend:
            return format_html('<span style="color: orange;">New Friend ({})</span>', obj.timer_status)
        else:
            return format_html('<span style="color: green;">Regular Member</span>')
    status_display.short_description = 'Status'


@admin.register(NewFriend)
class NewFriendAdmin(ImportExportModelAdmin):
    resource_class = NewFriendResource
    list_display = ('user', 'church', 'registration_date', 'source', 'timer_status', 'is_active')
    list_filter = ('registration_date', 'is_active', 'user__church')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'source', 'notes')
    readonly_fields = ('registration_date',)
    
    def church(self, obj):
        return obj.user.church.name if obj.user.church else '-'
    church.short_description = 'Church'
    
    def timer_status(self, obj):
        return obj.user.timer_status
    timer_status.short_description = 'Timer Status'


@admin.register(RegularMember)
class RegularMemberAdmin(ImportExportModelAdmin):
    resource_class = RegularMemberResource
    list_display = ('user', 'church', 'role_type', 'group', 'is_active')
    list_filter = ('role_type', 'is_active', 'user__church', 'group')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'ministry_involvement', 'skills')
    
    def church(self, obj):
        return obj.user.church.name if obj.user.church else '-'
    church.short_description = 'Church'


@admin.register(Group)
class GroupAdmin(ImportExportModelAdmin):
    resource_class = GroupResource
    list_display = ('name', 'group_type', 'church', 'leader', 'member_count', 'is_active', 'created_at')
    list_filter = ('group_type', 'is_active', 'church', 'created_at')
    search_fields = ('name', 'description', 'leader__first_name', 'leader__last_name')
    readonly_fields = ('created_at',)
    
    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Members'


@admin.register(ActivityLog)
class ActivityLogAdmin(ImportExportModelAdmin):
    resource_class = ActivityLogResource
    list_display = ('user', 'action', 'church', 'ip_address', 'timestamp')
    list_filter = ('action', 'timestamp', 'user__church')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'description')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    
    def church(self, obj):
        return obj.user.church.name if obj.user.church else '-'
    church.short_description = 'Church'
    
    def has_add_permission(self, request):
        return False  # Activity logs should only be created by the system
