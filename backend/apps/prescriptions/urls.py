"""
Prescriptions URL Configuration
Author: Clinical Pharmacy & Governance Team
"""

from django.urls import path
from apps.prescriptions.views import (
    PrescriptionListCreateView,
    PrescriptionDetailView,
    PrescriptionPDFView,
)

urlpatterns = [
    path('', PrescriptionListCreateView.as_view(), name='prescription-list-create'),
    path('<uuid:prescription_id>/', PrescriptionDetailView.as_view(), name='prescription-detail'),
    path('<uuid:prescription_id>/pdf/', PrescriptionPDFView.as_view(), name='prescription-pdf'),
]
