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
    
    # Custom logout
    path('logout/', views.custom_logout, name='custom_logout'),
    
    # AJAX endpoints
    path('ajax/church-detection/', views.ajax_church_detection, name='ajax_church_detection'),
    path('ajax/church-dashboard/<str:church_domain>/', views.ajax_church_dashboard, name='ajax_church_dashboard'),
] 