"""
Virtual Care Platform - Root URL Configuration
Author: Telehealth Platform Core Team

Clean, versioned API routing under /api/v1/
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework.views import APIView
from rest_framework import permissions
from common.responses import success_response


class HealthCheckView(APIView):
    """
    GET /api/v1/health/
    Public health check endpoint for uptime monitors and readiness probes.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return success_response(
            data={
                "status": "healthy",
                "service": "Virtual Care Telemedicine API",
                "version": "1.0.0",
                "safety_protocol": "1.0.4-CLINICAL"
            },
            message="All services operational."
        )


urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Core Health Check
    path('api/v1/health/', HealthCheckView.as_view(), name='api-health'),

    # Modular API endpoints
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/patients/', include('apps.patients.urls')),
    path('api/v1/doctors/', include('apps.doctors.urls')),
    path('api/v1/appointments/', include('apps.appointments.urls')),
    path('api/v1/consultations/', include('apps.consultations.urls')),
    path('api/v1/ai-care/', include('apps.ai_care.urls')),
    path('api/v1/hospitals/', include('apps.hospitals.urls')),
    path('api/v1/prescriptions/', include('apps.prescriptions.urls')),
    path('api/v1/', include('apps.billing.urls')),
    path('api/v1/notifications/', include('apps.notifications.urls')),
]
