"""
Appointments URL Configuration
Author: Patient Care Operations Team
"""

from django.urls import path
from apps.appointments.views import (
    AppointmentListCreateView,
    AppointmentDetailView,
    AppointmentCancelView,
    AppointmentRescheduleView,
    AppointmentJoinView,
)

urlpatterns = [
    path('', AppointmentListCreateView.as_view(), name='appointment-list-create'),
    path('<uuid:appointment_id>/', AppointmentDetailView.as_view(), name='appointment-detail'),
    path('<uuid:appointment_id>/cancel/', AppointmentCancelView.as_view(), name='appointment-cancel'),
    path('<uuid:appointment_id>/reschedule/', AppointmentRescheduleView.as_view(), name='appointment-reschedule'),
    path('<uuid:appointment_id>/join/', AppointmentJoinView.as_view(), name='appointment-join'),
]
