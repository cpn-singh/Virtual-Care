"""
Patients URL Configuration
Author: Clinical Systems Engineering Team
"""

from django.urls import path
from apps.patients.views import PatientProfileMeView

urlpatterns = [
    path('me/', PatientProfileMeView.as_view(), name='patient-profile-me'),
]
