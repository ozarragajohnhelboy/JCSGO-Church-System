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
    
    # Groups
    path('groups/', views.group_list, name='group_list'),
    path('groups/<int:group_id>/', views.group_detail, name='group_detail'),
    
    # Role Management
    path('role-management/', views.role_management, name='role_management'),
    path('ajax/update-user-role/<int:user_id>/', views.ajax_update_user_role, name='ajax_update_user_role'),
    path('ajax/get-user-details/<int:user_id>/', views.ajax_get_user_details, name='ajax_get_user_details'),
    path('ajax/bulk-role-update/', views.ajax_bulk_role_update, name='ajax_bulk_role_update'),
    
    # Activity Logs
    path('activity-logs/', views.activity_logs, name='activity_logs'),
    
    # Export functionality
    path('export/', views.export_members, name='export_members'),
    
    # Church Statistics
    path('statistics/', views.church_statistics, name='church_statistics'),
] 