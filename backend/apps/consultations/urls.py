"""
Consultations URL Configuration
Author: Telehealth Video & Media Team
"""

from django.urls import path
from apps.consultations.views import (
    ConsultationDetailView,
    ConsultationEndView,
    ClinicalNoteCreateUpdateView,
)

urlpatterns = [
    path('<uuid:consultation_id>/', ConsultationDetailView.as_view(), name='consultation-detail'),
    path('<uuid:consultation_id>/end/', ConsultationEndView.as_view(), name='consultation-end'),
    path('<uuid:consultation_id>/notes/', ClinicalNoteCreateUpdateView.as_view(), name='consultation-notes'),
]
