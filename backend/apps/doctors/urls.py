"""
Doctor URL Configuration
Author: Clinical Operations Team
"""

from django.urls import path
from apps.doctors.views import (
    SpecializationListView,
    DoctorListView,
    DoctorDetailView,
    DoctorAvailabilityListView,
    DoctorProfileMeView,
    DoctorMeAvailabilityView,
    AdminDoctorCreateView,
    DoctorAIEmailGenerateView,
    DoctorAIEmailProvisionAllView,
)

urlpatterns = [
    path('', DoctorListView.as_view(), name='doctor-list'),
    path('admin-create/', AdminDoctorCreateView.as_view(), name='doctor-admin-create'),
    path('ai-generate-email/', DoctorAIEmailGenerateView.as_view(), name='doctor-ai-generate-email'),
    path('ai-provision-all/', DoctorAIEmailProvisionAllView.as_view(), name='doctor-ai-provision-all'),
    path('specializations/', SpecializationListView.as_view(), name='specialization-list'),
    path('me/', DoctorProfileMeView.as_view(), name='doctor-me'),
    path('me/profile/', DoctorProfileMeView.as_view(), name='doctor-profile-me'),
    path('me/availability/', DoctorMeAvailabilityView.as_view(), name='doctor-me-availability'),
    path('<uuid:doctor_id>/', DoctorDetailView.as_view(), name='doctor-detail'),
    path('<uuid:doctor_id>/availability/', DoctorAvailabilityListView.as_view(), name='doctor-availability'),
]
