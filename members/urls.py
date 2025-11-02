from django.urls import path
from . import views

app_name = 'members'

urlpatterns = [
    # Member lists
    path('', views.member_list, name='member_list'),
    path('<int:pk>/', views.member_detail, name='member_detail'),
    path('new-friends/', views.new_friends_list, name='new_friends_list'),
    path('regular-members/', views.regular_members_list, name='regular_members_list'),
    
    # New Friends CRUD
    path('new-friends/add/', views.new_friend_add, name='new_friend_add'),
    path('new-friends/<int:new_friend_id>/edit/', views.new_friend_edit, name='new_friend_edit'),
    path('new-friends/<int:new_friend_id>/delete/', views.new_friend_delete, name='new_friend_delete'),
    path('new-friends/import/', views.new_friend_import, name='new_friend_import'),
    
    # Regular Members CRUD
    path('regular-members/add/', views.regular_member_add, name='regular_member_add'),
    path('regular-members/<int:regular_member_id>/edit/', views.regular_member_edit, name='regular_member_edit'),
    path('regular-members/<int:regular_member_id>/delete/', views.regular_member_delete, name='regular_member_delete'),
    path('regular-members/import/', views.regular_member_import, name='regular_member_import'),
    
    # Groups (Admin access)
    path('groups/', views.group_list, name='group_list'),
    path('groups/<int:pk>/', views.group_detail, name='group_detail'),
    
    # Care Groups (Leadership access - VSL, CSL, CL)
    path('care-groups/', views.care_group_list, name='care_group_list'),
    path('care-groups/create/', views.care_group_create, name='care_group_create'),
    path('care-groups/<int:group_id>/', views.care_group_detail, name='care_group_detail'),
    path('care-groups/<int:group_id>/edit/', views.care_group_edit, name='care_group_edit'),
    path('care-groups/<int:group_id>/add-member/', views.care_group_add_member, name='care_group_add_member'),
    path('care-groups/<int:group_id>/remove-member/<int:member_id>/', views.care_group_remove_member, name='care_group_remove_member'),
    
    # Role-specific New Friends (VSL, CSL, CL)
    path('my-new-friends/', views.role_new_friends_list, name='role_new_friends_list'),
    
    # Role Management
    path('role-management/', views.role_management, name='role_management'),
    path('ajax/update-user-role/<int:user_id>/', views.ajax_update_user_role, name='ajax_update_user_role'),
    path('ajax/get-user-details/<int:user_id>/', views.ajax_get_user_details, name='ajax_get_user_details'),
    path('ajax/bulk-role-update/', views.ajax_bulk_role_update, name='ajax_bulk_role_update'),
    path('ajax/get-available-members/<int:group_id>/', views.ajax_get_available_members, name='ajax_get_available_members'),
    path('ajax/search-members/<int:group_id>/', views.ajax_search_members, name='ajax_search_members'),
    path('ajax/search-leader/', views.ajax_search_leader, name='ajax_search_leader'),
    path('ajax/search-member-attendance/', views.ajax_search_member_for_attendance, name='ajax_search_member_for_attendance'),
    
    # AJAX: New Friend interactions
    path('ajax/update-timer-status/<int:user_id>/', views.ajax_update_timer_status, name='ajax_update_timer_status'),
    path('ajax/record-attendance/<int:user_id>/', views.ajax_record_attendance, name='ajax_record_attendance'),
    path('ajax/update-follow-up/<int:new_friend_id>/', views.ajax_update_follow_up, name='ajax_update_follow_up'),
    
    # Activity Logs
    path('activity-logs/', views.activity_logs, name='activity_logs'),
    path('ajax/activity-details/<int:activity_id>/', views.ajax_activity_details, name='ajax_activity_details'),
    path('ajax/member-activity-logs/<int:member_id>/', views.ajax_member_activity_logs, name='ajax_member_activity_logs'),
    path('ajax/group-activity-logs/<int:group_id>/', views.ajax_group_activity_logs, name='ajax_group_activity_logs'),
    
    # Export functionality
    path('export/', views.export_members, name='export_members'),
    path('export-role-data/', views.export_role_data, name='export_role_data'),
    
    # Church Statistics
    path('statistics/', views.church_statistics, name='church_statistics'),
    
    # Profile and QR Code
    path('profile/', views.user_profile, name='user_profile'),
    path('generate-qr/<int:user_id>/', views.generate_qr_code, name='generate_qr_code'),
    
    # Attendance System
    path('attendance/scanner/', views.qr_scanner, name='qr_scanner'),
    path('attendance/', views.attendance_list, name='attendance_list'),
    path('attendance/export/', views.attendance_export, name='attendance_export'),
    
    # Profile Import/Export
    path('profiles/export/', views.profile_export, name='profile_export'),
    path('profiles/import/', views.profile_import, name='profile_import'),
    
    # Care Group Reports
    path('care-group-reports/', views.care_group_report_list, name='care_group_report_list'),
    path('care-group-reports/create/', views.care_group_report_create, name='care_group_report_create'),
    path('care-group-reports/<int:report_id>/member-reports/', views.care_group_member_report_create, name='care_group_member_report_create'),
    path('care-group-reports/<int:report_id>/', views.care_group_report_detail, name='care_group_report_detail'),
    path('care-group-reports/<int:report_id>/print/', views.care_group_report_print, name='care_group_report_print'),
    path('care-group-reports/<int:report_id>/edit/', views.care_group_report_edit, name='care_group_report_edit'),
    path('care-group-reports/<int:report_id>/delete/', views.care_group_report_delete, name='care_group_report_delete'),
    path('care-group-reports/export/', views.care_group_report_export, name='care_group_report_export'),
    path('care-group-reports/<int:report_id>/export/', views.care_group_member_report_export, name='care_group_member_report_export'),
    
    # Care Group Attendance Tracking
    path('care-groups/<int:group_id>/attendance/', views.care_group_attendance_tracking, name='care_group_attendance_tracking'),
] 