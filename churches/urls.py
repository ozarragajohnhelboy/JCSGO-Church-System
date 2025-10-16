from django.urls import path
from . import views

app_name = 'churches'

urlpatterns = [
    # Church selection and authentication
    path('', views.church_selection, name='church_selection'),
    path('super-admin/login/', views.super_admin_login, name='super_admin_login'),
    path('login/<str:church_domain>/', views.church_login, name='church_login'),
    path('register/<str:church_domain>/', views.church_registration, name='church_registration'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('church-report/', views.church_report, name='church_report'),
    path('church-report/export-to-sheets/', views.export_church_report_to_sheets, name='export_church_report_to_sheets'),
    
    # Custom logout
    path('logout/', views.custom_logout, name='custom_logout'),
    
    # AJAX endpoints
    path('ajax/church-detection/', views.ajax_church_detection, name='ajax_church_detection'),
    path('ajax/church-dashboard/<str:church_domain>/', views.ajax_church_dashboard, name='ajax_church_dashboard'),
    
    # Church Management (Super Admin only)
    path('churches/', views.church_list, name='church_list'),
    path('churches/add/', views.add_church, name='add_church'),
    path('churches/<int:church_id>/edit/', views.edit_church, name='edit_church'),
    path('churches/<int:church_id>/delete/', views.delete_church, name='delete_church'),
    path('churches/<int:church_id>/detail/', views.church_detail, name='church_detail'),
    path('ajax/churches/<int:church_id>/toggle-status/', views.toggle_church_status, name='toggle_church_status'),
] 