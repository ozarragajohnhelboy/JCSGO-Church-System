# Import all views from separate modules to maintain compatibility with existing URLs

from .member_management_views import (
    member_list,
    member_detail,
    new_friends_list,
    regular_members_list
)

from .new_friends_views import (
    new_friend_add,
    new_friend_edit,
    new_friend_delete,
    new_friend_import
)

from .regular_members_views import (
    regular_member_add,
    regular_member_edit,
    regular_member_delete,
    regular_member_import
)

from .groups_views import (
    group_list,
    group_detail
)

# Import all placeholder views temporarily
from .placeholder_views import (
    activity_logs,
    church_statistics,
    ajax_get_available_members,
    ajax_update_timer_status,
    ajax_record_attendance,
    ajax_update_follow_up,
    ajax_add_to_group,
    ajax_remove_from_group,
    ajax_activity_details,
    export_members,
    export_role_data,
    role_management,
    ajax_update_user_role,
    ajax_get_user_details,
    ajax_bulk_role_update,
    care_group_list,
    care_group_create,
    care_group_detail,
    care_group_edit,
    care_group_add_member,
    care_group_remove_member,
    role_new_friends_list,
    user_profile,
    generate_qr_code,
    qr_scanner,
    attendance_list,
    attendance_export,
    profile_export,
    profile_import,
    care_group_report_list,
    care_group_report_create,
    care_group_member_report_create,
    care_group_report_detail,
    care_group_report_print,
    care_group_report_edit,
    care_group_report_delete,
    care_group_attendance_tracking,
    care_group_report_export,
    care_group_member_report_export
)

# Make all views available when importing from members.views
__all__ = [
    # Member Management
    'member_list',
    'member_detail', 
    'new_friends_list',
    'regular_members_list',
    
    # New Friends CRUD
    'new_friend_add',
    'new_friend_edit',
    'new_friend_delete', 
    'new_friend_import',
    
    # Regular Members CRUD
    'regular_member_add',
    'regular_member_edit',
    'regular_member_delete',
    'regular_member_import',
    
    # Groups
    'group_list',
    'group_detail',
    
    # All other views (temporarily from placeholder_views)
    'activity_logs',
    'church_statistics',
    'ajax_get_available_members',
    'ajax_update_timer_status',
    'ajax_record_attendance',
    'ajax_update_follow_up',
    'ajax_add_to_group',
    'ajax_remove_from_group',
    'ajax_activity_details',
    'export_members',
    'export_role_data',
    'role_management',
    'ajax_update_user_role',
    'ajax_get_user_details',
    'ajax_bulk_role_update',
    'care_group_list',
    'care_group_create',
    'care_group_detail',
    'care_group_edit',
    'care_group_add_member',
    'care_group_remove_member',
    'role_new_friends_list',
    'user_profile',
    'generate_qr_code',
    'qr_scanner',
    'attendance_list',
    'attendance_export',
    'profile_export',
    'profile_import',
    'care_group_attendance_tracking',
    'care_group_report_list',
    'care_group_report_create',
    'care_group_member_report_create',
    'care_group_report_detail',
    'care_group_report_print',
    'care_group_report_edit',
    'care_group_report_delete',
    'care_group_attendance_tracking',
    'care_group_report_export',
    'care_group_member_report_export'
]
