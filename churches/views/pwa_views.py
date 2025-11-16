from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET
from django.conf import settings
import json
import os

@require_GET
def manifest(request):
    manifest_data = {
        "name": "JCSGO Church Management System",
        "short_name": "JCSGO Church",
        "description": "Church Management System for JCSGO",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#667eea",
        "orientation": "portrait-primary",
        "icons": [
            {
                "src": "/static/image/JCSGO_logo.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any maskable"
            },
            {
                "src": "/static/image/JCSGO_logo.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable"
            }
        ],
        "categories": ["productivity", "business"],
        "screenshots": [],
        "shortcuts": [
            {
                "name": "Dashboard",
                "url": "/dashboard/",
                "description": "View Dashboard"
            },
            {
                "name": "Members",
                "url": "/members/",
                "description": "Manage Members"
            }
        ]
    }
    return JsonResponse(manifest_data)

@require_GET
def service_worker(request):
    sw_path = os.path.join(settings.BASE_DIR, 'static', 'service-worker.js')
    try:
        with open(sw_path, 'r') as f:
            sw_content = f.read()
    except FileNotFoundError:
        sw_path = os.path.join(settings.STATIC_ROOT, 'service-worker.js')
        with open(sw_path, 'r') as f:
            sw_content = f.read()
    return HttpResponse(sw_content, content_type='application/javascript')

@require_GET
def offline(request):
    from django.shortcuts import render
    return render(request, 'pwa/offline.html')

