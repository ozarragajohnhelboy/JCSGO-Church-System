# Import all views from separate modules to maintain compatibility with existing URLs

from .auth_views import (
    church_selection,
    church_login, 
    church_registration,
    super_admin_login,
    custom_logout
)

from .dashboard_views import dashboard

from .ajax_views import (
    ajax_church_dashboard,
    ajax_church_detection
)

# Make all views available when importing from churches.views
__all__ = [
    'church_selection',
    'church_login',
    'church_registration',
    'super_admin_login',
    'custom_logout',
    'dashboard',
    'ajax_church_dashboard',
    'ajax_church_detection',
]
