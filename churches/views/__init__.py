# Import all views from separate modules to maintain compatibility with existing URLs

from .auth_views import (
    church_selection,
    church_login, 
    church_registration,
    super_admin_login,
    custom_logout
)

from .dashboard_views import (
    dashboard, 
    church_report, 
    export_church_report_to_sheets,
    generate_new_friends_report,
    generate_members_report
)

from .ajax_views import (
    ajax_church_dashboard,
    ajax_church_detection
)

from .church_management_views import (
    church_list,
    add_church,
    edit_church,
    delete_church,
    toggle_church_status,
    church_detail
)

from .pwa_views import (
    manifest,
    service_worker,
    offline
)

__all__ = [
    'church_selection',
    'church_login',
    'church_registration',
    'super_admin_login',
    'custom_logout',
    'dashboard',
    'church_report',
    'export_church_report_to_sheets',
    'generate_new_friends_report',
    'generate_members_report',
    'ajax_church_dashboard',
    'ajax_church_detection',
    'church_list',
    'add_church',
    'edit_church',
    'delete_church',
    'toggle_church_status',
    'church_detail',
    'manifest',
    'service_worker',
    'offline',
]
