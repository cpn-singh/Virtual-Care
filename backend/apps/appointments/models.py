"""
Appointment Models
Author: Patient Care Operations Team

Coordinates virtual care encounters between verified clinicians and patients.
Tracks life-cycle states (pending -> confirmed -> in_progress -> completed / cancelled).
"""

import uuid
from django.db import models
from apps.patients.models import PatientProfile
from apps.doctors.models import DoctorProfile


class Appointment(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_RESCHEDULED = 'rescheduled'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending Confirmation'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_IN_PROGRESS, 'In Consultation'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_RESCHEDULED, 'Rescheduled'),
    ]

    PAYMENT_PENDING = 'pending'
    PAYMENT_PAID = 'paid'
    PAYMENT_REFUNDED = 'refunded'
    PAYMENT_WAIVED = 'waived'

    PAYMENT_CHOICES = [
        (PAYMENT_PENDING, 'Payment Pending'),
        (PAYMENT_PAID, 'Paid'),
        (PAYMENT_REFUNDED, 'Refunded'),
        (PAYMENT_WAIVED, 'Waived'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='appointments')
    
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    duration_minutes = models.PositiveSmallIntegerField(default=30)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_CONFIRMED)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default=PAYMENT_PENDING)
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=500.00)

    reason_for_visit = models.TextField(help_text="Primary reason reported by patient")
    patient_symptoms_summary = models.TextField(
        blank=True,
        help_text="AI care intake summary or structured symptom notes"
    )

    cancellation_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-scheduled_date', '-scheduled_time']

    def __str__(self):
        return f"Appointment {self.id}: {self.patient.user.full_name} with Dr. {self.doctor.user.full_name} on {self.scheduled_date}"
