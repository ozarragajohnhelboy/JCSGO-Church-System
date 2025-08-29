from django.urls import path
from . import views

app_name = 'members'

urlpatterns = [
    # Member Management
    path('members/', views.member_list, name='member_list'),
    path('members/<int:pk>/', views.member_detail, name='member_detail'),
    path('members/export/', views.export_members, name='export_members'),
    
    # New Friends Management
    path('new-friends/', views.new_friends_list, name='new_friends_list'),
    
    # Regular Members Management
    path('regular-members/', views.regular_members_list, name='regular_members_list'),
    
    # Group Management
    path('groups/', views.group_list, name='group_list'),
    path('groups/<int:pk>/', views.group_detail, name='group_detail'),
    
    # Activity Logs
    path('activity-logs/', views.activity_logs, name='activity_logs'),
    
    # Statistics
    path('statistics/', views.church_statistics, name='church_statistics'),
    
    # AJAX Endpoints
    path('ajax/update-timer-status/<int:user_id>/', views.ajax_update_timer_status, name='ajax_update_timer_status'),
    path('ajax/record-attendance/<int:user_id>/', views.ajax_record_attendance, name='ajax_record_attendance'),
    path('ajax/update-follow-up/<int:new_friend_id>/', views.ajax_update_follow_up, name='ajax_update_follow_up'),
    path('ajax/add-to-group/<int:user_id>/<int:group_id>/', views.ajax_add_to_group, name='ajax_add_to_group'),
    path('ajax/remove-from-group/<int:user_id>/<int:group_id>/', views.ajax_remove_from_group, name='ajax_remove_from_group'),
] 