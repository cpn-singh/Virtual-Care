"""
Hospitals URL Configuration
Author: Emergency Response Infrastructure Team
"""

from django.urls import path
from apps.hospitals.views import NearbyHospitalsView

urlpatterns = [
    path('nearby/', NearbyHospitalsView.as_view(), name='hospital-nearby'),
]
